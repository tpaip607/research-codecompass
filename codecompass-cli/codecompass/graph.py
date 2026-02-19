"""Neo4j graph queries for structural navigation"""

import os
from typing import List, Dict, Optional
from neo4j import GraphDatabase


class GraphBackend:
    """Neo4j-backed structural graph queries"""

    def __init__(
        self,
        uri: Optional[str] = None,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ):
        self.uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self.user = user or os.getenv("NEO4J_USER", "neo4j")
        self.password = password or os.getenv("NEO4J_PASSWORD", "research123")
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
        return self._driver

    def neighbors(
        self, file_path: str, direction: str = "both"
    ) -> List[Dict[str, str]]:
        """
        Get all structural neighbors of a file.

        Args:
            file_path: Repo-relative path (e.g., "app/db/repositories/base.py")
            direction: "in", "out", or "both" (default: "both")

        Returns:
            List of dicts with keys: neighbor, relation, direction
        """
        with self.driver.session() as session:
            query = """
                MATCH (f:File {path: $path})-[r]-(neighbor:File)
                RETURN
                    neighbor.path AS neighbor,
                    type(r) AS relation,
                    CASE WHEN startNode(r) = f THEN 'out' ELSE 'in' END AS direction
                ORDER BY direction, relation, neighbor
            """
            result = session.run(query, path=file_path)
            rows = result.data()

        # Filter by direction if requested
        if direction != "both":
            rows = [r for r in rows if r["direction"] == direction]

        return rows

    def stats(self) -> Dict[str, int]:
        """Get graph statistics (node count, edge counts by type)"""
        with self.driver.session() as session:
            # Total files
            file_count = session.run("MATCH (f:File) RETURN count(f) AS count").single()[
                "count"
            ]

            # Edge counts by type
            edge_result = session.run(
                """
                MATCH ()-[r]->()
                RETURN type(r) AS relation, count(r) AS count
                ORDER BY count DESC
            """
            )
            edges = {row["relation"]: row["count"] for row in edge_result}

        return {"files": file_count, "edges": edges}

    def close(self):
        if self._driver:
            self._driver.close()
