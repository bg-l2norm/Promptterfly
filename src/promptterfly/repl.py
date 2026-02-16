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

from promptterfly.utils.banner import print_banner

def print_header():
    """Print welcome banner and a random quote."""
    print_banner()
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

def show_context_tip(command: str):
    """Show context-sensitive tips after certain commands."""
    tips = {
        "prompt create": "Next: try 'optimize improve <id>' to enhance your prompt.",
        "optimize improve": "Tip: add a dataset at .promptterfly/dataset.jsonl for better results.",
        "version history": "To rollback: 'version restore <id> <version>'.",
        "init": "Now create a prompt: 'prompt create' and add a model: 'model add'.",
        "model add": "Don't forget to 'model set-default <name>' for optimization.",
    }
    tip = tips.get(command)
    if tip:
        console.print(f"[dim]💡 {tip}[/dim]\n")

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
            # Ensure project root discovery works from cwd
            sys.argv = ["promptterfly"] + parts
            app()
            # After successful execution, show context tip if applicable
            full_cmd = " ".join(parts)
            show_context_tip(full_cmd)
        except SystemExit as e:
            if e.code != 0:
                pass  # error already shown
            else:
                # success, maybe show tip
                full_cmd = " ".join(parts)
                show_context_tip(full_cmd)
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
