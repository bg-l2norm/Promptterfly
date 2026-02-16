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

# Default provider-model mapping for interactive selection when litellm is unavailable
DEFAULT_PROVIDER_MODELS = {
    # Major providers
    "openai": [
        "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo",
        "text-davinci-003", "davinci", "curie", "babbage", "ada"
    ],
    "anthropic": [
        "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307",
        "claude-2.1", "claude-2.0", "claude-instant-1.2"
    ],
    "google": [
        "gemini-1.5-pro-latest", "gemini-1.5-flash-latest", "gemini-pro", "gemini-pro-vision"
    ],
    "mistral": [
        "mistral-large-latest", "mistral-medium", "mistral-small", "mistral-7b-instruct"
    ],
    "cohere": [
        "command-r-plus", "command-r", "command", "command-light", "command-medium"
    ],
    "groq": [
        "llama3-70b-8192", "llama3-8b-8192", "mixtral-8x7b-32768", "gemma2-9b-it"
    ],
    "grok": [
        "grok-x-latest", "grok-beta"
    ],
    "openrouter": [
        "openrouter/quasar-alpha", "openrouter/anthracite-02b", "openrouter/phi-3-medium-128k"
    ],
    "together": [
        "togethercomputer/llama-2-70b-chat", "togethercomputer/llama-2-13b-chat"
    ],
    "anyscale": [
        "anyscale/meta-llama/Llama-2-7b-chat-hf", "anyscale/meta-llama/Llama-2-13b-chat-hf"
    ],
    # Local/community
    "ollama": [
        "ollama/llama2", "ollama/mistral", "ollama/codellama"
    ],
    "local": [
        "local/llama3", "local/mistral", "local/codellama"
    ],
}


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


def interactive_provider_selection() -> str:
    """Interactively select a provider from available options."""
    # Use a curated list of well-known providers; ignore litellm's raw list
    providers = sorted(DEFAULT_PROVIDER_MODELS.keys())
    if not providers:
        providers = ["openai"]  # fallback

    # Build case-insensitive mapping for provider names (full set)
    provider_map = {p.lower(): p for p in providers}

    # Truncate display to first 10 providers
    display_providers = providers[:10]
    console.print("[bold]Available providers:[/bold]")
    for i, p in enumerate(display_providers, 1):
        console.print(f"  {i}) {p}")
    if len(providers) > 10:
        console.print(f"  ... and {len(providers)-10} more. You can also type any provider name.")

    while True:
        choice = typer.prompt("Select provider by number or type name")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(display_providers):
                return display_providers[idx]
            else:
                console.print(f"[yellow]Invalid number. Please enter a number between 1 and {len(display_providers)}.[/yellow]")
        except ValueError:
            lc = choice.lower()
            if lc in provider_map:
                return provider_map[lc]
            else:
                console.print(f"[yellow]Invalid provider '{choice}'. Please select a valid provider from the list.[/yellow]")


def interactive_model_selection(provider: str) -> str:
    """Interactively select a model from the given provider's offerings."""
    models = []
    # Prefer DEFAULT_PROVIDER_MODELS for well-known models
    if provider in DEFAULT_PROVIDER_MODELS:
        models = DEFAULT_PROVIDER_MODELS[provider]
    # Optionally, could supplement with litellm if needed, but default is cleanest.
    if not models:
        return typer.prompt("Enter model identifier")
    models = sorted(set(models))
    max_show = 10
    console.print(f"[bold]Available models for {provider}:[/bold]")
    for i, m in enumerate(models[:max_show], 1):
        console.print(f"  {i}) {m}")
    if len(models) > max_show:
        console.print(f"  ... and {len(models)-max_show} more. You can also type the full model name.")
    while True:
        choice = typer.prompt("Select model by number or type full model name")
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(models[:max_show]):
                return models[idx]
            else:
                console.print(f"[yellow]Invalid number. Please enter a number between 1 and {len(models[:max_show])}.[/yellow]")
        except ValueError:
            # Non-numeric input is treated as a custom model identifier
            return choice


def ensure_dotenv_gitignore(project_root: Path):
    """Make sure .env is listed in .gitignore."""
    gitignore_path = project_root / ".gitignore"
    entry = ".env"
    if gitignore_path.exists():
        lines = [line.strip() for line in gitignore_path.read_text(encoding="utf-8").splitlines()]
        if entry not in lines:
            with open(gitignore_path, "a", encoding="utf-8") as f:
                f.write(f"\n{entry}\n")
            console.print("[dim]Added .env to .gitignore[/dim]")
    else:
        with open(gitignore_path, "w", encoding="utf-8") as f:
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

    final_provider = provider
    final_model = model

    # Resolve provider
    if final_provider is None:
        if final_model is not None:
            inferred = infer_provider(final_model)
            if inferred:
                final_provider = inferred
            else:
                final_provider = interactive_provider_selection()
        else:
            final_provider = interactive_provider_selection()

    # Safety fallback
    if not final_provider:
        final_provider = "openai"

    # Resolve model if missing
    if final_model is None:
        final_model = interactive_model_selection(final_provider)

    # Normalize model identifier: strip provider prefix if present
    if "/" in final_model:
        parts = final_model.split("/", 1)
        prefix, model_clean = parts
        if prefix != final_provider:
            console.print(f"[yellow]Warning: model prefix '{prefix}' differs from selected provider '{final_provider}'. Using '{model_clean}' as model name.[/yellow]")
        final_model = model_clean

    # Echo provider if inferred or selected (i.e., when provider arg was not given)
    if provider is None:
        console.print(f"[dim]Using provider: {final_provider}[/dim]")

    # Determine name
    final_name = name
    if final_name is None:
        suggested = f"{final_provider}-{final_model}".replace("/", "-")
        final_name = typer.prompt("Model config name", default=suggested)

    # Determine api_key_env
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
        if dotenv_path.exists():
            existing = dotenv_path.read_text(encoding="utf-8")
            lines = existing.splitlines()
            # Check if any line starts with the env var name (ignoring leading whitespace)
            if any(line.strip().startswith(f"{final_api_key_env}=") for line in lines):
                console.print(f"[yellow]{final_api_key_env} already exists in .env. Skipping.[/yellow]")
            else:
                with open(dotenv_path, "a", encoding="utf-8") as f:
                    f.write(f"\n{final_api_key_env}={key}\n")
                console.print(f"✅ API key saved to {dotenv_path}")
        else:
            with open(dotenv_path, "w", encoding="utf-8") as f:
                f.write(f"{final_api_key_env}={key}\n")
            console.print(f"✅ Created .env with API key at {dotenv_path}")

    config = ModelConfig(
        name=final_name,
        provider=final_provider,
        model=final_model,
        api_key_env=final_api_key_env,
        temperature=temperature,
        max_tokens=max_tokens
    )
    try:
        add_model(config, project_root)
        print_success(f"Added model '{final_name}'")
        typer.echo(f"Provider: {final_provider}")
        typer.echo(f"Model: {final_model}")
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
