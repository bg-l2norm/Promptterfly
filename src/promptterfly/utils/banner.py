"""Banner utilities for Promptterfly REPL."""
import textwrap
from rich.console import Console
from typing import Final

console = Console()

def get_butterfly_banner() -> str:
    """
    Returns a starry, color-themed ASCII art banner of a butterfly with sparkles.
    Uses Rich markup for ANSI colors:
    - Blue/purple for background stars
    - Gold/yellow for sparkles
    - Cyan/magenta for the butterfly
    """
    banner = r"""
        [purple]✦[/purple]   [cyan]                                [/cyan]   [yellow]✧[/yellow]
        [purple]✧[/purple]   [magenta]                           [/magenta]   [yellow]✦[/yellow]
    [gold]✦[/gold]     [cyan]                        [/cyan]     [gold]⋆[/gold]
    [gold]✧[/gold]   [cyan]                         [/cyan]   [gold]✨[/gold]
        [cyan]                      [/cyan]
        [cyan]                      [/cyan]
    [magenta]            ⢀⣀⣤⣤⣤⣀⡀       [/magenta]
    [magenta]         ⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⡀    [/magenta]
    [magenta]        ⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄   [/magenta]
    [magenta]        ⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇   [/magenta]
    [magenta]        ⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇   [/magenta]
    [cyan]      ⢀⣤⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣄  [/cyan]
    [cyan]      ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧ [/cyan]
    [cyan]      ⣿⣿⣿⠿⠛⠻⢿⣿⣿⣿⡿⠿⠛⠻⣿⣿⣿⣿⣿⡆[/cyan]
    [cyan]      ⢸⣿⣿⢱  ⢸⣿⡏⢸⣿ ⢀⡀⣿⣿⣿⣿⣿⡇[/cyan]
    [cyan]      ⢸⣿⣿⢸  ⢸⣿⡇⢸⣿ ⣿⣿⣿⣿⣿⣿⣿⡇[/cyan]
    [cyan]      ⢸⣿⣿⢸  ⢸⣿⡇⢸⣿ ⣿⣿⣿⣿⣿⣿⣿⡇[/cyan]
    [cyan]      ⢸⣿⣿⢸  ⢸⣿⡇⢸⣿ ⣿⣿⣿⣿⣿⣿⣿⡇[/cyan]
    [cyan]      ⢸⣿⣿⢸  ⢸⣿⡇⢸⣿ ⣿⣿⣿⣿⣿⣿⣿⡇[/cyan]
    [cyan]      ⠈⠻⣿⢸  ⢸⣿⠇⢸⣿ ⣿⣿⣿⣿⣿⣿⡿⠃[/cyan]
    [magenta]       ⠸⢿⢸  ⢸⣿ ⢸⣿ ⣿⣿⣿⡿⠟⠁  [/magenta]
    [magenta]        ⠈   ⠈⠁ ⠉⠉ ⠉⠉⠁     [/magenta]
        [cyan]                      [/cyan]
        [cyan]                      [/cyan]
    [purple]  ✦[/purple]     [cyan]                      [/cyan]     [purple]⋆[/purple]
    [purple] ✧[/purple]   [magenta]                      [/magenta]   [purple]✨[/purple]
        [yellow]✦[/yellow]   [blue]                      [/blue]   [gold]✧[/gold]

    [bold cyan]╔═══════════════════════════════════════════════════╗[/bold cyan]
    [bold cyan]║[/bold cyan]  [bold magenta]    __  __  ____   ___  ____   ____ ___ [/bold magenta]  [bold cyan]║[/bold cyan]
    [bold cyan]║[/bold cyan]  [bold magenta]   |  \/  |/ ___| / _ \|  _ \ / ___|_ _|[/bold magenta]  [bold cyan]║[/bold cyan]
    [bold cyan]║[/bold cyan]  [bold magenta]   | |\/| | |  _ | | | | | | | |  _ || |[/bold magenta]  [bold cyan]║[/bold cyan]
    [bold cyan]║[/bold cyan]  [bold magenta]   | |  | | |_| || |_| | |_| | |_| || |[/bold magenta]  [bold cyan]║[/bold cyan]
    [bold cyan]║[/bold cyan]  [bold magenta]   |_|  |_|\____| \___/|____/ \____|___|[/bold magenta]  [bold cyan]║[/bold cyan]
    [bold cyan]║[/bold cyan]  [bold yellow]        ✨ Prompt Manager v0.1.0 ✨[/bold yellow]  [bold cyan]║[/bold cyan]
    [bold cyan]╚═══════════════════════════════════════════════════╝[/bold cyan]
    """
    return textwrap.dedent(banner).lstrip()

def print_banner():
    """Print the starry butterfly banner to console."""
    console.print(get_butterfly_banner())
