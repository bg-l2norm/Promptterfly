"""Prompt management commands."""
import typer
import re
from typing import Optional
from pathlib import Path
from promptterfly.core.models import Prompt
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_table, print_success, print_error
from datetime import datetime

app = typer.Typer(help="Manage prompts")


# Removed random ID generation; now using sequential integers via store._next_id()

def _tokenize(s: str) -> set:
    """Extract lowercase alphanumeric words from a string."""
    return set(re.findall(r'\b\w+\b', s.lower()))

def _score_prompt(query: str, prompt: Prompt) -> float:
    """
    Compute a weighted match score between query and a prompt.
    - Exact name match: 1.0
    - Name tokens: 0.6 * (overlap fraction)
    - Description tokens: 0.3 * (overlap fraction)
    - Template tokens (≥2 matches): 0.05 * (overlap fraction) * 2^(count-1)
    Scores are capped at 1.0.
    """
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 0.0
    len_q = len(q_tokens)

    # Exact name match (case-insensitive, stripped)
    if prompt.name.strip().lower() == query.strip().lower():
        return 1.0

    # Name score
    name_tokens = _tokenize(prompt.name)
    name_match = len(q_tokens & name_tokens)
    score_name = (name_match / len_q) * 0.6

    # Description score
    desc_tokens = _tokenize(prompt.description or "")
    desc_match = len(q_tokens & desc_tokens)
    score_desc = (desc_match / len_q) * 0.3

    # Template score: only if at least 2 matching words
    template_tokens = _tokenize(prompt.template)
    temp_match = len(q_tokens & template_tokens)
    score_temp = 0.0
    if temp_match >= 2:
        base = (temp_match / len_q) * 0.05
        exponential = 2 ** (temp_match - 1)
        score_temp = base * exponential

    total = score_name + score_desc + score_temp
    return min(total, 1.0)


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
        tags_str = ", ".join(p.tags) if p.tags else "-"
        rows.append([p.id, p.name, tags_str, p.updated_at.strftime("%Y-%m-%d %H:%M")])
    print_table(["ID", "Name", "Tags", "Updated"], rows, title="Prompts")


@app.command()
def show(prompt_id: int):
    """Show prompt details."""
    store = _get_store()
    try:
        p = store.load_prompt(prompt_id)
    except FileNotFoundError:
        print_error(f"Prompt not found: {prompt_id}")
        raise typer.Exit(1)
    typer.echo(f"Name: {p.name}")
    typer.echo(f"Description: {p.description or '-'}")
    typer.echo(f"Template:\n{p.template}")


@app.command()
def create():
    """Create a new prompt interactively."""
    # Check project exists before starting prompts
    try:
        find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)
    
    typer.echo("Creating a new prompt")
    name = typer.prompt("Name")
    description = typer.prompt("Description (Optional)", default="")
    tags_input = typer.prompt("Tags (comma-separated, optional)", default="")
    tags = [t.strip() for t in tags_input.split(",") if t.strip()]
    store = _get_store()
    # Ensure unique name (auto-append _N if duplicate)
    existing_names = {p.name for p in store.list_prompts()}
    base_name = name
    counter = 1
    while name in existing_names:
        counter += 1
        name = f"{base_name}_{counter}"
    if counter > 1:
        typer.echo(f"Name already exists, using '{name}' instead.")
    typer.echo("\nEnter template (use {variables} for formatting).")
    typer.echo("Variables are supplied at render time via a JSON file.")
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
    prompt_id = store._next_id()
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
    # Save the prompt first
    store.save_prompt(prompt)

    # Auto-versioning: create a snapshot after creation (baseline) if enabled
    try:
        from promptterfly.core.config import load_config
        cfg = load_config(store.project_root)
        auto_version = cfg.auto_version
    except Exception:
        auto_version = True
    if auto_version:
        try:
            store.create_snapshot(prompt_id, message="Initial version (auto)")
        except Exception as e:
            # Don't fail creation if versioning fails
            typer.echo(f"[dim]Note: failed to create auto-version: {e}[/dim]")
    print_success(f"Created prompt {prompt_id}: {name}")
    # Auto-list to show the new prompt
    list()


