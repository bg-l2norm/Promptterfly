"""Optimization commands."""
import typer
from pathlib import Path
from typing import Optional

from promptterfly.storage.prompt_store import PromptStore
from promptterfly.storage.version_store import VersionStore
from promptterfly.optimization.engine import optimize as engine_optimize
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_success, print_error

app = typer.Typer(help="Optimize prompts")


@app.command("improve")
def improve(
    prompt_id: str,
    strategy: str = typer.Option("few_shot", "--strategy", help="Optimization strategy (default: few_shot)"),
    dataset: Optional[Path] = typer.Option(None, "--dataset", help="Path to dataset JSONL file")
):
    """Improve a prompt using the specified optimization strategy.

    Creates a version snapshot of the current prompt before optimization,
    then saves the optimized prompt as the new current version.
    """
    # Find project root
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)

    store = PromptStore(project_root)
    vs = VersionStore(project_root)

    # Verify prompt exists
    try:
        store.load_prompt(prompt_id)
    except FileNotFoundError:
        print_error(f"Prompt '{prompt_id}' not found.")
        raise typer.Exit(1)

    # Create snapshot of current prompt before optimization (auto-version)
    try:
        store.create_snapshot(prompt_id, message=f"Before optimization: strategy={strategy}")
    except Exception as e:
        print_error(f"Failed to create version snapshot: {e}")
        raise typer.Exit(1)

    # Determine the version number we just created
    versions = vs.list_versions(prompt_id)
    version_num = versions[-1].version if versions else None

    # Run optimization
    try:
        new_prompt = engine_optimize(
            prompt_id=prompt_id,
            strategy=strategy,
            dataset_path=str(dataset) if dataset else None
        )
    except Exception as e:
        print_error(f"Optimization failed: {e}")
        raise typer.Exit(1)

    # Save the optimized prompt
    try:
        store.save_prompt(new_prompt)
    except Exception as e:
        print_error(f"Failed to save optimized prompt: {e}")
        raise typer.Exit(1)

    # Output success
    if version_num is not None:
        print_success(f"Optimization complete. New version: v{version_num}")
    else:
        print_success("Optimization complete.")
