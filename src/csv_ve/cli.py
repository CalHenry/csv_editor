from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from textual.theme import BUILTIN_THEMES

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
    file: str = typer.Argument(..., help="CSV file to open"),
    theme: Optional[str] = typer.Option(
        None,
        "-t",
        "--theme",
        help="light, dark or any Textual theme name. Can change the theme in the running app",
    ),
):
    """
    csv-ve command line
    """
    if theme is not None:
        available_themes = list(BUILTIN_THEMES.keys())
        custom_theme_aliases = list(THEME_ALIASES.keys())
        if theme not in available_themes and theme not in custom_theme_aliases:
            console.print(f"[red]Error: Theme '{theme}' not found[/red]")
            console.print(
                f"[yellow]Available themes:[/yellow] {', '.join(sorted(available_themes + custom_theme_aliases))}"
            )
            raise typer.Exit(1)

    resolved_theme = resolve_theme(theme)

    file_path = Path(file)

    if not file_path.exists():
        console.print(f"[red]Error: File '{file}' not found[/red]")
        raise typer.Exit(1)
    if not file_path.suffix.lower() == ".csv":
        console.print(f"[red]Error: '{file}' is not a CSV file[/red]")
        raise typer.Exit(1)

    app = CSVEditorApp(csv_path=file, theme=resolved_theme)
    app.run()


if __name__ == "__main__":
    csv_ve_cli()
