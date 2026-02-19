"""
build_graph.py

Loads AST parser output (edges.json) into Neo4j.

Creates:
  - (:File {path}) nodes
  - [:IMPORTS], [:INHERITS], [:INSTANTIATES] relationships

Usage:
    python build_graph.py --edges /tmp/edges.json
    python build_graph.py --edges /tmp/edges.json --clear  # wipe graph first
"""

import json
import argparse
from pathlib import Path

from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "research123"


def clear_graph(session):
    session.run("MATCH (n) DETACH DELETE n")
    print("Graph cleared")


def create_indexes(session):
    session.run("CREATE INDEX file_path IF NOT EXISTS FOR (f:File) ON (f.path)")
    print("Index created on File.path")


def load_edges(session, edges: list[dict]):
    batch_size = 100
    total = 0

    for i in range(0, len(edges), batch_size):
        batch = edges[i:i + batch_size]
        session.run(
            """
            UNWIND $edges AS edge
            MERGE (a:File {path: edge.source})
            MERGE (b:File {path: edge.target})
            WITH a, b, edge
            CALL apoc.merge.relationship(a, edge.relation, {}, {}, b) YIELD rel
            RETURN count(rel)
            """,
            edges=batch,
        )
        total += len(batch)

    print(f"Loaded {total} edges into Neo4j")


def load_edges_no_apoc(session, edges: list[dict]):
    """Fallback loader without APOC — creates each relation type separately."""
    for relation in ["IMPORTS", "INHERITS", "INSTANTIATES"]:
        batch = [e for e in edges if e["relation"] == relation]
        if not batch:
            continue

        if relation == "IMPORTS":
            query = """
            UNWIND $edges AS edge
            MERGE (a:File {path: edge.source})
            MERGE (b:File {path: edge.target})
            MERGE (a)-[:IMPORTS]->(b)
            """
        elif relation == "INHERITS":
            query = """
            UNWIND $edges AS edge
            MERGE (a:File {path: edge.source})
            MERGE (b:File {path: edge.target})
            MERGE (a)-[:INHERITS]->(b)
            """
        elif relation == "INSTANTIATES":
            query = """
            UNWIND $edges AS edge
            MERGE (a:File {path: edge.source})
            MERGE (b:File {path: edge.target})
            MERGE (a)-[:INSTANTIATES]->(b)
            """

        session.run(query, edges=batch)
        print(f"  Loaded {len(batch)} {relation} edges")


def verify_graph(session):
    result = session.run("MATCH (n:File) RETURN count(n) AS nodes")
    nodes = result.single()["nodes"]

    result = session.run("MATCH ()-[r]->() RETURN count(r) AS rels")
    rels = result.single()["rels"]

    print(f"Graph contains {nodes} nodes and {rels} relationships")


def main():
    parser = argparse.ArgumentParser(description="Load AST edges into Neo4j")
    parser.add_argument("--edges", default="/tmp/edges.json", help="Path to edges.json from ast_parser.py")
    parser.add_argument("--clear", action="store_true", help="Clear the graph before loading")
    args = parser.parse_args()

    edges_path = Path(args.edges)
    if not edges_path.exists():
        print(f"Error: edges file not found: {edges_path}")
        print("Run ast_parser.py first.")
        return

    edges = json.loads(edges_path.read_text())
    print(f"Loaded {len(edges)} edges from {edges_path}")

    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

    try:
        with driver.session() as session:
            if args.clear:
                clear_graph(session)

            create_indexes(session)

            # Try APOC first, fall back to explicit queries
            try:
                load_edges(session, edges)
            except Exception as e:
                if "apoc" in str(e).lower():
                    print("APOC not available, using fallback loader")
                    load_edges_no_apoc(session, edges)
                else:
                    raise

            verify_graph(session)

    finally:
        driver.close()


if __name__ == "__main__":
    main()