@app.command()
def update(prompt_id: int):
    """Update an existing prompt."""
    store = _get_store()
    try:
        p = store.load_prompt(prompt_id)
    except FileNotFoundError:
        print_error(f"Prompt not found: {prompt_id}")
        raise typer.Exit(1)

    # Auto-versioning: snapshot current state before update, if enabled
    try:
        from promptterfly.core.config import load_config
        cfg = load_config(store.project_root)
        auto_version = getattr(cfg, 'auto_version', True)
    except Exception:
        auto_version = True
    if auto_version:
        try:
            store.create_snapshot(prompt_id, message="Before update")
        except Exception as e:
            # Don't block update if versioning fails
            typer.echo(f"[dim]Warning: failed to create version snapshot: {e}[/dim]")

    typer.echo(f"Updating prompt: {p.name}")
    typer.echo("Leave blank to keep current value.")
    name = typer.prompt("Name", default=p.name)
    description = typer.prompt("Description (Optional)", default=p.description or "")
    tags_input = typer.prompt("Tags (comma-separated)", default=", ".join(p.tags) if p.tags else "")
    tags = [t.strip() for t in tags_input.split(",") if t.strip()] if tags_input else p.tags
    # Ensure name uniqueness (exclude current prompt)
    existing_names = {other.name for other in store.list_prompts() if other.id != p.id}
    base_name = name
    counter = 1
    while name in existing_names:
        counter += 1
        name = f"{base_name}_{counter}"
    if counter > 1:
        typer.echo(f"Name conflicts with existing prompt, using '{name}' instead.")
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
def delete(prompt_id: int):
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
def render(prompt_id: int, vars_file: Optional[Path] = typer.Argument(None)):
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


@app.command()
def find(query: str):
    """
    Fuzzy search prompts by name, description, and template.
    Scoring:
      - Exact name match: 1.0 (auto-select)
      - Name token overlap: high weight
      - Description token overlap: medium weight
      - Template token matches (≥2 words): low base * exponential
    If the best score ≥ 0.8, it is shown immediately.
    Otherwise, the top 3 candidates are presented for selection.
    """
    store = _get_store()
    prompts = store.list_prompts()
    if not prompts:
        print_error("No prompts found.")
        raise typer.Exit(1)

    # Score each prompt
    scored = []
    for p in prompts:
        score = _score_prompt(query, p)
        scored.append((score, p))

    # Sort descending by score
    scored.sort(key=lambda x: x[0], reverse=True)
    top_score, top_prompt = scored[0]

    # If confident enough, auto-select and show details
    if top_score >= 0.8:
        typer.echo(f"Best match: Prompt {top_prompt.id} - {top_prompt.name} (score: {top_score:.0%})")
        typer.echo(f"Description: {top_prompt.description or '-'}")
        typer.echo(f"Template:\n{top_prompt.template}")
        return

    # Otherwise show top 3 for user to pick
    typer.echo(f"Top matches (best score: {top_score:.0%}):")
    rows = []
    for i, (score, p) in enumerate(scored[:3], start=1):
        preview = p.description or p.template[:40]
        if len(p.template) > 40:
            preview = preview if p.description else p.template[:40] + "..."
        rows.append([i, p.id, p.name, f"{score:.0%}", preview])
    print_table(["#", "ID", "Name", "Score", "Preview"], rows, title="Results")
    typer.echo("Enter the number (1-3) of the prompt to view, or press Enter to cancel.")
    choice = typer.prompt("", default="")
    if not choice:
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= min(3, len(scored)):
            raise ValueError()
    except ValueError:
        print_error("Invalid choice.")
        raise typer.Exit(1)
    _, selected_prompt = scored[idx]
    typer.echo(f"\nName: {selected_prompt.name}")
    typer.echo(f"Description: {selected_prompt.description or '-'}")
    typer.echo(f"Template:\n{selected_prompt.template}")
