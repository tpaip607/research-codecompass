"""
build_bm25_index.py

Builds a BM25 index over all Python files in the target repo.
Used for Condition B — pre-ranks files by relevance before Claude starts.

Chunks at function/class level using AST (not line-level).
Saves index as a pickle file for fast re-loading.

Usage:
    python build_bm25_index.py --repo /path/to/repo --output bm25_index.pkl

    # Query the index (for testing):
    python build_bm25_index.py --repo /path/to/repo --query "JWT token authentication"
"""

import ast
import pickle
import argparse
from pathlib import Path
from dataclasses import dataclass

from rank_bm25 import BM25Okapi


@dataclass
class CodeChunk:
    file_path: str      # repo-relative path
    chunk_type: str     # "function", "class", or "module"
    name: str           # function/class name, or filename for module-level
    source: str         # raw source code of the chunk


def tokenize(text: str) -> list[str]:
    """
    Simple tokenizer: split on non-alphanumeric chars, lowercase, filter short tokens.
    Preserves snake_case and camelCase as meaningful tokens.
    """
    import re
    # Split camelCase and snake_case into sub-tokens
    text = re.sub(r'([a-z])([A-Z])', r'\1 \2', text)      # camelCase → camel Case
    text = re.sub(r'[^a-zA-Z0-9_]', ' ', text)             # non-alphanumeric → space
    tokens = text.lower().split()
    return [t for t in tokens if len(t) > 1]               # drop single chars


def extract_chunks(file_path: Path, repo_root: Path) -> list[CodeChunk]:
    """Extract function/class level chunks from a Python file."""
    chunks = []
    rel_path = str(file_path.relative_to(repo_root))
    source_code = file_path.read_text(encoding="utf-8")

    try:
        tree = ast.parse(source_code)
    except SyntaxError:
        # Fall back to module-level chunk
        return [CodeChunk(file_path=rel_path, chunk_type="module", name=file_path.stem, source=source_code)]

    lines = source_code.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            if not hasattr(node, "lineno"):
                continue

            start = node.lineno - 1
            end = getattr(node, "end_lineno", start + 20)
            chunk_source = "\n".join(lines[start:end])

            chunk_type = "class" if isinstance(node, ast.ClassDef) else "function"
            chunks.append(CodeChunk(
                file_path=rel_path,
                chunk_type=chunk_type,
                name=node.name,
                source=chunk_source,
            ))

    # Always include a module-level chunk (imports + top-level code)
    chunks.append(CodeChunk(
        file_path=rel_path,
        chunk_type="module",
        name=file_path.stem,
        source=source_code[:2000],  # First 2000 chars captures imports
    ))

    return chunks


def build_index(repo_root: Path) -> tuple[BM25Okapi, list[CodeChunk]]:
    """Build BM25 index over all Python files in the repo."""
    all_chunks = []

    for py_file in sorted(repo_root.rglob("*.py")):
        try:
            chunks = extract_chunks(py_file, repo_root)
            all_chunks.extend(chunks)
        except Exception:
            continue

    print(f"Indexed {len(all_chunks)} chunks from {repo_root}")

    tokenized = [tokenize(f"{c.file_path} {c.name} {c.source}") for c in all_chunks]
    index = BM25Okapi(tokenized)

    return index, all_chunks


def search(index: BM25Okapi, chunks: list[CodeChunk], query: str, top_n: int = 10) -> list[dict]:
    """Return top-N files ranked by BM25 score for a given query."""
    query_tokens = tokenize(query)
    scores = index.get_scores(query_tokens)

    # Aggregate scores at file level (take max score per file)
    file_scores: dict[str, float] = {}
    for chunk, score in zip(chunks, scores):
        if chunk.file_path not in file_scores or score > file_scores[chunk.file_path]:
            file_scores[chunk.file_path] = score

    ranked = sorted(file_scores.items(), key=lambda x: x[1], reverse=True)
    return [{"file": f, "score": round(s, 4)} for f, s in ranked[:top_n]]


def main():
    parser = argparse.ArgumentParser(description="Build BM25 index over a Python repo")
    parser.add_argument("--repo", required=True, help="Path to target repo")
    parser.add_argument("--output", default="bm25_index.pkl", help="Output pickle file")
    parser.add_argument("--query", help="Optional: test query to run after building index")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    index, chunks = build_index(repo_root)

    output_path = Path(args.output)
    with open(output_path, "wb") as f:
        pickle.dump({"index": index, "chunks": chunks, "repo_root": str(repo_root)}, f)
    print(f"Saved BM25 index to {output_path} ({len(chunks)} chunks)")

    if args.query:
        results = search(index, chunks, args.query)
        print(f"\nTop results for: '{args.query}'")
        for r in results:
            print(f"  {r['score']:6.4f}  {r['file']}")


if __name__ == "__main__":
    main()
