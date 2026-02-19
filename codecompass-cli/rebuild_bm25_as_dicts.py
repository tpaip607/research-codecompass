"""Rebuild BM25 index with plain dicts instead of CodeChunk objects"""

import pickle
import sys
from pathlib import Path

# Load the existing index
index_path = Path("../bm25_index.pkl")
if not index_path.exists():
    print(f"Error: {index_path} not found")
    sys.exit(1)

print(f"Loading {index_path}...")

# Add parent to path to import CodeChunk
sys.path.insert(0, str(Path(__file__).parent.parent / "data_processing"))
from build_bm25_index import CodeChunk

with open(index_path, "rb") as f:
    data = pickle.load(f)

# Convert CodeChunk objects to dicts
chunks_as_dicts = []
for chunk in data["chunks"]:
    if isinstance(chunk, CodeChunk):
        chunks_as_dicts.append({
            "file_path": chunk.file_path,
            "chunk_type": chunk.chunk_type,
            "name": chunk.name,
            "source": chunk.source,
        })
    else:
        chunks_as_dicts.append(chunk)

# Save new index
new_data = {
    "index": data["index"],
    "chunks": chunks_as_dicts,
}

output_path = Path("../bm25_index_dicts.pkl")
with open(output_path, "wb") as f:
    pickle.dump(new_data, f)

print(f"Saved {len(chunks_as_dicts)} chunks to {output_path}")
print("Use: export BM25_INDEX_PATH=bm25_index_dicts.pkl")
