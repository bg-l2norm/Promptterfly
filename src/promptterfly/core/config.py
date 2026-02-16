"""Configuration loader and manager."""
import os
from pathlib import Path
from typing import Optional
import yaml
from .models import ProjectConfig
from ..utils.io import find_project_root, ensure_dir, atomic_write


DEFAULT_CONFIG = {
    "prompts_dir": "prompts",
    "auto_version": True,
    "default_model": "gpt-3.5-turbo",
    "optimization": {}
}


def load_config(project_root: Optional[Path] = None) -> ProjectConfig:
    """Load project config from .promptterfly/config.yaml."""
    if project_root is None:
        project_root = find_project_root()
    config_path = project_root / ".promptterfly" / "config.yaml"
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        # Merge with defaults for missing keys
        merged = {**DEFAULT_CONFIG, **data}
        return ProjectConfig(**merged)
    else:
        # Create default config
        cfg = ProjectConfig(**DEFAULT_CONFIG)
        ensure_dir(config_path.parent)
        save_config(project_root, cfg)
        return cfg


def save_config(project_root: Path, config: ProjectConfig) -> None:
    """Save config to .promptterfly/config.yaml."""
    config_path = project_root / ".promptterfly" / "config.yaml"
    data = config.model_dump(mode="json")
    # Convert Path to string for YAML
    if isinstance(data.get("prompts_dir"), Path):
        data["prompts_dir"] = str(data["prompts_dir"])
    yaml_str = yaml.dump(data, sort_keys=False)
    atomic_write(config_path, yaml_str)
