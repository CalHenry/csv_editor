from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .ui import CSVEditorApp

console = Console()
csv_ve_cli = typer.Typer()

# use theme aliases instead of textual themes names for default dark and light themes
THEME_ALIASES = {
    "dark": "catppuccin-mocha",  # default dark
    "light": "textual-light",  # default light
}


def resolve_theme(theme_input: Optional[str]) -> str:
    """
    Resolve theme input to be dark or light
    """
    if theme_input is None:
        return THEME_ALIASES["dark"]

    return THEME_ALIASES.get(theme_input.lower(), theme_input)


@csv_ve_cli.command()
def main(
    file: str = typer.Argument(..., help="File to open"),
    theme: Optional[str] = typer.Option(
        None, "-t", "--theme", help="light, dar or any Textual theme name"
    ),
):
    """
    csv-ve command line
    """
    resolved_theme = resolve_theme(theme)

    if not Path(file).exists():
        console.print(f"[red]Error: File '{file}' not found[/red]")
        raise typer.Exit(1)

    app = CSVEditorApp(csv_path=file, theme=resolved_theme)
    app.run()


if __name__ == "__main__":
    csv_ve_cli()
