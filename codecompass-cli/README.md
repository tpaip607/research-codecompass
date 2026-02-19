# CodeCompass CLI

**Navigate codebases by structure, not just semantics.**

A command-line tool that gives AI coding assistants (and humans) access to the structural dependency graph of a codebase — finding files connected by imports, inheritance, and instantiation, not just keyword similarity.

## Why?

When you ask an AI to "add a `logger` parameter to `BaseRepository.__init__`", it reads the right files — but misses the central factory that instantiates every repository in the app. That file has no shared vocabulary with the task. It's invisible to retrieval. Visible only to structure.

CodeCompass solves this: structural navigation as a CLI tool, not a prompt hack.

---

## Installation

### From source (development)

```bash
cd codecompass-cli
pip install -e .
```

### From PyPI (when published)

```bash
pip install codecompass-cli
```

---

## Usage

### 1. Show structural neighbors of a file

```bash
codecompass neighbors app/db/repositories/base.py
```

**Output:**
```
Structural neighbors of 'app/db/repositories/base.py':

  ← [IMPORTS]       app/api/dependencies/database.py
  ← [IMPORTS]       app/db/repositories/articles.py
  ← [IMPORTS]       app/db/repositories/comments.py
  ← [INSTANTIATES]  app/api/dependencies/database.py

Total: 7 structural connections
```

Filter by direction:
```bash
codecompass neighbors app/main.py --direction in   # who imports this file?
codecompass neighbors app/main.py --direction out  # what does this file import?
```

### 2. Search with BM25 keyword ranking

```bash
codecompass search "password hashing salt"
```

**Output:**
```
Top 5 files for 'password hashing salt':

   1. (score 8.432)  app/services/security.py
   2. (score 6.128)  app/core/config.py
   3. (score 3.991)  tests/test_auth.py
```

Adjust number of results:
```bash
codecompass search "JWT token validation" --top 10
```

### 3. Show graph statistics

```bash
codecompass stats
```

**Output:**
```
CodeCompass Graph Statistics:

  Files: 71

  Edges:
    IMPORTS         201
    INHERITS         20
    INSTANTIATES     34
```

---

## Configuration

CodeCompass uses environment variables for configuration:

```bash
# Neo4j connection (for graph queries)
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=research123

# BM25 index path (for semantic search)
export BM25_INDEX_PATH=bm25_index.pkl
```

Or create a `.env` file in your project root.

---

## Building the Graph

CodeCompass requires a pre-built dependency graph. To build one:

### 1. Start Neo4j

```bash
docker compose up -d neo4j
```

### 2. Parse the codebase

```bash
python data_processing/ast_parser.py --repo /path/to/your/repo
python data_processing/build_graph.py
```

### 3. Build the BM25 index (optional, for `search` command)

```bash
python data_processing/build_bm25_index.py --repo /path/to/your/repo
```

---

## Why a CLI instead of MCP?

**Advantages of a CLI over MCP:**

1. **Universal** — works with any agent that can run bash (Claude Code, Cursor, Aider, raw API)
2. **Transparent** — commands appear in bash history and transcripts
3. **Debuggable** — easy to reproduce and verify results
4. **No registration** — no MCP server setup, just `pip install` and go
5. **Familiar** — models already have strong priors for using CLI tools

**When to use MCP instead:**
- Need structured tool schemas for strict validation
- Want in-process calls (no fork/exec overhead)
- Building IDE integrations that prefer MCP

---

## For AI Agents

If you're an AI coding assistant, here's how to use CodeCompass:

**Before editing a file:**
```bash
codecompass neighbors <file_path>
```
This shows all files structurally connected to the target. Read the ones that matter for the task.

**When grep finds nothing:**
```bash
codecompass search "<keywords>"
```
This uses BM25 to find files by content similarity, ranked by relevance.

**Key rule:** Architectural dependencies (factories, dependency injectors, base class instantiation sites) don't share vocabulary with task descriptions. Use `neighbors` to find them.

---

## Research

This tool is part of the **CodeCompass** research project studying the Navigation Paradox in large-context AI coding:

> *As context windows grow to 1M tokens, the bottleneck shifts from capacity to salience. Files aren't missing because they don't fit — they're missing because the model never looked for them.*

Paper: *"The Navigation Paradox in 1M-Token Contexts"* (arXiv, pending)

**Key finding:** Graph-based structural navigation achieves **96.6% coverage** on hidden-dependency tasks, vs **76.2%** for vanilla Claude Code and **74.6%** for BM25-augmented prompts.

But the tool gets ignored **61% of the time** despite explicit instructions. CLI adoption rates are untested — this is an open research question.

---

## License

MIT License. See `LICENSE` for details.

---

## Contributing

Issues and PRs welcome at: `https://github.com/[author]/research-codecompass`
