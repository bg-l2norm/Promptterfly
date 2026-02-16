"""Model management commands: list, add, remove, set-default."""
import typer
from typing import List, Optional
from promptterfly.core.models import ModelConfig
from promptterfly.models.registry import (
    load_models,
    add_model,
    remove_model,
    set_default,
    get_model_by_name,
)
from promptterfly.utils.tui import print_table, print_success, print_error
from pathlib import Path

app = typer.Typer(help="Manage LLM models in the registry")


@app.command("list")
def list_models():
    """List all configured models."""
    try:
        from promptterfly.utils.io import find_project_root
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)

    models = load_models(project_root)
    if not models:
        typer.echo("No models configured. Use 'promptterfly model add' to add one.")
        return

    rows = []
    for m in models:
        default_marker = "(default)" if m.name == get_default_model_name(project_root) else ""
        rows.append([
            m.name,
            m.provider,
            m.model,
            m.api_key_env or "-",
            f"{m.temperature:.2f}",
            str(m.max_tokens),
            default_marker
        ])
    print_table(
        ["Name", "Provider", "Model", "API Key Env", "Temp", "Max Tokens", ""],
        rows,
        title="Configured Models"
    )


def get_default_model_name(project_root: Path) -> str:
    """Get the default model name from config."""
    from promptterfly.core.config import load_config
    config = load_config(project_root)
    return config.default_model


@app.command("add")
def add_model_cmd(
    name: Optional[str] = typer.Argument(None, help="Model name (identifier)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Provider: openai, anthropic, etc."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model identifier (e.g. gpt-4, claude-3-opus)"),
    api_key_env: Optional[str] = typer.Option(None, "--api-key-env", help="Environment variable name for API key"),
    temperature: float = typer.Option(0.7, "--temperature", min=0.0, max=2.0),
    max_tokens: int = typer.Option(1024, "--max-tokens", min=1)
):
    """Add a new model to the registry."""
    # Interactive prompts for missing arguments
    if name is None:
        name = typer.prompt("Model name")
    if provider is None:
        provider = typer.prompt("Provider", default="openai")
    if model is None:
        model = typer.prompt("Model identifier", default="gpt-4")
    # api_key_env remains optional (can be None)
    try:
        from promptterfly.utils.io import find_project_root
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)

    config = ModelConfig(
        name=name,
        provider=provider,
        model=model,
        api_key_env=api_key_env,
        temperature=temperature,
        max_tokens=max_tokens
    )
    try:
        add_model(config, project_root)
        print_success(f"Added model '{name}'")
        typer.echo(f"Provider: {provider}")
        typer.echo(f"Model: {model}")
        typer.echo(f"Temperature: {temperature}")
        typer.echo(f"Max tokens: {max_tokens}")
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)


@app.command("remove")
def remove_model_cmd(name: str = typer.Argument(..., help="Model name to remove")):
    """Remove a model from the registry."""
    try:
        from promptterfly.utils.io import find_project_root
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)

    # Check if it's the default model
    default_name = get_default_model_name(project_root)
    if name == default_name:
        print_error(f"Cannot remove default model '{name}'. Change default first with 'model set-default'.")
        raise typer.Exit(1)

    removed = remove_model(name, project_root)
    if removed:
        print_success(f"Removed model '{name}'")
    else:
        print_error(f"Model '{name}' not found")
        raise typer.Exit(1)


@app.command("set-default")
def set_default_cmd(name: str = typer.Argument(..., help="Model name to set as default")):
    """Set the default model for the project."""
    try:
        from promptterfly.utils.io import find_project_root
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)

    # Verify model exists
    model = get_model_by_name(name, project_root)
    if model is None:
        print_error(f"Model '{name}' not found in registry")
        raise typer.Exit(1)

    try:
        set_default(name, project_root)
        print_success(f"Default model set to '{name}'")
    except ValueError as e:
        print_error(str(e))
        raise typer.Exit(1)
