"""Model registry management."""
import os
from pathlib import Path
from typing import List, Optional
import yaml
from pydantic import ValidationError

from ..core.models import ModelConfig
from ..utils.io import find_project_root, ensure_dir, atomic_write, load_yaml, save_yaml


MODELS_FILE = ".promptterfly/models.yaml"


def _get_models_path(project_root: Path) -> Path:
    """Get path to models.yaml file."""
    return project_root / MODELS_FILE


def load_models(project_root: Optional[Path] = None) -> List[ModelConfig]:
    """Load all model configurations from .promptterfly/models.yaml.

    Args:
        project_root: Project root directory. If None, auto-discovered.

    Returns:
        List of ModelConfig objects. Empty list if file doesn't exist or is empty.

    Raises:
        FileNotFoundError: If no project root found.
        ValidationError: If YAML data is invalid.
    """
    if project_root is None:
        project_root = find_project_root()

    models_path = _get_models_path(project_root)

    if not models_path.exists():
        # Create empty models file
        ensure_dir(models_path.parent)
        save_models([], project_root)
        return []

    data = load_yaml(models_path)

    if not data:
        return []

    # Expecting a list of model configs
    if not isinstance(data, list):
        raise ValidationError(
            f"models.yaml should contain a list of model configurations, got {type(data)}",
            ModelConfig
        )

    models = []
    for idx, item in enumerate(data):
        try:
            model = ModelConfig(**item)
            models.append(model)
        except ValidationError as e:
            raise ValidationError(
                f"Invalid model config at index {idx}: {e}",
                ModelConfig
            ) from e

    return models


def save_models(models: List[ModelConfig], project_root: Path) -> None:
    """Save model configurations to .promptterfly/models.yaml.

    Args:
        models: List of ModelConfig objects.
        project_root: Project root directory.
    """
    models_path = _get_models_path(project_root)
    ensure_dir(models_path.parent)

    # Convert to dict list for YAML serialization
    data = [model.model_dump(mode="json") for model in models]
    save_yaml(models_path, data)


def add_model(config: ModelConfig, project_root: Optional[Path] = None) -> None:
    """Add a new model configuration.

    Args:
        config: ModelConfig to add.
        project_root: Project root directory. If None, auto-discovered.

    Raises:
        FileNotFoundError: If no project root found.
    """
    if project_root is None:
        project_root = find_project_root()

    models = load_models(project_root)

    # Remove any existing model with the same name (update)
    models = [m for m in models if m.name != config.name]
    models.append(config)
    save_models(models, project_root)


def remove_model(name: str, project_root: Optional[Path] = None) -> bool:
    """Remove a model configuration by name.

    Args:
        name: Model name to remove.
        project_root: Project root directory. If None, auto-discovered.

    Returns:
        True if model was removed, False if not found.

    Raises:
        FileNotFoundError: If no project root found.
    """
    if project_root is None:
        project_root = find_project_root()

    models = load_models(project_root)
    original_len = len(models)

    models = [m for m in models if m.name != name]

    if len(models) < original_len:
        save_models(models, project_root)
        return True
    return False


def set_default(name: str, project_root: Optional[Path] = None) -> None:
    """Set the default model in ProjectConfig.

    Args:
        name: Model name to set as default.
        project_root: Project root directory. If None, auto-discovered.

    Raises:
        ValueError: If model name doesn't exist.
        FileNotFoundError: If no project root found.
    """
    if project_root is None:
        project_root = find_project_root()

    # First verify the model exists
    models = load_models(project_root)
    if not any(m.name == name for m in models):
        raise ValueError(f"Model '{name}' not found in registry")

    # Load and update ProjectConfig
    from ..core.config import load_config, save_config
    config = load_config(project_root)
    config.default_model = name
    save_config(project_root, config)


def get_model_by_name(name: str, project_root: Optional[Path] = None) -> Optional[ModelConfig]:
    """Retrieve a model configuration by name.

    Args:
        name: Model name to find.
        project_root: Project root directory. If None, auto-discovered.

    Returns:
        ModelConfig if found, None otherwise.
    """
    if project_root is None:
        project_root = find_project_root()

    models = load_models(project_root)
    for model in models:
        if model.name == name:
            return model
    return None
