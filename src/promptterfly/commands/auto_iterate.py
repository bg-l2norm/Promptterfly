import typer
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.core.config import load_config
from promptterfly.optimization.engine import optimize
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_success, print_error
from pathlib import Path

app = typer.Typer(help="Iterative auto-evolution")

@app.command("bootstrap")
def bootstrap_iterations(
    dataset: Path = typer.Option(".promptterfly/dataset.jsonl", "--dataset"),
    max_iterations: int = typer.Option(3, "--max-iter", help="Max optimization iterations per prompt"),
    improvement_threshold: float = typer.Option(0.01, "--threshold", help="Min relative improvement to continue")
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

    for p in prompts:
        typer.echo(f"\\n[{p.id}] {p.name}")
        current = template = p.template
        for i in range(1, max_iterations+1):
            typer.echo(f"  Iteration {i}...")
            try:
                new_prompt = optimize(prompt_id=p.id, dataset_path=str(dataset))
                new = new_prompt.template
                # Simple similarity: if identical, stop
                if new == current:
                    typer.echo("  No change; stopping.")
                    break
                # Compute length ratio as crude metric
                improvement = abs(len(new) - len(current)) / max(len(current),1)
                current = new
                store.save_prompt(new_prompt)
                if improvement < improvement_threshold:
                    typer.echo(f"  Improvement ({improvement:.3f}) below threshold; stopping.")
                    break
            except Exception as e:
                print_error(f"  Error: {e}")
                break
    print_success("Bootstrap iterations complete.")
