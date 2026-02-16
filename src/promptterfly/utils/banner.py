"""Banner utilities for Promptterfly REPL."""
from rich.console import Console

console = Console()

def get_butterfly_banner() -> str:
    """
    Returns a starry, color-themed ASCII art banner of a butterfly with sparkles.
    The butterfly is compact and recognizable. Sparkles appear above and below.
    """
    # Top sparkles
    top = (
        "[purple]✦[/purple]" + " " * 38 + "[yellow]✧[/yellow]\n"
        "[purple]✧[/purple]" + " " * 38 + "[yellow]✨[/yellow]\n"
    )
    # Butterfly art (9 lines)
    art = """\
[cyan]       .-.[/cyan]
[magenta]     .'   `.[/magenta]
[cyan]    /       \\[/cyan]
[magenta]   ;         ;[/magenta]
[cyan]   |    •    |[/cyan]
[magenta]   ;         ;[/magenta]
[cyan]    \\       /[/cyan]
[magenta]     `.   .'[/magenta]
[cyan]       `-'[/cyan]
"""
    # Bottom sparkles
    bottom = (
        "[yellow]✦[/yellow]" + " " * 38 + "[purple]✧[/purple]\n"
        "[yellow]✧[/yellow]" + " " * 38 + "[purple]✨[/purple]\n"
    )
    return top + art + bottom

def print_banner():
    """Print the starry butterfly banner to console."""
    console.print(get_butterfly_banner())
