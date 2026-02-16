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
    # removed "addmodel", "setmodel" in favor of multi-word aliases below
    "find": ["prompt", "find"],
    "search": ["prompt", "find"],
    "f": ["prompt", "find"],
}

# Multi-word aliases (natural verb-noun phrasing)
MULTI_ALIASES = {
    "add model": ["model", "add"],
    "remove model": ["model", "remove"],
    "list models": ["model", "list"],
    "set model": ["model", "set-default"],
    "config set": ["config-set"],
}

def print_header():
    """Print welcome banner and a random quote."""
    print_banner()
    console.print(f"[italic]\"{get_random_quote()}\"[/italic]\n")
    console.print("[green]Welcome to Promptterfly![/green]")
    console.print("Type [bold]'help'[/bold] for available commands, or [bold]'exit'[/bold] to quit.\n")

def print_help():
    """Print a clear, descriptive help listing."""
    console.print("\n[bold cyan]Commands[/bold cyan] (type directly in the REPL):")
    
    commands = [
        ("init [--path dir]", "Initialize a project"),
        ("prompt list (ls)", "List all prompts"),
        ("prompt create (new/create)", "Create a new prompt interactively"),
        ("prompt show <id> (show)", "Show prompt details"),
        ("prompt delete <id> (del)", "Delete a prompt"),
        ("prompt render <id> [vars.json] (run)", "Render a prompt with variables"),
        ("prompt find <query> (find/search/f)", "Fuzzy search prompts"),
        ("version history <id> (hist)", "Show prompt version history"),
        ("version restore <id> <version> (restore)", "Restore a prompt version"),
        ("optimize improve <id> (opt)", "Run optimization to improve a prompt"),
        ("model list (models/list models)", "List configured models"),
        ("model add (add model)", "Add a new model (interactive prompts)"),
        ("model remove <name> (remove model)", "Remove a model"),
        ("model set-default <name> (set model)", "Set the default model"),
        ("config show", "Show current configuration"),
        ("config set <key> <value> (config set)", "Set a configuration value"),
        ("help", "Show this help"),
        ("exit / quit", "Exit the REPL"),
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

        # Resolve multi-word aliases first (e.g., "add model")
        matched = False
        for n in (3, 2):  # check longer phrases first
            if len(parts) >= n:
                phrase = " ".join(parts[:n])
                if phrase in MULTI_ALIASES:
                    replacement = MULTI_ALIASES[phrase]
                    parts = replacement + parts[n:]
                    matched = True
                    break
        if not matched:
            # Single-word alias
            if command in ALIAS_MAP:
                replacement = ALIAS_MAP[command]
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
