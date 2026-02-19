"""
CodeCompass MCP Server

Exposes two tools to Claude Code:
  1. get_architectural_context(file_path)
     → Queries Neo4j for structural neighbors (1-hop in both directions)
     → Reveals non-semantic dependencies the agent would otherwise miss

  2. semantic_search(query)
     → BM25 search over function/class-level code chunks
     → Surfaces relevant files when keyword search returns nothing

Usage:
    python server.py

Register with Claude Code:
    claude mcp add codecompass --command "python" --args "mcp_server/server.py"
"""

import os
import pickle
import sys
from pathlib import Path

# Add data_processing to path for BM25 utilities
sys.path.insert(0, str(Path(__file__).parent.parent / "data_processing"))

from fastmcp import FastMCP
from neo4j import GraphDatabase
from build_bm25_index import search as bm25_search

# --- Config ---
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "research123")
BM25_INDEX_PATH = os.getenv("BM25_INDEX_PATH", "bm25_index.pkl")

# --- Init ---
mcp = FastMCP("CodeCompass")

_neo4j_driver = None
_bm25_data = None


def get_neo4j():
    global _neo4j_driver
    if _neo4j_driver is None:
        _neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    return _neo4j_driver


def get_bm25():
    global _bm25_data
    if _bm25_data is None:
        index_path = Path(BM25_INDEX_PATH)
        if not index_path.exists():
            raise FileNotFoundError(
                f"BM25 index not found at {index_path}. "
                "Run: python data_processing/build_bm25_index.py --repo <repo_path>"
            )
        with open(index_path, "rb") as f:
            _bm25_data = pickle.load(f)
    return _bm25_data["index"], _bm25_data["chunks"]


# --- Tools ---

@mcp.tool()
def get_architectural_context(file_path: str) -> str:
    """
    Returns all files structurally connected to the given file via the code graph.

    Includes:
    - Files that import this file (dependents)
    - Files this file imports (dependencies)
    - Files sharing inheritance or instantiation relationships

    Use this BEFORE editing any file to discover which other files will be affected.
    Critical for architecture-heavy tasks where the full dependency chain is not obvious.

    Args:
        file_path: Repo-relative path, e.g. "app/services/jwt.py"
    """
    try:
        driver = get_neo4j()
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
                "This may mean the file has no imports/exports in the graph, "
                "or the path doesn't match exactly. Check with: get_architectural_context('app/...')"
            )

        lines = [f"Structural neighbors of '{file_path}':\n"]
        for row in rows:
            direction_symbol = "→" if row["direction"] == "outgoing" else "←"
            lines.append(f"  {direction_symbol} [{row['relation']}]  {row['neighbor']}")

        lines.append(f"\nTotal: {len(rows)} structural connections")
        return "\n".join(lines)

    except Exception as e:
        return f"Error querying graph: {e}\nIs Neo4j running? Try: docker compose up -d"


@mcp.tool()
def semantic_search(query: str, top_n: int = 8) -> str:
    """
    Searches the codebase using BM25 keyword ranking over function/class-level chunks.

    Returns the most relevant files ranked by relevance score.
    Use this when you don't know which file contains a concept,
    or when grep returns no results for a keyword.

    Args:
        query: Natural language or code description, e.g. "password hashing salt"
        top_n: Number of results to return (default 8)
    """
    try:
        index, chunks = get_bm25()
        results = bm25_search(index, chunks, query, top_n=top_n)

        if not results:
            return f"No results found for query: '{query}'"

        lines = [f"Top {len(results)} files for '{query}':\n"]
        for i, r in enumerate(results, 1):
            lines.append(f"  {i:2}. (score {r['score']:.3f})  {r['file']}")

        return "\n".join(lines)

    except FileNotFoundError as e:
        return str(e)
    except Exception as e:
        return f"Error running BM25 search: {e}"


if __name__ == "__main__":
    print("Starting CodeCompass MCP server...")
    print(f"  Neo4j: {NEO4J_URI}")
    print(f"  BM25 index: {BM25_INDEX_PATH}")
    mcp.run()
