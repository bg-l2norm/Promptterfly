"""Promptterfly CLI entry point."""
import typer
from typing import Optional
from pathlib import Path

app = typer.Typer(help="Promptterfly: Local prompt manager with versioning & optimization")


@app.command()
def init(path: Path = typer.Option(Path.cwd(), "--path", help="Project directory")):
    """Initialize Promptterfly in the current or specified directory."""
    from promptterfly.core.config import load_config, save_config, DEFAULT_CONFIG
    from promptterfly.utils.io import ensure_dir

    project_root = path.resolve()
    pt_dir = project_root / ".promptterfly"
    ensure_dir(pt_dir)
    # Create default config
    from promptterfly.core.models import ProjectConfig
    config = ProjectConfig(**DEFAULT_CONFIG)
    save_config(project_root, config)
    # Create prompts directory
    ensure_dir(pt_dir / "prompts")
    typer.echo(f"Initialized Promptterfly in {pt_dir}")


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
from promptterfly.commands import prompt, version, optimize, model  # noqa: E402

app.add_typer(prompt.app, name="prompt")
app.add_typer(version.app, name="version")
app.add_typer(optimize.app, name="optimize")
app.add_typer(model.app, name="model")


if __name__ == "__main__":
    app()
