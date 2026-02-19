"""tools.py — Tool implementations for the SDK-based agentic loop.

All file operations work relative to BENCHMARK_REPO.
Tool inputs accept repo-relative paths (e.g., "app/services/jwt.py").

Tool set:
  Conditions A & B: read_file, write_file, edit_file, list_files,
                    search_content, run_bash
  Condition C:      all of the above + get_architectural_context,
                    semantic_search
"""
import glob as glob_module
import os
import pickle
import re
import subprocess
from pathlib import Path
from typing import Any

BENCHMARK_REPO = os.getenv(
    "BENCHMARK_REPO",
    "/Users/tarak/engineer/repos/fastapi-realworld-example-app",
)
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "research123")
BM25_INDEX_PATH = os.getenv(
    "BM25_INDEX_PATH",
    "/Users/tarak/engineer/repos/research-codecompass/bm25_index.pkl",
)

_neo4j_driver = None


def _get_neo4j():
    global _neo4j_driver
    if _neo4j_driver is None:
        from neo4j import GraphDatabase

        _neo4j_driver = GraphDatabase.driver(
            NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
    return _neo4j_driver


def _resolve(file_path: str) -> Path:
    """Convert a repo-relative (or absolute) path to absolute path under BENCHMARK_REPO."""
    if file_path.startswith(BENCHMARK_REPO):
        return Path(file_path)
    return Path(BENCHMARK_REPO) / file_path.lstrip("/")


# ---------------------------------------------------------------------------
# File operations
# ---------------------------------------------------------------------------


def read_file(file_path: str) -> str:
    path = _resolve(file_path)
    if not path.exists():
        return f"Error: file not found: {file_path}"
    try:
        return path.read_text(encoding="utf-8")
    except Exception as e:
        return f"Error reading {file_path}: {e}"


def write_file(file_path: str, content: str) -> str:
    path = _resolve(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return f"Wrote {path.stat().st_size} bytes to {file_path}"
    except Exception as e:
        return f"Error writing {file_path}: {e}"


def edit_file(file_path: str, old_str: str, new_str: str) -> str:
    path = _resolve(file_path)
    if not path.exists():
        return f"Error: file not found: {file_path}"
    try:
        content = path.read_text(encoding="utf-8")
        if old_str not in content:
            return f"Error: old_str not found in {file_path}"
        count = content.count(old_str)
        if count > 1:
            return (
                f"Error: old_str appears {count} times in {file_path}. "
                "Make it more specific to match exactly once."
            )
        path.write_text(content.replace(old_str, new_str, 1), encoding="utf-8")
        return f"Successfully edited {file_path}"
    except Exception as e:
        return f"Error editing {file_path}: {e}"


def list_files(pattern: str) -> str:
    if pattern.startswith("/"):
        search_pattern = pattern
    else:
        search_pattern = str(Path(BENCHMARK_REPO) / pattern)

    matches = glob_module.glob(search_pattern, recursive=True)
    if not matches:
        return f"No files found matching: {pattern}"

    repo_root = Path(BENCHMARK_REPO)
    result = []
    for m in sorted(matches):
        try:
            result.append(str(Path(m).relative_to(repo_root)))
        except ValueError:
            result.append(m)
    return "\n".join(result)


def search_content(pattern: str, path: str = ".") -> str:
    search_path = path if path.startswith("/") else str(Path(BENCHMARK_REPO) / path)
    try:
        result = subprocess.run(
            ["grep", "-r", "-n", "--include=*.py", pattern, search_path],
            capture_output=True,
            text=True,
            timeout=30,
        )
        output = result.stdout.strip()
        if not output:
            return f"No matches found for: {pattern}"
        lines = output.split("\n")
        if len(lines) > 50:
            return "\n".join(lines[:50]) + f"\n... ({len(lines) - 50} more lines truncated)"
        return output
    except subprocess.TimeoutExpired:
        return "Error: search timed out after 30s"
    except Exception as e:
        return f"Error searching: {e}"


# Read-only bash command prefixes
_ALLOWED_BASH_PREFIXES = (
    "ls", "cat ", "head ", "tail ", "find ",
    "echo ", "wc ", "pwd", "git log", "git show", "git diff",
    "grep ", "python ", "python3 ",
)


def run_bash(command: str) -> str:
    cmd = command.strip()
    allowed = any(
        cmd == prefix.rstrip() or cmd.startswith(prefix)
        for prefix in _ALLOWED_BASH_PREFIXES
    )
    if not allowed:
        return (
            "Error: only read-only commands are allowed "
            "(ls, cat, head, tail, find, git log, git show, grep, wc, echo)."
        )
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=BENCHMARK_REPO,
        )
        output = (result.stdout + result.stderr).strip()
        if len(output) > 4000:
            return output[:4000] + "\n... (truncated)"
        return output or "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: command timed out after 30s"
    except Exception as e:
        return f"Error running command: {e}"


# ---------------------------------------------------------------------------
# Graph / BM25 tools (Condition C)
# ---------------------------------------------------------------------------


def get_architectural_context(file_path: str) -> str:
    try:
        driver = _get_neo4j()
        with driver.session() as session:
            result = session.run(
                """
                MATCH (f:File {path: $path})-[r]-(neighbor:File)
                RETURN
                    neighbor.path AS neighbor,
                    type(r) AS relation,
                    CASE WHEN startNode(r) = f THEN 'outgoing' ELSE 'incoming' END AS direction
                ORDER BY relation, direction, neighbor
                """,
                path=file_path,
            )
            rows = result.data()

        if not rows:
            return (
                f"No structural neighbors found for '{file_path}'.\n"
                "Verify the path is correct (e.g., 'app/db/repositories/base.py')."
            )

        lines = [f"Structural neighbors of '{file_path}':\n"]
        for row in rows:
            symbol = "→" if row["direction"] == "outgoing" else "←"
            lines.append(f"  {symbol} [{row['relation']}]  {row['neighbor']}")
        lines.append(f"\nTotal: {len(rows)} structural connections")
        return "\n".join(lines)

    except Exception as e:
        return f"Error querying graph: {e}\nIs Neo4j running? Try: docker compose up -d"


def semantic_search(query: str, top_n: int = 8) -> str:
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

        if not seen:
            return f"No results found for: '{query}'"

        lines = [f"Top {len(seen)} files for '{query}':\n"]
        for i, (file, score) in enumerate(seen.items(), 1):
            lines.append(f"  {i:2}. (score {score:.3f})  {file}")
        return "\n".join(lines)

    except FileNotFoundError:
        return f"BM25 index not found at {BM25_INDEX_PATH}. Run: python data_processing/build_bm25_index.py"
    except Exception as e:
        return f"Error running semantic search: {e}"


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

_TOOL_FUNCTIONS: dict[str, Any] = {
    "read_file": lambda inp: read_file(inp["file_path"]),
    "write_file": lambda inp: write_file(inp["file_path"], inp["content"]),
    "edit_file": lambda inp: edit_file(inp["file_path"], inp["old_str"], inp["new_str"]),
    "list_files": lambda inp: list_files(inp["pattern"]),
    "search_content": lambda inp: search_content(inp["pattern"], inp.get("path", ".")),
    "run_bash": lambda inp: run_bash(inp["command"]),
    "get_architectural_context": lambda inp: get_architectural_context(inp["file_path"]),
    "semantic_search": lambda inp: semantic_search(inp["query"], inp.get("top_n", 8)),
}


def execute_tool(name: str, tool_input: dict) -> str:
    fn = _TOOL_FUNCTIONS.get(name)
    if fn is None:
        return f"Unknown tool: {name}"
    try:
        return fn(tool_input)
    except KeyError as e:
        return f"Missing required parameter for tool '{name}': {e}"
    except Exception as e:
        return f"Tool error ({name}): {e}"


# ---------------------------------------------------------------------------
# Tool schema definitions (Anthropic API format)
# ---------------------------------------------------------------------------

_BASE_TOOLS = [
    {
        "name": "read_file",
        "description": "Read the full contents of a file in the repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Repo-relative path, e.g. 'app/services/jwt.py'",
                }
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "write_file",
        "description": "Write or overwrite a file with the given content.",
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Repo-relative path to write",
                },
                "content": {
                    "type": "string",
                    "description": "Complete file content to write",
                },
            },
            "required": ["file_path", "content"],
        },
    },
    {
        "name": "edit_file",
        "description": (
            "Replace an exact string in a file. "
            "old_str must appear exactly once in the file."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Repo-relative path to the file",
                },
                "old_str": {
                    "type": "string",
                    "description": "Exact string to find and replace (must be unique)",
                },
                "new_str": {
                    "type": "string",
                    "description": "Replacement string",
                },
            },
            "required": ["file_path", "old_str", "new_str"],
        },
    },
    {
        "name": "list_files",
        "description": "List files matching a glob pattern in the repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern, e.g. 'app/**/*.py' or 'app/db/**'",
                }
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "search_content",
        "description": "Search for a regex pattern in Python files within the repository.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Regex or literal string to search for",
                },
                "path": {
                    "type": "string",
                    "description": "Directory to search in (repo-relative). Defaults to repo root.",
                },
            },
            "required": ["pattern"],
        },
    },
    {
        "name": "run_bash",
        "description": (
            "Run a read-only bash command (ls, cat, head, tail, find, grep, "
            "git log, git show, git diff, wc, echo). Executes from repo root."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Read-only bash command to execute",
                }
            },
            "required": ["command"],
        },
    },
]

_MCP_TOOLS = [
    {
        "name": "get_architectural_context",
        "description": (
            "Returns all files structurally connected to the given file via the code graph. "
            "Shows dependencies (files this file imports) and dependents (files that import this). "
            "Also shows inheritance and instantiation relationships. "
            "Call this BEFORE editing any file to discover hidden dependencies."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Repo-relative path, e.g. 'app/db/repositories/base.py'",
                }
            },
            "required": ["file_path"],
        },
    },
    {
        "name": "semantic_search",
        "description": (
            "Search the codebase using BM25 keyword ranking over function/class-level chunks. "
            "Returns the most relevant files by relevance score. "
            "Use when you don't know which file contains a concept or when grep returns nothing."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language or code description to search for",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of top results to return (default 8)",
                },
            },
            "required": ["query"],
        },
    },
]


def get_tool_definitions(condition: str) -> list[dict]:
    """Return the tool list for a given experiment condition."""
    if condition in ("A", "B", "E"):
        # Vanilla (A), BM25-augmented (B), CLI-based (E) - base tools only
        return _BASE_TOOLS
    else:  # C, D
        # MCP-based (C standard, D checklist) - base + MCP tools
        return _BASE_TOOLS + _MCP_TOOLS
