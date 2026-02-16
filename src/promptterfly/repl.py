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

# Command aliases - map short forms to full command sequences
ALIAS_MAP = {
    "ls": ["prompt", "list"],
    "new": ["prompt", "create"],
    "create": ["prompt", "create"],
    "show": ["prompt", "show"],  # preserves following argument as ID
    "del": ["prompt", "delete"],
    "run": ["prompt", "render"],
    "hist": ["version", "history"],
    "restore": ["version", "restore"],
    "opt": ["optimize", "improve"],
    "models": ["model", "list"],
    "addmodel": ["model", "add"],
    "setmodel": ["model", "set-default"],
}

def print_header():
    """Print welcome banner and a random quote."""
    print_banner()
    console.print(f"[italic]\"{get_random_quote()}\"[/italic]\n")
    console.print("[green]Welcome to Promptterfly![/green]")
    console.print("Type [bold]'help'[/bold] for available commands, or [bold]'exit'[/bold] to quit.\n")

def print_help():
    """Print a minimal help listing."""
    console.print("\n[bold cyan]Available commands[/bold cyan] (use without prefix):")
    console.print("  The REPL shows a colorful startup banner and spiky loading animation during optimization.\n")
    
    # First show aliases for quick reference
    console.print("[bold]Command aliases:[/bold]")
    console.print("  ls           → prompt list")
    console.print("  new, create  → prompt create")
    console.print("  show <id>    → prompt show <id>")
    console.print("  del          → prompt delete")
    console.print("  run          → prompt render")
    console.print("  hist         → version history")
    console.print("  restore      → version restore")
    console.print("  opt          → optimize improve")
    console.print("  models       → model list")
    console.print("  addmodel     → model add")
    console.print("  setmodel     → model set-default")
    console.print("")

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
    console.print("[bold]Full command list:[/bold]")
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
    """Show first-run tip if no project initialized."""
    try:
        find_project_root()
    except FileNotFoundError:
        console.print("[dim]No project found. Run 'init' to get started.[/dim]\n")

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

        # Resolve aliases before dispatching
        if command in ALIAS_MAP:
            replacement = ALIAS_MAP[command]
            # For 'show' and commands that take an immediate argument, keep the rest
            if command == "show" and len(parts) > 1:
                parts = replacement + parts[1:]
            else:
                parts = replacement + parts[1:]

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
