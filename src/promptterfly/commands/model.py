"""Model management commands: list, add, remove, set-default."""
import typer
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.prompt import Prompt, Confirm
from promptterfly.core.models import ModelConfig
from promptterfly.models.registry import (
    load_models,
    add_model,
    remove_model,
    set_default,
    get_model_by_name,
)
from promptterfly.utils.tui import print_table, print_success, print_error

console = Console()


def infer_provider(model_str: str) -> Optional[str]:
    """Infer the provider from a model identifier."""
    model_str = model_str.strip().lower()
    # If it contains a slash, treat the part before slash as provider
    if "/" in model_str:
        provider = model_str.split("/", 1)[0]
        # Return provider and also clean model? We'll handle in calling code.
        return provider
    if "gpt" in model_str or "chatgpt" in model_str or model_str.startswith("text-"):
        return "openai"
    if "claude" in model_str:
        return "anthropic"
    if "gemini" in model_str:
        return "google"
    if "mistral" in model_str:
        return "mistral"
    if "command" in model_str:
        return "cohere"
    # Add more as needed
    return None


def ensure_dotenv_gitignore(project_root: Path):
    """Make sure .env is listed in .gitignore."""
    gitignore_path = project_root / ".gitignore"
    entry = ".env"
    if gitignore_path.exists():
        lines = gitignore_path.read_text().splitlines()
        if entry not in lines:
            with open(gitignore_path, "a") as f:
                f.write(f"\n{entry}\n")
            console.print("[dim]Added .env to .gitignore[/dim]")
    else:
        with open(gitignore_path, "w") as f:
            f.write(f"{entry}\n")
        console.print("[dim]Created .gitignore with .env[/dim]")


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
    name: Optional[str] = typer.Argument(None, help="Model name (for your reference)"),
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="Provider: openai, anthropic, etc."),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Model identifier (e.g. gpt-4, anthropic/claude-3-opus)"),
    api_key_env: Optional[str] = typer.Option(None, "--api-key-env", help="Environment variable name for API key"),
    temperature: float = typer.Option(0.7, "--temperature", min=0.0, max=2.0),
    max_tokens: int = typer.Option(1024, "--max-tokens", min=1)
):
    """Add a new model to the registry."""
    try:
        from promptterfly.utils.io import find_project_root
        project_root = find_project_root()
    except FileNotFoundError:
        print_error("Not in a Promptterfly project. Run 'promptterfly init' first.")
        raise typer.Exit(1)

    # Interactive prompts for missing arguments
    if name is None:
        name = typer.prompt("Model name (for your reference)")

    if model is None:
        model = typer.prompt("Model identifier (e.g., gpt-4, anthropic/claude-3-opus)")

    # If provider not provided, try to infer from model
    final_provider = provider
    if final_provider is None:
        inferred = infer_provider(model)
        if inferred:
            final_provider = inferred
            # If model includes provider prefix, strip it
            if "/" in model:
                model = model.split("/", 1)[1]
                console.print(f"[dim]Inferred provider: {final_provider}; model normalized to '{model}'[/dim]")
            else:
                console.print(f"[dim]Inferred provider: {final_provider}[/dim]")
        else:
            final_provider = typer.prompt("Provider", default="openai")
    else:
        # Provider provided; still check for slash and normalize
        if "/" in model:
            parts = model.split("/", 1)
            if parts[0] != final_provider:
                console.print(f"[yellow]Warning: model prefix '{parts[0]}' differs from specified provider '{final_provider}'. Using specified provider and stripping prefix.[/yellow]")
            model = parts[1]

    # Determine api_key_env if not given
    final_api_key_env = api_key_env
    if final_api_key_env is None:
        default_env = f"{final_provider.upper()}_API_KEY"
        final_api_key_env = typer.prompt("API key environment variable name", default=default_env)

    # Offer to set the API key now
    set_now = typer.confirm("Set your API key now? (Recommended)", default=True)
    if set_now:
        key = typer.prompt(f"{final_provider} API key", hide_input=True)
        dotenv_path = project_root / ".env"
        ensure_dotenv_gitignore(project_root)
        # Avoid duplicate entries
        if dotenv_path.exists():
            existing = dotenv_path.read_text()
            if f"{final_api_key_env}=" in existing:
                console.print(f"[yellow]{final_api_key_env} already exists in .env. Skipping.[/yellow]")
            else:
                with open(dotenv_path, "a") as f:
                    f.write(f"\n{final_api_key_env}={key}\n")
                console.print(f"✅ API key saved to {dotenv_path}")
        else:
            with open(dotenv_path, "w") as f:
                f.write(f"{final_api_key_env}={key}\n")
            console.print(f"✅ Created .env with API key at {dotenv_path}")

    config = ModelConfig(
        name=name,
        provider=final_provider,
        model=model,
        api_key_env=final_api_key_env,
        temperature=temperature,
        max_tokens=max_tokens
    )
    try:
        add_model(config, project_root)
        print_success(f"Added model '{name}'")
        typer.echo(f"Provider: {final_provider}")
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
