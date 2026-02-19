"""
ast_parser.py

Parses all .py files in a target repo and extracts structural edges:
  - IMPORTS:      file A imports from file B
  - INHERITS:     class in A inherits from class defined in B
  - INSTANTIATES: file A calls constructor of class defined in B

Output: JSON file with list of {source, target, relation} dicts.

Usage:
    python ast_parser.py --repo /path/to/repo --output edges.json
"""

import ast
import json
import argparse
from pathlib import Path
from typing import Optional


def find_python_files(repo_root: Path) -> list[Path]:
    return sorted(repo_root.rglob("*.py"))


def resolve_import_to_path(module: str, current_file: Path, repo_root: Path) -> Optional[str]:
    """
    Convert a module import string to a repo-relative file path.
    e.g. "app.services.jwt" -> "app/services/jwt.py"
    Returns None if the module is external (not in repo).
    """
    parts = module.split(".")
    candidate = repo_root.joinpath(*parts).with_suffix(".py")
    if candidate.exists():
        return str(candidate.relative_to(repo_root))

    # Try as package __init__.py
    candidate_init = repo_root.joinpath(*parts, "__init__.py")
    if candidate_init.exists():
        return str(candidate_init.relative_to(repo_root))

    return None


def extract_edges(file_path: Path, repo_root: Path) -> list[dict]:
    """
    Parse a single Python file and return all structural edges it produces.
    """
    edges = []
    source = str(file_path.relative_to(repo_root))

    try:
        source_code = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source_code, filename=str(file_path))
    except (SyntaxError, UnicodeDecodeError):
        return edges

    # Collect top-level class names defined in this file for INSTANTIATES resolution
    defined_classes: dict[str, str] = {}  # class_name -> source file

    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            defined_classes[node.name] = source

    for node in ast.walk(tree):

        # --- IMPORTS ---
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = resolve_import_to_path(alias.name, file_path, repo_root)
                if target and target != source:
                    edges.append({"source": source, "target": target, "relation": "IMPORTS"})

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                # Handle relative imports
                if node.level and node.level > 0:
                    # Relative import: resolve from current package
                    pkg_parts = list(file_path.relative_to(repo_root).parent.parts)
                    # Go up `level - 1` levels
                    for _ in range(node.level - 1):
                        if pkg_parts:
                            pkg_parts.pop()
                    module_full = ".".join(pkg_parts + [node.module]) if pkg_parts else node.module
                else:
                    module_full = node.module

                target = resolve_import_to_path(module_full, file_path, repo_root)
                if target and target != source:
                    edges.append({"source": source, "target": target, "relation": "IMPORTS"})

        # --- INHERITS ---
        elif isinstance(node, ast.ClassDef):
            for base in node.bases:
                base_name = None
                if isinstance(base, ast.Name):
                    base_name = base.id
                elif isinstance(base, ast.Attribute):
                    base_name = base.attr

                if base_name:
                    # Check if base class is imported from another file
                    for edge in edges:
                        if edge["relation"] == "IMPORTS" and edge["source"] == source:
                            edges.append({
                                "source": source,
                                "target": edge["target"],
                                "relation": "INHERITS",
                                "meta": f"{node.name} inherits {base_name}"
                            })
                            break

        # --- INSTANTIATES (Call expressions) ---
        elif isinstance(node, ast.Call):
            called_name = None
            if isinstance(node.func, ast.Name):
                called_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                called_name = node.func.attr

            if called_name and called_name[0].isupper():  # Convention: classes start with uppercase
                # Check if this class is imported from another file
                for edge in edges:
                    if edge["relation"] == "IMPORTS" and edge["source"] == source:
                        edges.append({
                            "source": source,
                            "target": edge["target"],
                            "relation": "INSTANTIATES",
                            "meta": f"calls {called_name}()"
                        })
                        break

    # Deduplicate edges (same source/target/relation)
    seen = set()
    unique_edges = []
    for edge in edges:
        key = (edge["source"], edge["target"], edge["relation"])
        if key not in seen:
            seen.add(key)
            unique_edges.append(edge)

    return unique_edges


def parse_repo(repo_root: Path) -> list[dict]:
    all_edges = []
    files = find_python_files(repo_root)
    print(f"Found {len(files)} Python files")

    for f in files:
        edges = extract_edges(f, repo_root)
        all_edges.extend(edges)

    print(f"Extracted {len(all_edges)} edges")
    return all_edges


def main():
    parser = argparse.ArgumentParser(description="Parse a Python repo into structural graph edges")
    parser.add_argument("--repo", required=True, help="Path to the target repo root")
    parser.add_argument("--output", default="edges.json", help="Output JSON file path")
    args = parser.parse_args()

    repo_root = Path(args.repo).resolve()
    if not repo_root.exists():
        print(f"Error: repo path does not exist: {repo_root}")
        return

    edges = parse_repo(repo_root)

    output_path = Path(args.output)
    output_path.write_text(json.dumps(edges, indent=2))
    print(f"Saved {len(edges)} edges to {output_path}")

    # Print summary
    from collections import Counter
    relation_counts = Counter(e["relation"] for e in edges)
    for rel, count in sorted(relation_counts.items()):
        print(f"  {rel}: {count}")


if __name__ == "__main__":
    main()
