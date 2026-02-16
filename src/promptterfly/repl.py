"""Interactive REPL for Promptterfly."""
import sys
import shlex
from pathlib import Path
from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
import random

from promptterfly.cli import app
from promptterfly.core.config import load_config
from promptterfly.utils.io import find_project_root
from promptterfly.utils.quotes import get_random_quote

console = Console()

BANNER = r"""
╔═══════════════════════════════════════════════════╗
║            ____  _  _   ___   ___  _   _         ║
║           |  _ \| || | |_ _| |_ _|| | | |        ║
║           | |_) | || |  | |   | | | |_| |        ║
║           |  _ <|__  _| | |   | | |  _  |        ║
║           |_| \_\  ||_| |___| |___||_| |_|        ║
║                    Prompt Manager v0.1.0           ║
╚═══════════════════════════════════════════════════╝
"""

def print_header():
    """Print welcome banner and a random quote."""
    console.print(BANNER, style="bold cyan")
    console.print(f"[italic]\"{get_random_quote()}\"[/italic]\n")
    console.print("[green]Welcome to Promptterfly![/green]")
    console.print("Type [bold]'help'[/bold] for available commands, or [bold]'exit'[/bold] to quit.\n")

def print_help():
    """Print a minimal help listing."""
    console.print("\n[bold cyan]Available commands[/bold cyan] (use without prefix):")
    commands = [
        ("init [--path dir]", "Initialize project"),
        ("prompt list", "List prompts"),
        ("prompt show <id>", "Show prompt"),
        ("prompt create", "Create prompt interactively"),
        ("prompt update <id>", "Update prompt"),
        ("prompt delete <id>", "Delete prompt"),
        ("prompt render <id> [vars.json]", "Render with variables"),
        ("version history <id>", "Show version history"),
        ("version restore <id> <version>", "Restore version"),
        ("optimize improve <id> [--strategy few_shot] [--dataset path]", "Run optimization"),
        ("model list", "List configured models"),
        ("model add <name>", "Add model"),
        ("model remove <name>", "Remove model"),
        ("model set-default <name>", "Set default model"),
        ("config show", "Show configuration"),
        ("config set <key> <value>", "Set config value"),
        ("help", "Show this help"),
        ("exit / quit", "Exit REPL"),
    ]
    for cmd, desc in commands:
        console.print(f"  [yellow]{cmd}[/yellow] – {desc}")
    console.print("")

def detect_first_run() -> bool:
    """Check if this is the first REPL run."""
    flag = Path(".promptterfly/.repl_first_done")
    if flag.exists():
        return False
    return True

def mark_first_run():
    Path(".promptterfly").mkdir(parents=True, exist_ok=True)
    flag = Path(".promptterfly/.repl_first_done")
    flag.touch()

def show_onboarding():
    """Show quick start tips on first run."""
    console.print("\n[bold green]Quick Start:[/bold green]")
    console.print("  1. Navigate to your project directory")
    console.print("  2. Run [bold]init[/bold] once:  [yellow]init[/yellow]")
    console.print("  3. Create a prompt:         [yellow]prompt create[/yellow]")
    console.print("  4. Optimize it:             [yellow]optimize improve <id>[/yellow]")
    console.print("  5. View history:            [yellow]version history <id>[/yellow]")
    console.print("\nAll commands work without the 'promptterfly' prefix.\n")

def repl_loop():
    """Main REPL loop."""
    print_header()

    first = detect_first_run()
    if first:
        show_onboarding()
        mark_first_run()

    while True:
        try:
            # Read input with a nice prompt
            cmd_str = console.input("[bold cyan]❯[/bold cyan] ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[green]Goodbye![/green]")
            break

        if not cmd_str:
            continue

        # Handle built-in commands
        parts = shlex.split(cmd_str)
        command = parts[0].lower()

        if command in ("exit", "quit"):
            console.print("[green]Goodbye![/green]")
            break

        if command == "help":
            print_help()
            continue

        # Dispatch to Typer CLI programmatically
        try:
            # Find project root if needed (for commands that require it)
            # We'll let Typer handle it; just pass through
            from promptterfly.core.config import load_config
            # Ensure project root discovery works from cwd
            # Call the Typer app with the command line
            sys.argv = ["promptterfly"] + parts
            # Clear any previous state; call app
            app()
        except SystemExit as e:
            # Typer calls sys.exit; we continue unless it's an error we want to break on
            # Non-zero exit indicates error; we just continue REPL
            if e.code != 0:
                # Error already printed by Typer; continue
                pass
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")

def main():
    try:
        repl_loop()
    except KeyboardInterrupt:
        console.print("\n[green]Goodbye![/green]")
        sys.exit(0)

if __name__ == "__main__":
    main()
