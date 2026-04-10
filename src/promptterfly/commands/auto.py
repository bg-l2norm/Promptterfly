"""Auto-evolution commands."""
import typer
import os
import json
from pathlib import Path
from typing import Optional
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.core.config import load_config
from promptterfly.models.registry import get_model_by_name
from promptterfly.optimization.engine import optimize as engine_optimize
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_success, print_error
import litellm
from datetime import datetime
from promptterfly.core.models import Prompt

app = typer.Typer(help="Auto-evolution commands")

@app.command("generate")
def auto_generate(
    description: str = typer.Argument(..., help="Description of what you want the prompt to do"),
    iterations: int = typer.Option(3, "--iterations", "-i", help="Number of variations to test")
):
    """Automatically generate and evaluate a prompt template from a description."""
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)

    cfg = load_config(project_root)
    model_cfg = get_model_by_name(cfg.default_model, project_root)
    if not model_cfg:
        print_error(f"Default model '{cfg.default_model}' not found.")
        raise typer.Exit(1)

    if model_cfg.api_key_env:
        api_key = os.getenv(model_cfg.api_key_env)
        if not api_key:
            print_error(f"API key env '{model_cfg.api_key_env}' is not set.")
            raise typer.Exit(1)

    model_str = model_cfg.model
    if model_cfg.provider == "openai":
        model_str = f"openai/{model_cfg.model}"
    elif model_cfg.provider == "anthropic":
        model_str = f"anthropic/{model_cfg.model}"

    typer.echo(f"Sub-agent is thinking about: '{description}'...")

    try:
        # Generate variations
        sys_prompt = "You are an expert prompt engineer. The user will provide a goal. You will write a prompt template that accomplishes this goal. The template should use Python {variable} syntax for inputs. Output ONLY the raw template, no markdown formatting or intro text."

        variations = []
        for i in range(iterations):
            resp = litellm.completion(
                model=model_str,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": description}
                ],
                temperature=0.8 + (i * 0.1), # increase temp for variance
                max_tokens=500
            )
            variations.append(resp.choices[0].message.content.strip())


        typer.echo(f"Generated {iterations} variations. Evaluating them...")

        # Evaluate variations
        eval_prompt = "You are evaluating prompt templates. I will give you a prompt template. Score its quality for the following goal from 1 to 100 based on clarity, structure, and effectiveness. ONLY output the integer score.\n\nGoal: {goal}\n\nTemplate: {template}"

        best_score = -1
        best_template = variations[0]

        for template in variations:
            try:
                resp = litellm.completion(
                    model=model_str,
                    messages=[
                        {"role": "user", "content": eval_prompt.format(goal=description, template=template)}
                    ],
                    temperature=0.0,
                    max_tokens=10
                )
                score_str = resp.choices[0].message.content.strip()
                digits = ''.join(filter(str.isdigit, score_str))
                score = int(digits) if digits else 0
                if score > best_score:
                    best_score = score
                    best_template = template
            except Exception:
                # Fallback score if it fails
                pass

        typer.echo(f"Best prompt found (Score: {best_score}/100):\n{best_template}")

        # Generate name
        resp = litellm.completion(
            model=model_str,
            messages=[{"role": "user", "content": f"Generate a short (2-4 words) descriptive title for this prompt template. Output ONLY the title, no quotes, no extra text.\n\nTemplate:\n{best_template}"}],
            temperature=0.7,
            max_tokens=10
        )
        name = resp.choices[0].message.content.strip().replace('"', '')
        if not name:
            name = "Auto_Generated_Prompt"

        store = PromptStore(project_root)
        prompt_id = store._next_id()
        now = datetime.now()

        prompt = Prompt(
            id=prompt_id,
            name=name,
            description=f"Auto-generated for: {description}",
            template=best_template,
            tags=["auto-generated"],
            created_at=now,
            updated_at=now,
        )
        store.save_prompt(prompt)

        print_success(f"Saved optimized prompt '{name}' as ID {prompt_id}")

    except Exception as e:
        print_error(f"Auto-generation failed: {e}")
        raise typer.Exit(1)


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
