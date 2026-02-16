"""
Configuration loading and saving for Promptterfly.

Handles project-local configuration stored in .promptterfly/config.yaml.
"""

import yaml
from pathlib import Path
from typing import Optional
from pydantic import ValidationError

from .models import ProjectConfig

CONFIG_DIR = ".promptterfly"
CONFIG_FILE = "config.yaml"


def load_config(project_root: Path) -> ProjectConfig:
    """
    Load project configuration from .promptterfly/config.yaml.

    If the config file does not exist, creates a default configuration.

    Args:
        project_root: Root directory of the project

    Returns:
        ProjectConfig: Validated configuration object

    Raises:
        InvalidConfig: If the config file exists but is invalid
    """
    config_path = project_root / CONFIG_DIR / CONFIG_FILE

    if not config_path.exists():
        # Create default config
        config = ProjectConfig()
        save_config(project_root, config)
        return config

    try:
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f) or {}

        # Validate and construct ProjectConfig
        config = ProjectConfig(**data)
        return config

    except (yaml.YAMLError, ValidationError) as e:
        raise InvalidConfig(f"Failed to load config from {config_path}: {e}") from e


def save_config(project_root: Path, config: ProjectConfig) -> None:
    """
    Save configuration to .promptterfly/config.yaml.

    Args:
        project_root: Root directory of the project
        config: ProjectConfig object to serialize
    """
    config_dir = project_root / CONFIG_DIR
    config_dir.mkdir(parents=True, exist_ok=True)
    config_path = config_dir / CONFIG_FILE

    # Convert to dict, handling Path serialization
    data = config.model_dump()
    # Convert Path objects to strings
    if isinstance(data.get('prompts_dir'), Path):
        data['prompts_dir'] = str(data['prompts_dir'])

    with open(config_path, 'w') as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def get_config_dir(project_root: Path) -> Path:
    """
    Get the .promptterfly directory path for the project.

    Args:
        project_root: Root directory of the project

    Returns:
        Path to .promptterfly directory
    """
    return project_root / CONFIG_DIR
