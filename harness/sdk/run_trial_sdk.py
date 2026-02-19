"""run_trial_sdk.py — Single trial runner using the Anthropic Python SDK.

Executes one CodeCompass benchmark trial:
  1. Find task directory and load gold standard
  2. Reset benchmark repo to clean state
  3. Build prompt (condition-specific; Condition B prepends BM25 rankings)
  4. Run agentic loop via anthropic.messages.create
  5. Compute ACS metrics inline from tool call log
  6. Write metrics.json + trial_meta.json to results/
  7. Upload scores to Langfuse trace (v3 API)
"""
import json
import os
import pickle
import re
import subprocess
import time
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

import anthropic

# ---------------------------------------------------------------------------
# Paths & configuration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent.parent  # research-codecompass/
BENCHMARK_REPO = os.getenv(
    "BENCHMARK_REPO",
    "/Users/tarak/engineer/repos/fastapi-realworld-example-app",
)
BM25_INDEX_PATH = os.getenv(
    "BM25_INDEX_PATH",
    str(REPO_ROOT / "bm25_index.pkl"),
)
MODEL = os.getenv("MODEL", "claude-sonnet-4-5-20250929")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "8192"))
MAX_TURNS = int(os.getenv("MAX_TURNS", "50"))

# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert software engineer. Complete the given coding task \
in a Python repository.

File paths in tool calls are relative to the repository root \
(e.g., "app/services/jwt.py"). Do NOT use absolute paths.

Work methodically:
1. Read the task carefully and identify which files need changing.
2. Explore the codebase with list_files, search_content, and read_file.
3. Make precise, targeted changes using edit_file or write_file.
4. Verify changes are consistent across the codebase before finishing."""

_MCP_SUFFIX = """

You also have access to architectural graph tools:
- get_architectural_context: reveals all files that import/depend on a given file.
  Call this BEFORE editing any file to discover hidden dependencies.
- semantic_search: BM25 keyword search over the codebase when grep returns nothing.

