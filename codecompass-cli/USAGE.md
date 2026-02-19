# CodeCompass CLI - Quick Start

## Installation

```bash
cd codecompass-cli
python3.11 -m pip install -e .
```

## Configuration

Set environment variables (or add to `.env`):

```bash
export NEO4J_URI=bolt://localhost:7687
export NEO4J_USER=neo4j
export NEO4J_PASSWORD=research123
export BM25_INDEX_PATH=bm25_index_dicts.pkl
```

**Important:** Use `bm25_index_dicts.pkl` (plain dicts) instead of `bm25_index.pkl` (pickled objects) to avoid unpickling errors.

If you only have `bm25_index.pkl`:
```bash
cd codecompass-cli
python3.11 rebuild_bm25_as_dicts.py
```

## Usage Examples

### 1. Graph statistics

```bash
codecompass stats
```

Output:
```
CodeCompass Graph Statistics:

  Files: 71

  Edges:
    IMPORTS          201
    INSTANTIATES      34
    INHERITS          20
```

### 2. Find structural neighbors

```bash
codecompass neighbors app/db/repositories/base.py
```

Output:
```
Structural neighbors of 'app/db/repositories/base.py':

  ← [IMPORTS]       app/api/dependencies/database.py
  ← [IMPORTS]       app/db/repositories/articles.py
  ← [IMPORTS]       app/db/repositories/comments.py
  ← [IMPORTS]       app/db/repositories/profiles.py
  ← [IMPORTS]       app/db/repositories/tags.py
  ← [IMPORTS]       app/db/repositories/users.py
  ← [INSTANTIATES]  app/api/dependencies/database.py

Total: 7 structural connections
```

**Key insight:** `database.py` appears here — but NOT in BM25 search for "logger parameter BaseRepository".

### 3. BM25 search

```bash
codecompass search "logger parameter BaseRepository"
```

Output:
```
Top 5 files for 'logger parameter BaseRepository':

   1. (score 8.172)  app/db/queries/tables.py
   2. (score 6.007)  app/db/events.py
   3. (score 5.979)  app/core/settings/app.py
   4. (score 5.380)  app/db/repositories/articles.py
   5. (score 4.769)  app/core/logging.py
```

Notice: `database.py` is **not** in the results. This is the Navigation Paradox.

### 4. JSON output

```bash
codecompass neighbors app/db/repositories/base.py --json
codecompass search "password hashing" --json
codecompass stats --json
```

All commands support `--json` for programmatic use.

### 5. Filter by direction

```bash
# Who imports this file?
codecompass neighbors app/main.py --direction in

# What does this file import?
codecompass neighbors app/main.py --direction out
```

## Using with AI Coding Assistants

**Recommended workflow:**

1. Before editing any file, run:
   ```bash
   codecompass neighbors <file_path>
   ```

2. Read all files shown as `INSTANTIATES` or `INHERITS` connections.

3. If you're unsure which file contains a concept:
   ```bash
   codecompass search "<keywords>"
   ```

**Why this matters:**

Architectural dependencies (factories, DI containers, base class instantiation sites) don't share vocabulary with task descriptions. Graph navigation finds them. BM25 search does not.

## Troubleshooting

### "No module named 'codecompass'"

The CLI is installed in a non-PATH location. Either:
- Add to PATH: `export PATH="$HOME/Library/Python/3.11/bin:$PATH"`
- Use full path: `/Users/tarak/Library/Python/3.11/bin/codecompass`
- Install globally: `sudo python3.11 -m pip install -e codecompass-cli`

### "Can't get attribute 'CodeChunk'"

You're using `bm25_index.pkl` instead of `bm25_index_dicts.pkl`. Run:
```bash
cd codecompass-cli
python3.11 rebuild_bm25_as_dicts.py
export BM25_INDEX_PATH=bm25_index_dicts.pkl
```

### "Is Neo4j running?"

Start the Neo4j container:
```bash
docker compose up -d neo4j
```

### BM25 index not found

Build it:
```bash
cd /Users/tarak/engineer/repos/research-codecompass
python3.11 data_processing/build_bm25_index.py --repo /path/to/your/repo
python3.11 codecompass-cli/rebuild_bm25_as_dicts.py
```

## Comparison: MCP vs CLI

| Feature | MCP Server | CLI Tool |
|---------|------------|----------|
| **Portability** | Claude Code only | Any agent with bash |
| **Setup** | `claude mcp add` | `pip install` |
| **Transparency** | Hidden tool calls | Visible in bash history |
| **Speed** | In-process | Fork/exec (negligible) |
| **Debugging** | Opaque | Easy to reproduce |
| **Adoption (expected)** | 39% (measured) | ?? (untested) |

**Hypothesis:** CLI adoption may be higher because models have stronger priors for using bash tools than abstract MCP interfaces.

## Next Steps

To test CLI adoption in the experiment:

1. Create Condition D: "CLI-based graph navigation"
2. Replace MCP instructions with bash command instructions
3. Run 10-20 trials on G3 tasks
4. Compare MCP adoption (39%) vs CLI adoption (?%)

If CLI adoption > 50%, this confirms that interface familiarity matters as much as tool capability.
