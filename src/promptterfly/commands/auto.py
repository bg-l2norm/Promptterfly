"""Auto-evolution commands."""
import typer
from pathlib import Path
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.core.config import load_config
from promptterfly.models.registry import get_model_by_name
from promptterfly.optimization.engine import optimize as engine_optimize
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_success, print_error

app = typer.Typer(help="Auto-evolution commands")


@app.command("optimize-all")
def auto_optimize_all(
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would be optimized without applying"),
    max_iterations: int = typer.Option(1, "--max-iter", help="Number of optimization iterations per prompt (overrides dataset few-shot only)"),
    dataset_path: Optional[Path] = typer.Option(None, "--dataset", help="Dataset file (JSONL). Default: .promptterfly/dataset.jsonl")
):
    """Optimize all prompts using the available dataset. Cost-effective: runs few-shot only."""
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

    # Determine dataset path
    if dataset_path is None:
        dataset_file = project_root / ".promptterfly" / "dataset.jsonl"
    else:
        dataset_file = dataset_path
    if not dataset_file.exists():
        print_error(f"Dataset not found: {dataset_file}. Generate with 'dataset generate'.")
        raise typer.Exit(1)

    # Pre-load model configuration per prompt or default each time
    results = []
    for p in prompts:
        # Per-prompt model override: check p.model_name (if set)
        model_name = p.model_name or load_config(project_root).default_model
        model_cfg = get_model_by_name(model_name, project_root)
        if not model_cfg:
            print_error(f"Model '{model_name}' for prompt {p.id} not configured. Skipping.")
            results.append((p.id, p.name, "skipped (model)"))
            continue

        typer.echo(f"Optimizing prompt {p.id}: {p.name} using {model_name}")
        if dry_run:
            results.append((p.id, p.name, "dry-run"))
            continue

        # Multiple iterations if requested (simple loop)
        current_prompt = p
        for i in range(max_iterations):
            try:
                new_prompt = engine_optimize(prompt_id=current_prompt.id, dataset_path=str(dataset_file))
                # Avoid duplicate work if unchanged
                if new_prompt.template == current_prompt.template:
                    typer.echo("  No change; stopping iterations.")
                    break
                store.save_prompt(new_prompt)
                current_prompt = new_prompt
            except Exception as e:
                print_error(f"  Error: {e}")
                break

        results.append((p.id, p.name, f"optimized ({i+1} iter)"))

    # Summary
    typer.echo("\nOptimization Summary:")
    for pid, name, status in results:
        typer.echo(f"  {pid}: {name} -> {status}")
    if not dry_run:
        print_success("Auto-optimize all completed.")


@app.command("bootstrap")
def bootstrap_iterations(
    dataset: Path = typer.Option(".promptterfly/dataset.jsonl", "--dataset"),
    max_iterations: int = typer.Option(3, "--max-iter", help="Max optimization iterations per prompt"),
    improvement_threshold: float = typer.Option(0.01, "--threshold", help="Min relative improvement (length ratio) to continue")
):
    """Iteratively optimize prompts until convergence or max iterations."""
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

    ds_path = project_root / dataset
    if not ds_path.exists():
        print_error(f"Dataset not found: {ds_path}")
        raise typer.Exit(1)

    for p in prompts:
        typer.echo(f"\n[{p.id}] {p.name}")
        current_template = p.template
        for i in range(1, max_iterations+1):
            typer.echo(f"  Iteration {i}...")
            try:
                new_prompt = engine_optimize(prompt_id=p.id, dataset_path=str(ds_path))
                new_template = new_prompt.template
                if new_template == current_template:
                    typer.echo("  No change; stopping.")
                    break
                # Crude improvement: length delta ratio
                improvement = abs(len(new_template) - len(current_template)) / max(len(current_template), 1)
                current_template = new_template
                store.save_prompt(new_prompt)
                if improvement < improvement_threshold:
                    typer.echo(f"  Improvement ({improvement:.3f}) below threshold; stopping.")
                    break
            except Exception as e:
                print_error(f"  Error: {e}")
                break
    print_success("Bootstrap iterations complete.")
