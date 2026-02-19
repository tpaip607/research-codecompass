"""BM25 search backend for semantic code search"""

import os
import pickle
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class CodeChunk:
    """Code chunk structure (must match data_processing/build_bm25_index.py)"""
    file_path: str
    chunk_type: str
    name: str
    source: str


class BM25Backend:
    """BM25 keyword search over code chunks"""

    def __init__(self, index_path: Optional[str] = None):
        self.index_path = Path(
            index_path or os.getenv("BM25_INDEX_PATH", "bm25_index.pkl")
        )
        self._index = None
        self._chunks = None

    def _load(self):
        """Lazy-load the BM25 index"""
        if self._index is None:
            if not self.index_path.exists():
                raise FileNotFoundError(
                    f"BM25 index not found at {self.index_path}. "
                    "Build it with: python data_processing/build_bm25_index.py --repo <path>"
                )
            with open(self.index_path, "rb") as f:
                data = pickle.load(f)
            self._index = data["index"]
            self._chunks = data["chunks"]

    def search(self, query: str, top_n: int = 8) -> List[Dict[str, any]]:
        """
        Search the codebase using BM25 ranking.

        Args:
            query: Natural language or code keywords
            top_n: Number of results to return

        Returns:
            List of dicts with keys: file, score, chunk_text, chunk_type
        """
        self._load()

        # Tokenize query
        tokens = query.lower().split()

        # Get BM25 scores
        scores = self._index.get_scores(tokens)

        # Get top N indices
        top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[
            :top_n
        ]

        results = []
        seen_files = set()
        for idx in top_indices:
            chunk = self._chunks[idx]
            score = scores[idx]

            # Handle both dict and CodeChunk object formats
            if isinstance(chunk, CodeChunk):
                file_path = chunk.file_path
                chunk_text = chunk.source
                chunk_type = chunk.chunk_type
            else:
                file_path = chunk.get("file", chunk.get("file_path", ""))
                chunk_text = chunk.get("text", chunk.get("source", ""))
                chunk_type = chunk.get("type", chunk.get("chunk_type", ""))

            # Only return the top result per file
            if file_path not in seen_files:
                results.append(
                    {
                        "file": file_path,
                        "score": float(score),
                        "chunk_text": chunk_text,
                        "chunk_type": chunk_type,
                    }
                )
                seen_files.add(file_path)

            if len(results) >= top_n:
                break

        return results
