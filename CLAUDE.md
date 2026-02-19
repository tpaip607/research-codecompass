# CodeCompass — Instructions for Claude

## What This Repo Is

This is the research implementation for **CodeCompass**, a study evaluating whether graph-based structural navigation improves agentic coding task performance over vanilla Claude Code and BM25 retrieval.

Paper title: *"The Navigation Paradox in 1M-Token Contexts"*

## Repo Layout

```
benchmarks/tasks/       # 30 benchmark tasks (g1_semantic, g2_structural, g3_hidden)
mcp_server/             # FastMCP server exposing graph + BM25 tools to Claude
data_processing/        # AST parser, Neo4j loader, BM25 index builder
harness/                # Experiment runner scripts and ACS calculator
results/                # Auto-generated trial outputs (gitignored)
paper/                  # Notes and paper drafts
```

## Target Benchmark Repo

`/Users/tarak/engineer/repos/fastapi-realworld-example-app`

Do NOT modify this repo directly. The harness resets it via `git stash` before each trial.

## Running the Infrastructure

```bash
docker compose up -d        # Start Neo4j + Weaviate
python data_processing/ast_parser.py        # Parse repo into edges
python data_processing/build_graph.py       # Load edges into Neo4j
python data_processing/build_bm25_index.py  # Build BM25 index
python mcp_server/server.py                 # Start MCP server
```

## Running a Single Trial

```bash
./harness/run_trial.sh <task_id> <condition> <run_number>
# condition: A (vanilla) | B (bm25) | C (graph)
# Example: ./harness/run_trial.sh 01 C 1
```

## MCP Registration

```bash
claude mcp add codecompass -- python3.11 /Users/tarak/engineer/repos/research-codecompass/mcp_server/server.py
```

Note: Must use python3.11 (system python3 is 3.9 which is too old for fastmcp).

## Experiment Conditions

| Condition | Description |
|-----------|-------------|
| A | Vanilla Claude Code — no MCP, default tools only |
| B | Claude Code + BM25 file ranking prepended to prompt |
| C | Claude Code + CodeCompass MCP (graph + BM25 tools) |
