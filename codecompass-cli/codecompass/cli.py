"""CodeCompass CLI - Structural navigation for codebases"""

import sys
import click
from .graph import GraphBackend
from .search import BM25Backend


@click.group()
@click.version_option()
def cli():
    """
    CodeCompass - Navigate codebases by structure, not just semantics.

    \b
    Examples:
      codecompass neighbors app/db/repositories/base.py
      codecompass search "logger parameter BaseRepository" --top 10
      codecompass stats
    """
    pass


@cli.command()
@click.argument("file_path")
@click.option(
    "--direction",
    type=click.Choice(["in", "out", "both"]),
    default="both",
    help="Filter by edge direction (default: both)",
)
@click.option(
    "--json", "output_json", is_flag=True, help="Output as JSON instead of text"
)
def neighbors(file_path, direction, output_json):
    """
    Show all files structurally connected to FILE_PATH.

    \b
    Displays:
      - Files that import this file (incoming)
      - Files this file imports (outgoing)
      - Inheritance and instantiation relationships

    \b
    Examples:
      codecompass neighbors app/db/repositories/base.py
      codecompass neighbors app/api/routes/articles.py --direction in
    """
    try:
        graph = GraphBackend()
        results = graph.neighbors(file_path, direction)

        if not results:
            click.echo(
                f"No structural neighbors found for '{file_path}'.\n"
                "Check the file path or run 'codecompass stats' to verify the graph is loaded.",
                err=True,
            )
            sys.exit(1)

        if output_json:
            import json

            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"Structural neighbors of '{file_path}':\n")
            for row in results:
                arrow = "→" if row["direction"] == "out" else "←"
                click.echo(f"  {arrow} [{row['relation']}]  {row['neighbor']}")
            click.echo(f"\nTotal: {len(results)} structural connections")

        graph.close()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            "\nIs Neo4j running? Try: docker compose up -d neo4j", err=True
        )
        sys.exit(1)


@cli.command()
@click.argument("query")
@click.option("--top", default=8, help="Number of results to return (default: 8)")
@click.option(
    "--json", "output_json", is_flag=True, help="Output as JSON instead of text"
)
def search(query, top, output_json):
    """
    Search the codebase using BM25 keyword ranking.

    \b
    Returns the most relevant files ranked by score.
    Use this when you don't know which file contains a concept.

    \b
    Examples:
      codecompass search "password hashing salt"
      codecompass search "JWT token validation" --top 5
    """
    try:
        bm25 = BM25Backend()
        results = bm25.search(query, top_n=top)

        if not results:
            click.echo(f"No results found for query: '{query}'", err=True)
            sys.exit(1)

        if output_json:
            import json

            click.echo(json.dumps(results, indent=2))
        else:
            click.echo(f"Top {len(results)} files for '{query}':\n")
            for i, r in enumerate(results, 1):
                click.echo(f"  {i:2}. (score {r['score']:.3f})  {r['file']}")

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option(
    "--json", "output_json", is_flag=True, help="Output as JSON instead of text"
)
def stats(output_json):
    """
    Show graph statistics (file count, edge counts by type).

    \b
    Examples:
      codecompass stats
      codecompass stats --json
    """
    try:
        graph = GraphBackend()
        data = graph.stats()

        if output_json:
            import json

            click.echo(json.dumps(data, indent=2))
        else:
            click.echo("CodeCompass Graph Statistics:\n")
            click.echo(f"  Files: {data['files']}")
            click.echo(f"\n  Edges:")
            for relation, count in data["edges"].items():
                click.echo(f"    {relation:15} {count:4}")

        graph.close()

    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
