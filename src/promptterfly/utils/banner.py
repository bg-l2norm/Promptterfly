"""Banner utilities for Promptterfly REPL."""
from rich.console import Console

console = Console()

def get_butterfly_banner() -> str:
    """
    Returns a starry, color-themed ASCII art banner of a butterfly with sparkles.
    The design is compact (~40 columns) and uses regular spaces for reliable rendering.
    Sparkles are placed above and below the butterfly.
    """
    # Top sparkles
    top = (
        "[purple]✦[/purple]" + " " * 38 + "[yellow]✧[/yellow]\n"
        "[purple]✧[/purple]" + " " * 38 + "[yellow]✨[/yellow]\n"
    )
    # Butterfly art (alternating cyan and magenta)
    art = """\
[cyan]       .-.[/cyan]
[magenta]     .'   `.[/magenta]
[cyan]    /       \\[/cyan]
[magenta]   ;         ;[/magenta]
[cyan]   |    •    |[/cyan]
[magenta]   ;       /[/magenta]
[cyan]     `.   .'[/cyan]
[magenta]       `-'[/magenta]
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
