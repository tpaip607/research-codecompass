"""
calculate_acs.py

Parses a Claude Code JSONL transcript and computes:
  - ACS  (Architectural Coverage Score): fraction of required files accessed
  - FCTC (First Correct Tool Call): steps until first required file was touched
  - total_tool_calls, mcp_calls, internal_search_calls

Confirmed JSONL schema (from live session inspection):
  type=assistant, message.content[].type=tool_use, with fields:
    name  -> tool name (Read, Edit, Write, Bash, get_architectural_context, semantic_search, ...)
    input -> dict with file_path, command, etc.

Usage:
    python calculate_acs.py \
        --transcript results/task_01_A_run1/transcript.jsonl \
        --gold benchmarks/tasks/g1_semantic/task_01/gold_standard.json \
        --output results/task_01_A_run1/metrics.json
"""

import json
import re
import argparse
from pathlib import Path


MCP_TOOLS = {
    "get_architectural_context", "semantic_search",
    "mcp__codecompass__get_architectural_context", "mcp__codecompass__semantic_search",
}
INTERNAL_SEARCH_TOOLS = {"Grep", "Bash"}
FILE_ACCESS_TOOLS = {"Read", "Edit", "Write"}


def extract_path_from_bash(command: str) -> list[str]:
    """Extract file paths from bash commands like cat, grep, head, tail, sed."""
    paths = []
    # Match paths that look like app/... or tests/...
    pattern = r'(?:app|tests)/[\w/._-]+\.py'
    paths.extend(re.findall(pattern, command))
    return paths


def extract_tool_calls(jsonl_path: str) -> list[dict]:
    """
    Parse transcript JSONL and return all tool calls in order.
    Each entry: {step, name, input, file_path (if applicable)}
    """
    tool_calls = []
    step = 0

    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            if obj.get("type") != "assistant":
                continue

            msg = obj.get("message", {})
            if not isinstance(msg, dict):
                continue

            for block in msg.get("content", []):
                if not isinstance(block, dict):
                    continue
                if block.get("type") != "tool_use":
                    continue

                step += 1
                name = block.get("name", "")
                inp = block.get("input", {})

                # Extract file path depending on tool
                file_paths = []

                if name in FILE_ACCESS_TOOLS:
                    path = inp.get("file_path") or inp.get("path")
                    if path:
                        file_paths.append(path)

                elif name == "Bash":
                    cmd = inp.get("command", "")
                    file_paths.extend(extract_path_from_bash(cmd))

                elif name == "Grep":
                    path = inp.get("path", "")
                    if path:
                        file_paths.append(path)

                tool_calls.append({
                    "step": step,
                    "name": name,
                    "input": inp,
                    "file_paths": file_paths,
                })

    return tool_calls


def normalize_path(path: str, repo_root: str = "") -> str:
    """Strip repo root prefix to get repo-relative path.

    Handles both absolute paths and paths already relative to repo root.
    Also handles common subpath anchors like app/ and tests/.
    """
    # Strip explicit repo root if provided
    if repo_root and path.startswith(repo_root):
        path = path[len(repo_root):]
        return path.lstrip("/")

    # Auto-detect: find first occurrence of app/ or tests/ in path
    import re
    match = re.search(r'(?:^|/)((app|tests)/.+)', path)
    if match:
        return match.group(1)

    return path.lstrip("/")


