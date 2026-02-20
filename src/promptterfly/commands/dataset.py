"""Dataset management commands."""
import typer
import os
import json
from pathlib import Path
from typing import Optional
from promptterfly.utils.io import find_project_root
from promptterfly.utils.tui import print_success, print_error
from promptterfly.core.config import load_config
from promptterfly.models.registry import get_model_by_name

app = typer.Typer(help="Dataset management for optimization")


@app.command("generate")
def generate(
    count: int = typer.Option(10, "--count", "-n", help="Number of examples to generate"),
    prompt_id: Optional[int] = typer.Option(None, "--prompt-id", help="Prompt ID to base generation on (uses template as instruction)"),
    output: Path = typer.Option(".promptterfly/dataset.jsonl", "--output", help="Output dataset path (appended)"),
    model_name: Optional[str] = typer.Option(None, "--model", help="Override default model for generation")
):
    """Generate synthetic few-shot examples using the configured LLM."""
    try:
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project.")
        raise typer.Exit(1)

    cfg = load_config(project_root)
    # Resolve model to use
    if model_name:
        resolved_model = model_name
    else:
        resolved_model = cfg.default_model
    model_cfg = get_model_by_name(resolved_model, project_root)
    if not model_cfg:
        print_error(f"Model '{resolved_model}' not configured.")
        raise typer.Exit(1)

    # Get prompt template if prompt_id is given
    template = "You are a helpful assistant."
    if prompt_id is not None:
        from promptterfly.storage.prompt_store import PromptStore
        store = PromptStore(project_root)
        try:
            p = store.load_prompt(prompt_id)
            template = p.template
        except FileNotFoundError:
            print_error(f"Prompt {prompt_id} not found.")
            raise typer.Exit(1)

    # Build generation meta-prompt
    gen_prompt = f"""Given the following instruction/template, generate {count} diverse input-output pairs that would be useful for fine-tuning.

Instruction: {template}

For each example, output a JSON object with keys 'input' (the user query) and 'completion' (the ideal assistant response). Output one JSON per line, no extra text."""

    # Set up environment for API key if needed
    if model_cfg.api_key_env:
        api_key = os.getenv(model_cfg.api_key_env)
        if not api_key:
            print_error(f"API key environment variable {model_cfg.api_key_env} not set.")
            raise typer.Exit(1)

    # Prepare litellm model string
    if model_cfg.provider == "openai":
        model_str = f"openai/{model_cfg.model}"
    elif model_cfg.provider == "anthropic":
        model_str = f"anthropic/{model_cfg.model}"
    else:
        model_str = model_cfg.model

    try:
        import litellm
        responses = litellm.completion(
            model=model_str,
            messages=[{"role": "user", "content": gen_prompt}],
            temperature=0.8,
            max_tokens=1024,
            n=1,
        )
        text = responses.choices[0].message.content.strip()
    except Exception as e:
        print_error(f"LLM call failed: {e}")
        raise typer.Exit(1)

    # Parse JSON lines
    examples = []
    for line in text.splitlines():
        try:
            obj = json.loads(line)
            if "input" in obj and "completion" in obj:
                examples.append(obj)
        except json.JSONDecodeError:
            continue

    if not examples:
        print_error("No valid examples generated.")
        raise typer.Exit(1)

    # Append to dataset file
    output_path = project_root / output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    existing = 0
    if output_path.exists():
        existing = sum(1 for _ in open(output_path))
    with open(output_path, "a") as f:
        for ex in examples[:count]:
            f.write(json.dumps(ex) + "\n")

    print_success(f"Generated {len(examples[:count])} examples → {output} (total now ~{existing + len(examples[:count])})")
