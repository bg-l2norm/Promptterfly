"""Version commands: history, restore."""
import typer
from typing import Optional
from datetime import datetime
from promptterfly.storage.version_store import VersionStore
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_table, print_success, print_error, print_warning

app = typer.Typer(help="Manage prompt version history")


def _format_datetime(dt: datetime) -> str:
    """Format datetime for display."""
    return dt.strftime("%Y-%m-%d %H:%M:%S")


@app.command("history")
def history(prompt_id: str):
    """List version history for a prompt."""
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("No .promptterfly directory found. Are you in a project?")
        raise typer.Exit(1)

    ps = PromptStore(project_root)
    vs = VersionStore(project_root)

    # Check if prompt exists (file or versions)
    prompt_path = ps.get_prompt_path(prompt_id)
    versions_dir = ps.get_versions_dir(prompt_id)
    if not prompt_path.exists() and not versions_dir.exists():
        print_error(f"Prompt not found: {prompt_id}")
        raise typer.Exit(1)

    versions = vs.list_versions(prompt_id)
    if not versions:
        print_warning(f"Prompt '{prompt_id}' exists but has no version history yet.")
        return

    rows = []
    for v in versions:
        created_str = _format_datetime(v.created_at) if v.created_at else "-"
        message = v.message or ""
        rows.append([v.version, created_str, message])

    print_table(["Version", "Created", "Message"], rows, title=f"Version History: {prompt_id}")


@app.command("restore")
def restore(prompt_id: str, version: int):
    """Restore a prompt to a specific version."""
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("No .promptterfly directory found. Are you in a project?")
        raise typer.Exit(1)

    store = VersionStore(project_root)

    # Check if the version exists
    version_details = store.get_version_details(prompt_id, version)
    if version_details is None:
        # Check if prompt exists at all to give better error
        ps = PromptStore(project_root)
        prompt_path = ps.get_prompt_path(prompt_id)
        versions_dir = ps.get_versions_dir(prompt_id)
        if not prompt_path.exists() and not versions_dir.exists():
            print_error(f"Prompt not found: {prompt_id}")
        else:
            print_error(f"Version {version} not found for prompt: {prompt_id}")
        raise typer.Exit(1)

    # Show version info and confirm
    typer.echo(f"Prompt: {prompt_id}")
    typer.echo(f"Version: {version}")
    typer.echo(f"Created: {_format_datetime(version_details.created_at)}")
    typer.echo(f"Message: {version_details.message or '(no message)'}")
    typer.echo()
    confirm = typer.confirm(f"Restore to this version? This will replace the current prompt.")
    if not confirm:
        typer.echo("Cancelled.")
        raise typer.Exit(0)

    try:
        restored_prompt = store.restore_version(prompt_id, version)
        print_success(f"Restored prompt {prompt_id} to version {version}")
        typer.echo(f"Current name: {restored_prompt.name}")
        typer.echo(f"Updated at: {_format_datetime(restored_prompt.updated_at)}")
    except FileNotFoundError as e:
        print_error(str(e))
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Failed to restore: {e}")
        raise typer.Exit(1)
