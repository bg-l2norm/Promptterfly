"""Prompt management commands."""
import typer
from typing import Optional
from promptterfly.core.models import Prompt
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_table, print_success, print_error
from datetime import datetime
import uuid

app = typer.Typer(help="Manage prompts")


def _generate_id() -> str:
    return str(uuid.uuid4())[:8]


def _get_store():
    """Get PromptStore instance with project_root."""
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)
    return PromptStore(project_root)


@app.command()
def list():
    """List all prompts."""
    store = _get_store()
    prompts = store.list_prompts()
    rows = []
    for p in prompts:
        rows.append([p.id, p.name, ", ".join(p.tags), p.updated_at.strftime("%Y-%m-%d %H:%M")])
    print_table(["ID", "Name", "Tags", "Updated"], rows, title="Prompts")


@app.command()
def show(prompt_id: str):
    """Show prompt details."""
    store = _get_store()
    try:
        p = store.load_prompt(prompt_id)
    except FileNotFoundError:
        print_error(f"Prompt not found: {prompt_id}")
        raise typer.Exit(1)
    typer.echo(f"Name: {p.name}")
    typer.echo(f"Description: {p.description or '-'}")
    typer.echo(f"Tags: {', '.join(p.tags) if p.tags else '-'}")
    typer.echo(f"Template:\n{p.template}")


@app.command()
def create():
    """Create a new prompt interactively."""
    typer.echo("Creating a new prompt")
    name = typer.prompt("Name")
    description = typer.prompt("Description (optional)", default="")
    tags_str = typer.prompt("Tags (comma separated)", default="")
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    typer.echo("Enter template (use {variables} for formatting). End with EOF (Ctrl+D) or empty line.")
    typer.echo("--- begin template ---")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    typer.echo("--- end template ---")
    template = "\n".join(lines).strip()
    if not template:
        print_error("Template cannot be empty")
        raise typer.Exit(1)
    prompt_id = _generate_id()
    now = datetime.now()
    prompt = Prompt(
        id=prompt_id,
        name=name,
        description=description or None,
        template=template,
        tags=tags,
        created_at=now,
        updated_at=now,
    )
    store = _get_store()
    store.save_prompt(prompt)
    print_success(f"Created prompt {prompt_id}: {name}")


@app.command()
def update(prompt_id: str):
    """Update an existing prompt."""
    store = _get_store()
    try:
        p = store.load_prompt(prompt_id)
    except FileNotFoundError:
        print_error(f"Prompt not found: {prompt_id}")
        raise typer.Exit(1)
    typer.echo(f"Updating prompt: {p.name}")
    typer.echo("Leave blank to keep current value.")
    name = typer.prompt("Name", default=p.name)
    description = typer.prompt("Description", default=p.description or "")
    tags_str = typer.prompt("Tags (comma separated)", default=", ".join(p.tags))
    tags = [t.strip() for t in tags_str.split(",") if t.strip()]
    typer.echo("Enter new template (Ctrl+D to keep current).")
    typer.echo("--- begin template ---")
    lines = []
    try:
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    typer.echo("--- end template ---")
    template_input = "\n".join(lines).strip()
    new_template = template_input if template_input else p.template
    p.name = name
    p.description = description or None
    p.tags = tags
    p.template = new_template
    p.updated_at = datetime.now()
    store.save_prompt(p)
    print_success(f"Updated prompt {prompt_id}")


@app.command()
def delete(prompt_id: str):
    """Delete a prompt."""
    store = _get_store()
    try:
        store.load_prompt(prompt_id)
    except FileNotFoundError:
        print_error(f"Prompt not found: {prompt_id}")
        raise typer.Exit(1)
    confirm = typer.confirm(f"Delete prompt {prompt_id} and all its versions?")
    if confirm:
        store.delete_prompt(prompt_id)
        print_success(f"Deleted prompt {prompt_id}")
    else:
        typer.echo("Cancelled")


@app.command()
def render(prompt_id: str, vars_file: Optional[Path] = typer.Argument(None)):
    """Render prompt with variables from JSON file."""
    import json
    store = _get_store()
    try:
        p = store.load_prompt(prompt_id)
    except FileNotFoundError:
        print_error(f"Prompt not found: {prompt_id}")
        raise typer.Exit(1)
    vars_dict = {}
    if vars_file:
        with open(vars_file) as f:
            vars_dict = json.load(f)
    try:
        rendered = p.render(**vars_dict)
    except KeyError as e:
        print_error(f"Missing variable: {e}")
        raise typer.Exit(1)
    typer.echo(rendered)
