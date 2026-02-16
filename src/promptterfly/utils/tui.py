"""Terminal UI helpers using Rich."""
from rich.console import Console
from rich.table import Table
from rich.syntax import Syntax
from typing import List, Any


console = Console()


def print_table(columns: List[str], rows: List[List[Any]], title: str = None) -> None:
    """Print a rich table."""
    table = Table(title=title, show_header=True, header_style="bold magenta")
    for col in columns:
        table.add_column(col)
    for row in rows:
        table.add_row(*[str(cell) for cell in row])
    console.print(table)


def print_success(msg: str) -> None:
    """Print success message in green."""
    console.print(f"[bold green]✓[/] {msg}")


def print_error(msg: str) -> None:
    """Print error message in red."""
    console.print(f"[bold red]✗[/] {msg}")


def print_warning(msg: str) -> None:
    """Print warning message in yellow."""
    console.print(f"[bold yellow]⚠[/] {msg}")


def highlight_code(code: str, lexer: str = None, theme: str = "monokai") -> Syntax:
    """Return a Rich Syntax object for code highlighting."""
    return Syntax(code, lexer or "text", theme=theme, line_numbers=True, word_wrap=True)
