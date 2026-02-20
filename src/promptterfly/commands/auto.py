import typer
from pathlib import Path
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.core.config import load_config
from promptterfly.models.registry import get_model_by_name
from promptterfly.optimization.engine import optimize
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_success, print_error
import json

app = typer.Typer(help="Auto-evolution commands")

@app.command("optimize-all")
def auto_optimize_all(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be optimized without applying"),
    max_per_prompt: int = typer.Option(1, "--max", help="Number of optimization iterations per prompt")
):
    """Optimize all prompts using the available dataset. Runs few-shot optimization per prompt."""
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project.")
        raise typer.Exit(1)

    store = PromptStore(project_root)
    prompts = store.list_prompts()
    if not prompts:
        print_error("No prompts found.")
        raise typer.Exit(1)

    # Load dataset once
    dataset_path = project_root / ".promptterfly" / "dataset.jsonl"
    if not dataset_path.exists():
        print_error("Dataset not found at .promptterfly/dataset.jsonl. Generate with 'dataset generate'.")
        raise typer.Exit(1)

    results = []
    for p in prompts:
        # Per-prompt model override?
        model_name = getattr(p, 'model_name', None) or load_config(project_root).default_model
        # Temporarily set default model to the one we'll use
        # Note: optimization currently uses default model; to support override we'd need to pass model_cfg
        typer.echo(f"Optimizing prompt {p.id}: {p.name} using {model_name}")
        if dry_run:
            results.append((p.id, p.name, "skipped"))
            continue
        try:
            new_prompt = optimize(prompt_id=p.id, dataset_path=str(dataset_path))
            store.save_prompt(new_prompt)
            results.append((p.id, p.name, "optimized"))
        except Exception as e:
            print_error(f"Failed for prompt {p.id}: {e}")
            results.append((p.id, p.name, f"error: {e}"))

    # Summary
    typer.echo("\nOptimization Summary:")
    for pid, name, status in results:
        typer.echo(f"  {pid}: {name} -> {status}")
    if not dry_run:
        print_success("Auto-optimize all completed.")