def calculate_metrics(tool_calls: list[dict], required_files: list[str]) -> dict:
    """
    Compute ACS, FCTC, ECR, RER, and supporting metrics from tool call trace.

    New metrics:
      - ECR (Edit Completeness Rate): fraction of required files actually edited
      - RER (Read-to-Edit Ratio): files_read / files_edited (lower is better)
    """
    required_set = set(required_files)
    accessed_files = set()
    read_files = set()  # NEW: track Read operations
    edited_files = set()  # NEW: track Edit operations
    mcp_calls = 0
    internal_search_calls = 0
    fctc = None  # steps until first required file touched

    for call in tool_calls:
        name = call["name"]

        if name in MCP_TOOLS:
            mcp_calls += 1
        if name in INTERNAL_SEARCH_TOOLS:
            internal_search_calls += 1

        for raw_path in call["file_paths"]:
            # Normalize: strip absolute prefix if present
            norm = normalize_path(raw_path)
            accessed_files.add(norm)

            # NEW: Track Read vs Edit separately
            if name == "Read":
                read_files.add(norm)
            elif name == "Edit":
                edited_files.add(norm)

            if norm in required_set and fctc is None:
                fctc = call["step"]

    hit = accessed_files & required_set
    acs = len(hit) / len(required_set) if required_set else 0.0

    # NEW: Calculate ECR and RER
    edited_hit = edited_files & required_set
    ecr = len(edited_hit) / len(required_set) if required_set else 0.0
    rer = len(read_files) / len(edited_files) if edited_files else float('inf')

    return {
        "acs": round(acs, 4),
        "ecr": round(ecr, 4),  # NEW
        "rer": round(rer, 2) if rer != float('inf') else -1,  # NEW: -1 = no edits
        "fctc": fctc if fctc is not None else -1,  # -1 = never touched a required file
        "total_tool_calls": len(tool_calls),
        "mcp_calls": mcp_calls,
        "internal_search_calls": internal_search_calls,
        "files_accessed": sorted(accessed_files),
        "files_read": sorted(read_files),  # NEW
        "files_edited": sorted(edited_files),  # NEW
        "required_files_hit": sorted(hit),
        "required_files_edited": sorted(edited_hit),  # NEW
        "required_files_missed": sorted(required_set - accessed_files),
        "required_files_total": len(required_set),
    }


def main():
    parser = argparse.ArgumentParser(description="Calculate ACS from a Claude Code transcript")
    parser.add_argument("--transcript", required=True, help="Path to transcript.jsonl")
    parser.add_argument("--gold", required=True, help="Path to gold_standard.json")
    parser.add_argument("--output", required=True, help="Path to write metrics.json")
    args = parser.parse_args()

    # Load gold standard
    gold = json.loads(Path(args.gold).read_text())
    required_files = gold["required_files"]
    task_id = gold["task_id"]

    # Parse transcript
    transcript_path = args.transcript
    if not Path(transcript_path).exists():
        print(f"Warning: transcript not found at {transcript_path}")
        metrics = {
            "task_id": task_id,
            "error": "transcript_not_found",
            "acs": 0.0,
            "ecr": 0.0,
            "rer": -1,
            "fctc": -1,
            "total_tool_calls": 0,
            "mcp_calls": 0,
            "internal_search_calls": 0,
            "files_accessed": [],
            "files_read": [],
            "files_edited": [],
            "required_files_hit": [],
            "required_files_edited": [],
            "required_files_missed": required_files,
            "required_files_total": len(required_files),
        }
    else:
        tool_calls = extract_tool_calls(transcript_path)
        metrics = calculate_metrics(tool_calls, required_files)
        metrics["task_id"] = task_id

    # Write output
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, indent=2))

    # Print summary
    print(f"Task: {task_id}")
    print(f"  ACS:              {metrics['acs']:.2%}  ({len(metrics['required_files_hit'])}/{metrics['required_files_total']} required files)")
    print(f"  ECR:              {metrics['ecr']:.2%}  ({len(metrics.get('required_files_edited', []))}/{metrics['required_files_total']} required files edited)")
    print(f"  RER:              {metrics['rer']:.2f}  (read-to-edit ratio)")
    print(f"  FCTC:             step {metrics['fctc']}")
    print(f"  Total tool calls: {metrics['total_tool_calls']}")
    print(f"  MCP calls:        {metrics['mcp_calls']}")
    print(f"  Internal search:  {metrics['internal_search_calls']}")
    print(f"  Files read:       {len(metrics.get('files_read', []))}")
    print(f"  Files edited:     {len(metrics.get('files_edited', []))}")
    if metrics["required_files_missed"]:
        print(f"  Missed files:     {metrics['required_files_missed']}")


if __name__ == "__main__":
    main()