Systematically use get_architectural_context on every file you plan to modify."""

# ---------------------------------------------------------------------------
# ACS calculation (mirrors calculate_acs.py logic for SDK tool names)
# ---------------------------------------------------------------------------

_FILE_ACCESS_TOOLS = {"read_file", "write_file", "edit_file"}
_MCP_TOOLS = {"get_architectural_context", "semantic_search"}
_SEARCH_TOOLS = {"search_content", "run_bash"}


def _normalize_path(path: str) -> str:
    match = re.search(r"(?:^|/)((app|tests)/.+)", path)
    if match:
        return match.group(1)
    return path.lstrip("/")


def _compute_acs(tool_calls: list[dict], required_files: list[str]) -> dict:
    required_set = set(required_files)
    accessed_files: set[str] = set()
    mcp_calls = 0
    internal_search_calls = 0
    fctc: Optional[int] = None

    for call in tool_calls:
        name = call["name"]
        inp = call["input"]

        if name in _MCP_TOOLS:
            mcp_calls += 1
        if name in _SEARCH_TOOLS:
            internal_search_calls += 1

        raw_paths: list[str] = []
        if name in _FILE_ACCESS_TOOLS:
            fp = inp.get("file_path", "")
            if fp:
                raw_paths.append(fp)
        elif name == "run_bash":
            raw_paths.extend(
                re.findall(r"(?:app|tests)/[\w/._-]+\.py", inp.get("command", ""))
            )

        for raw in raw_paths:
            norm = _normalize_path(raw)
            accessed_files.add(norm)
            if norm in required_set and fctc is None:
                fctc = call["step"]

    hit = accessed_files & required_set
    acs = len(hit) / len(required_set) if required_set else 0.0

    return {
        "acs": round(acs, 4),
        "fctc": fctc if fctc is not None else -1,
        "total_tool_calls": len(tool_calls),
        "mcp_calls": mcp_calls,
        "internal_search_calls": internal_search_calls,
        "files_accessed": sorted(accessed_files),
        "required_files_hit": sorted(hit),
        "required_files_missed": sorted(required_set - accessed_files),
        "required_files_total": len(required_set),
    }


# ---------------------------------------------------------------------------
# BM25 prompt prefix (Condition B)
# ---------------------------------------------------------------------------


def _bm25_prefix(query: str, top_n: int = 10) -> str:
    try:
        with open(BM25_INDEX_PATH, "rb") as f:
            data = pickle.load(f)
        index = data["index"]
        chunks = data["chunks"]

        tokens = query.lower().split()
        scores = index.get_scores(tokens)
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)

        seen: dict[str, float] = {}
        for i in top_indices:
            file = chunks[i].get("file_path") or chunks[i].get("file", "")
            if file and file not in seen:
                seen[file] = float(scores[i])
            if len(seen) >= top_n:
                break

        lines = [
            "The following files are likely relevant to this task "
            "(ranked by BM25 keyword similarity):\n"
        ]
        for idx, (file, score) in enumerate(seen.items(), 1):
            lines.append(f"  {idx:2}. (score {score:.3f})  {file}")
        return "\n".join(lines) + "\n\n---\n\n"
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def find_task_dir(task_id: str) -> Path:
    tasks_root = REPO_ROOT / "benchmarks" / "tasks"
    matches = list(tasks_root.glob(f"*/task_{task_id}"))
    if not matches:
        raise FileNotFoundError(f"Task directory not found for task_id={task_id!r}")
    return matches[0]


def _reset_repo() -> None:
    for cmd in [
        ["git", "stash", "--quiet"],
        ["git", "stash", "drop", "--quiet"],
        ["git", "checkout", "--", "."],
    ]:
        subprocess.run(cmd, cwd=BENCHMARK_REPO, capture_output=True)


def _lf_span(langfuse, **kwargs):
    """Return a Langfuse span context manager, or nullcontext if tracing is off."""
    if langfuse is None:
        return nullcontext()
    try:
        return langfuse.start_as_current_span(**kwargs)
    except Exception:
        return nullcontext()


def _lf_gen(langfuse, **kwargs):
    """Return a Langfuse generation context manager, or nullcontext."""
    if langfuse is None:
        return nullcontext()
    try:
        # v3.14+: start_as_current_observation(as_type='generation') preferred
        if hasattr(langfuse, "start_as_current_observation"):
            return langfuse.start_as_current_observation(as_type="generation", **kwargs)
        return langfuse.start_as_current_generation(**kwargs)
    except Exception:
        return nullcontext()


# ---------------------------------------------------------------------------
# Main trial function
# ---------------------------------------------------------------------------


def run_trial(
    task_id: str,
    condition: str,
    run_num: int,
    tool_callback: Optional[Callable[[int, str, dict, str], None]] = None,
    langfuse=None,
) -> dict:
    """Run a single benchmark trial and return the metrics dict.

    Also writes metrics.json and trial_meta.json to results/.
    """
    from harness.sdk.tools import execute_tool, get_tool_definitions  # noqa: PLC0415

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_dir = (
        REPO_ROOT / "results" / f"task_{task_id}_{condition}_run{run_num}_{timestamp}"
    )
    result_dir.mkdir(parents=True, exist_ok=True)

    # --- Load task ---
    task_dir = find_task_dir(task_id)
    gold = json.loads((task_dir / "gold_standard.json").read_text())
    required_files: list[str] = gold["required_files"]
    min_acs: float = gold.get("min_acs_threshold", 0.8)
    task_group: str = gold.get("group", "unknown")
    task_desc: str = gold.get("description", "")

    # --- Prompt ---
    # Select prompt file based on condition
    if condition == "C":
        prompt_file = task_dir / "prompt_c.md"
    elif condition == "D":
        prompt_file = task_dir / "prompt_d.md"
    elif condition == "E":
        prompt_file = task_dir / "prompt_e.md"
    else:
        prompt_file = task_dir / "prompt.md"

    # Fallback to base prompt if condition-specific doesn't exist
    if not prompt_file.exists():
        prompt_file = task_dir / "prompt.md"

    base_prompt = prompt_file.read_text()
    final_prompt = (_bm25_prefix(task_desc) + base_prompt) if condition == "B" else base_prompt
    (result_dir / "prompt_used.md").write_text(final_prompt)

    # Add MCP suffix for C and D (both use MCP tools)
    system = SYSTEM_PROMPT + (_MCP_SUFFIX if condition in ("C", "D") else "")

    # --- SDK client & tools ---
    client = anthropic.Anthropic()
    tools = get_tool_definitions(condition)

    # --- State ---
    messages: list[dict] = [{"role": "user", "content": final_prompt}]
    tool_calls_log: list[dict] = []
    step = 0
    total_input_tokens = 0
    total_output_tokens = 0
    trace_id: Optional[str] = None
    turn = 0

    # ---------------------------------------------------------------------------
    # Langfuse v3: wrap entire trial in a root span = trace
    # ---------------------------------------------------------------------------
    with _lf_span(langfuse, name="codecompass_trial"):
        if langfuse:
            try:
                langfuse.update_current_trace(
                    metadata={
                        "task_id": task_id,
                        "condition": condition,
                        "group": task_group,
                        "run_number": run_num,
                        "task_description": task_desc,
                        "model": MODEL,
                    },
                    tags=[condition, task_group, f"task_{task_id}"],
                )
                trace_id = langfuse.get_current_trace_id()
            except Exception:
                pass

        # Reset repo
        with _lf_span(langfuse, name="reset_repo", input={"repo": BENCHMARK_REPO}):
            _reset_repo()
            if langfuse:
                try:
                    langfuse.update_current_span(output="reset complete")
                except Exception:
                    pass

        # Build prompt span
        with _lf_span(langfuse, name="build_prompt", input={"condition": condition}):
            if langfuse:
                try:
                    langfuse.update_current_span(
                        output={
                            "prompt_length": len(final_prompt),
                            "bm25_augmented": condition == "B",
                        }
                    )
                except Exception:
                    pass

        # Agentic loop
        with _lf_span(langfuse, name="agentic_loop"):
            for turn in range(1, MAX_TURNS + 1):
                with _lf_gen(
                    langfuse,
                    name=f"claude_call_{turn}",
                    model=MODEL,
                    input=messages,
                ):
                    response = client.messages.create(
                        model=MODEL,
                        max_tokens=MAX_TOKENS,
                        system=system,
                        tools=tools,
                        messages=messages,
                    )

                    total_input_tokens += response.usage.input_tokens
                    total_output_tokens += response.usage.output_tokens

                    if langfuse:
                        try:
                            update = (
                                langfuse.update_current_observation
                                if hasattr(langfuse, "update_current_observation")
                                else langfuse.update_current_generation
                            )
                            update(
                                output=[
                                    b.model_dump() if hasattr(b, "model_dump") else str(b)
                                    for b in response.content
                                ],
                                usage_details={
                                    "input": response.usage.input_tokens,
                                    "output": response.usage.output_tokens,
                                },
                            )
                        except Exception:
                            pass

                    messages.append({"role": "assistant", "content": response.content})

                    if response.stop_reason == "end_turn":
                        break

                    if response.stop_reason != "tool_use":
                        break

                    # Process tool calls
                    tool_results = []
                    for block in response.content:
                        if not hasattr(block, "type") or block.type != "tool_use":
                            continue

                        step += 1
                        tool_name: str = block.name
                        tool_input: dict = block.input
                        t0 = time.monotonic()

                        with _lf_span(
                            langfuse,
                            name=f"tool:{tool_name}",
                            input=tool_input,
                        ):
                            tool_result = execute_tool(tool_name, tool_input)
                            duration_ms = int((time.monotonic() - t0) * 1000)
                            if langfuse:
                                try:
                                    langfuse.update_current_span(
                                        output=tool_result[:500],
                                        metadata={"duration_ms": duration_ms},
                                    )
                                except Exception:
                                    pass

                        tool_calls_log.append(
                            {"step": step, "name": tool_name, "input": tool_input}
                        )

                        if tool_callback is not None:
                            try:
                                tool_callback(step, tool_name, tool_input, tool_result)
                            except Exception:
                                pass

                        tool_results.append(
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": tool_result,
                            }
                        )

                    messages.append({"role": "user", "content": tool_results})

        # --- Compute ACS ---
        metrics = _compute_acs(tool_calls_log, required_files)
        metrics["task_id"] = gold["task_id"]
        metrics["total_input_tokens"] = total_input_tokens
        metrics["total_output_tokens"] = total_output_tokens
        metrics["turns"] = turn

        # --- Write results ---
        (result_dir / "metrics.json").write_text(json.dumps(metrics, indent=2))
        (result_dir / "trial_meta.json").write_text(
            json.dumps(
                {
                    "task_id": task_id,
                    "condition": condition,
                    "run_number": run_num,
                    "timestamp": timestamp,
                    "model": MODEL,
                    "benchmark_repo": BENCHMARK_REPO,
                    "turns": turn,
                    "total_input_tokens": total_input_tokens,
                    "total_output_tokens": total_output_tokens,
                    "langfuse_trace_id": trace_id,
                },
                indent=2,
            )
        )

        # --- Langfuse scores ---
        if langfuse and trace_id:
            scores = [
                ("acs", metrics["acs"]),
                ("fctc", float(metrics["fctc"])),
                ("mcp_calls", float(metrics["mcp_calls"])),
                ("total_tool_calls", float(metrics["total_tool_calls"])),
                ("success", 1.0 if metrics["acs"] >= min_acs else 0.0),
            ]
            for score_name, score_value in scores:
                try:
                    langfuse.create_score(
                        name=score_name,
                        value=score_value,
                        trace_id=trace_id,
                        data_type="NUMERIC",
                    )
                except Exception:
                    pass

    metrics["result_dir"] = str(result_dir)
    metrics["langfuse_trace_id"] = trace_id
    return metrics
