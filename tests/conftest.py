"""Pytest configuration and fixtures for Promptterfly tests."""
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from promptterfly.core.models import Prompt, ProjectConfig
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.core.config import save_config, DEFAULT_CONFIG


@pytest.fixture
def temp_project_root(tmp_path: Path) -> Path:
    """
    Create a temporary project root with initialized .promptterfly directory.

    Args:
        tmp_path: pytest built-in tmp_path fixture

    Returns:
        Path to the temporary project root
    """
    project_root = tmp_path / "project"
    project_root.mkdir()

    # Initialize .promptterfly structure
    pt_dir = project_root / ".promptterfly"
    pt_dir.mkdir()
    prompts_dir = pt_dir / "prompts"
    prompts_dir.mkdir()

    # Save default config
    config = ProjectConfig(**DEFAULT_CONFIG)
    save_config(project_root, config)

    return project_root


@pytest.fixture
def temp_promptstore(temp_project_root: Path) -> PromptStore:
    """
    Create a PromptStore instance bound to a temporary project root.

    Args:
        temp_project_root: temporary project root fixture

    Returns:
        PromptStore instance
    """
    return PromptStore(temp_project_root)


@pytest.fixture
def sample_prompt() -> Prompt:
    """
    Create a sample Prompt instance for testing.

    Returns:
        Prompt object with sample data
    """
    now = datetime.now()
    return Prompt(
        id="test123",
        name="Test Prompt",
        description="A test prompt",
        template="Hello, {name}! How are you?",
        tags=["test", "sample"],
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
def populated_promptstore(temp_promptstore: PromptStore, sample_prompt: Prompt) -> PromptStore:
    """
    Create a PromptStore with one prompt saved.

    Args:
        temp_promptstore: PromptStore fixture
        sample_prompt: sample Prompt to save

    Returns:
        PromptStore with saved prompt
    """
    temp_promptstore.save_prompt(sample_prompt)
    return temp_promptstore
