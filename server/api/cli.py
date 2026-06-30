"""This module provides different helper commands
"""

from pathlib import Path

import typer

cli = typer.Typer()

@cli.command()
def ping():
    # just a command so that export-openapi is not "run"
    print("pong")

@cli.command()
def export_openapi(
    target_path: Path = typer.Argument(
        exists=None,
        file_okay=True,
        dir_okay=False,
        help="Path of the YAML or JSON data file",
    )
):
    """Export OpenAPI specification to a file."""
    import json
    import yaml

    import sys
    # add server/ to path
    sys.path.append(str(Path(__file__).parent.parent))

    from api import api

    openapi = api.app.openapi()
    version = openapi.get("openapi", "unknown version")

    print(f"writing openapi spec v{version}")
    with open(target_path, "w") as f:
        if str(target_path).endswith(".json"):
            json.dump(openapi, f, indent=2)
        else:
            yaml.dump(openapi, f, sort_keys=False)

    print(f"spec written to {target_path}")

def main() -> None:
    cli()
