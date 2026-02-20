"""Promptterfly CLI entry point."""
import typer
from typing import Optional
from pathlib import Path
from rich.console import Console

app = typer.Typer(help="Promptterfly: Local prompt manager with versioning & optimization")

# Import shared helpers from model commands to avoid duplication
from promptterfly.commands.model import interactive_provider_selection, interactive_model_selection

console = Console()


@app.command()
def init(
    path: Path = typer.Option(Path.cwd(), "--path", help="Project directory")
):
    """Initialize Promptterfly in the current or specified directory."""
    from promptterfly.core.config import load_config, save_config, DEFAULT_CONFIG
    from promptterfly.utils.io import ensure_dir
    from promptterfly.core.models import ProjectConfig, ModelConfig
    from promptterfly.models.registry import add_model, set_default
    from promptterfly.utils.io import find_project_root

    project_root = path.resolve()
    pt_dir = project_root / ".promptterfly"
    ensure_dir(pt_dir)
    # Create default config
    config = ProjectConfig(**DEFAULT_CONFIG)
    save_config(project_root, config)
    # Create prompts directory
    ensure_dir(pt_dir / "prompts")
    typer.echo(f"✅ Initialized Promptterfly in {pt_dir}")

    # Walkthrough: ask if they want to set up a model now
    setup_model = typer.confirm("Would you like to set up a default model now?", default=True)
    if not setup_model:
        console.print("You can add models later with [bold]promptterfly model add[/bold].")
        return

    console.print("\n[bold]Configure your first LLM model:[/bold]")
    provider = interactive_provider_selection()
    base_url = None
    if provider in {"local", "ollama", "llamacpp"}:
        default_url = "http://localhost:11434" if provider == "ollama" else "http://localhost:5000"
        base_url = typer.prompt("Local server base URL", default=default_url)
    model_id = interactive_model_selection(provider)
    # Normalize model identifier: strip provider prefix if present
    if "/" in model_id:
        parts = model_id.split("/", 1)
        if parts[0] != provider:
            console.print(f"[yellow]Warning: model prefix '{parts[0]}' differs from selected provider '{provider}'. Using '{parts[1]}' as model name.[/yellow]")
        model_id = parts[1]

    # Auto-generate a model config name (registry name)
    name = f"{provider}-{model_id}".replace("/", "-")
    console.print(f"[dim]Using model configuration name: {name}[/dim]")

    # Determine if provider is local (no API key needed)
    if provider in {"local", "ollama", "llamacpp"}:
        api_key_env = None
        set_now = False
        console.print("[dim]Local provider detected; skipping API key setup.[/dim]")
    else:
        # For cloud providers, use standard env var name automatically (no prompt)
        api_key_env = f"{provider.upper()}_API_KEY"
        # Offer to set API key now
        set_now = typer.confirm("Set your API key now? (Recommended)", default=True)

    if set_now:
        # Prompt for API key; require non‑empty input with clear error
        while True:
            key = typer.prompt(f"{provider} API key", hide_input=True).strip()
            if key:
                break
            console.print("[red]API key cannot be empty. Please try again.[/red]")
        dotenv_path = project_root / ".env"
        # Ensure .gitignore has .env
        gitignore_path = project_root / ".gitignore"
        entry = ".env"
        if gitignore_path.exists():
            lines = gitignore_path.read_text().splitlines()
            if entry not in lines:
                with open(gitignore_path, "a") as f:
                    f.write(f"\n{entry}\n")
                typer.echo("[dim]Added .env to .gitignore[/dim]")
        else:
            with open(gitignore_path, "w") as f:
                f.write(f"{entry}\n")
            typer.echo("[dim]Created .gitignore with .env[/dim]")
        # Write key to .env
        if dotenv_path.exists():
            existing = dotenv_path.read_text()
            if f"{api_key_env}=" in existing:
                typer.echo(f"[yellow]{api_key_env} already exists in .env. Skipping.[/yellow]")
            else:
                with open(dotenv_path, "a") as f:
                    f.write(f"\n{api_key_env}={key}\n")
                typer.echo(f"✅ API key saved to {dotenv_path}")
        else:
            with open(dotenv_path, "w") as f:
                f.write(f"{api_key_env}={key}\n")
            typer.echo(f"✅ Created .env with API key at {dotenv_path}")

    # Create ModelConfig and add to registry
    model_cfg = ModelConfig(
        name=name,
        provider=provider,
        model=model_id,
        api_key_env=api_key_env,
        base_url=base_url,
    )
    try:
        add_model(model_cfg, project_root)
        # Set as default
        set_default(name, project_root)
        typer.echo(f"✅ Added model '{name}' and set as default.")
    except ValueError as e:
        console.print(f"[red]Error adding model: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def config():
    """Show current configuration."""
    from promptterfly.core.config import load_config
    import yaml

    cfg = load_config()
    typer.echo(yaml.dump(cfg.model_dump(mode="json"), sort_keys=False))


@app.command()
def config_set(key: str, value: str):
    """Set a configuration value."""
    from promptterfly.core.config import load_config, save_config

    cfg = load_config()
    if not hasattr(cfg, key):
        typer.echo(f"Unknown config key: {key}")
        raise typer.Exit(1)
    # Try to parse value appropriately
    current = getattr(cfg, key)
    if isinstance(current, bool):
        parsed = value.lower() in ("true", "1", "yes", "on")
    elif isinstance(current, int):
        parsed = int(value)
    elif isinstance(current, float):
        parsed = float(value)
    else:
        parsed = value
    setattr(cfg, key, parsed)
    save_config(Path.cwd(), cfg)
    typer.echo(f"Set {key} = {parsed}")


# Import and register subcommands
from promptterfly.commands import prompt, version, optimize, model, auto, dataset  # noqa: E402

app.add_typer(prompt.app, name="prompt")
app.add_typer(version.app, name="version")
app.add_typer(optimize.app, name="optimize")
app.add_typer(model.app, name="model")
app.add_typer(auto.app, name="auto")
app.add_typer(dataset.app, name="dataset")


if __name__ == "__main__":
    app()
