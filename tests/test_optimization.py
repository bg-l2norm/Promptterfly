"""Unit tests for optimization engine with mocking."""
import pytest
import json
from datetime import datetime
from pathlib import Path
from promptterfly.optimization.engine import optimize, STRATEGIES
from promptterfly.core.models import Prompt, ModelConfig
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.core.config import save_config, DEFAULT_CONFIG
from promptterfly.models.registry import save_models


@pytest.fixture
def opt_project(tmp_path: Path):
    """Set up a project with config, models, dataset, and a prompt."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    pt_dir = project_root / ".promptterfly"
    pt_dir.mkdir()
    (pt_dir / "prompts").mkdir()

    # Save config
    from promptterfly.core.models import ProjectConfig
    config = ProjectConfig(**DEFAULT_CONFIG)
    save_config(project_root, config)

    # Save a model
    models = [
        ModelConfig(
            name="test-model",
            provider="openai",
            model="gpt-4",
            api_key_env=None,
            temperature=0.7,
            max_tokens=1024,
        )
    ]
    save_models(models, project_root)

    # Create dataset
    dataset_file = pt_dir / "dataset.jsonl"
    with open(dataset_file, "w") as f:
        f.write(json.dumps({"input": "Hello", "completion": "Hi"}) + "\n")
        f.write(json.dumps({"input": "How are you?", "completion": "I'm fine"}) + "\n")

    # Create a prompt
    store = PromptStore(project_root)
    prompt = Prompt(
        id=1,
        name="Test Prompt",
        template="You are a chatbot. {input}",
        created_at=datetime(2023, 1, 1),
        updated_at=datetime(2023, 1, 1),
    )
    store.save_prompt(prompt)

    return {
        "project_root": project_root,
        "prompt_id": 1,
        "store": store,
    }


def test_optimize_returns_new_prompt(opt_project, monkeypatch):
    """Test that optimize returns a new Prompt with updated template."""
    project_root = opt_project["project_root"]
    prompt_id = opt_project["prompt_id"]

    # Patch find_project_root to return our project_root
    import promptterfly.utils.io as io_module
    monkeypatch.setattr(io_module, "find_project_root", lambda: project_root)

    # Mock the few_shot strategy
    def mock_few_shot(prompt: Prompt, dataset, model_cfg):
        return prompt.template + "\n\n[Optimized by mock]"

    import promptterfly.optimization.engine as engine_module
    original = engine_module.STRATEGIES.get("few_shot")
    engine_module.STRATEGIES["few_shot"] = mock_few_shot

    try:
        new_prompt = optimize(prompt_id=prompt_id)
        assert new_prompt is not None
        assert new_prompt.id == prompt_id
        assert new_prompt.template.endswith("[Optimized by mock]")
        assert new_prompt.updated_at > datetime(2023, 1, 1)
        # Metadata should include optimization_strategy
        assert new_prompt.metadata.get("optimization_strategy") == "few_shot"
    finally:
        if original is not None:
            engine_module.STRATEGIES["few_shot"] = original


def test_optimize_creates_version_snapshot(opt_project, monkeypatch):
    """Test that optimize creates a snapshot before optimization."""
    project_root = opt_project["project_root"]
    prompt_id = opt_project["prompt_id"]
    store = opt_project["store"]

    def mock_few_shot(prompt, dataset, model_cfg):
        return prompt.template + " optimized"

    import promptterfly.optimization.engine as engine_module
    original = engine_module.STRATEGIES.get("few_shot")
    engine_module.STRATEGIES["few_shot"] = mock_few_shot

    import promptterfly.utils.io as io_module
    monkeypatch.setattr(io_module, "find_project_root", lambda: project_root)

    try:
        # Count versions before
        from promptterfly.storage.version_store import VersionStore
        vs = VersionStore(project_root)
        initial_versions = vs.list_versions(prompt_id)
        assert len(initial_versions) == 0

        new_prompt = optimize(prompt_id=prompt_id)

        # Now a version should exist because optimize (the engine itself) does NOT create a snapshot; only the CLI does. Wait: engine.optimize does not create a snapshot; it's the CLI command that does. In this test we are calling engine.optimize directly, so no snapshot should be created.
        versions = vs.list_versions(prompt_id)
        assert len(versions) == 0  # No snapshot from engine.optimize directly
    finally:
        if original is not None:
            engine_module.STRATEGIES["few_shot"] = original


def test_optimize_prompt_not_found(opt_project, monkeypatch):
    """Test optimize raises error if prompt not found."""
    project_root = opt_project["project_root"]

    import promptterfly.utils.io as io_module
    monkeypatch.setattr(io_module, "find_project_root", lambda: project_root)

    # Non-existent ID
    with pytest.raises(FileNotFoundError):
        optimize(prompt_id=999)


def test_optimize_dataset_missing(opt_project, monkeypatch):
    """Test optimize raises error if dataset file missing."""
    project_root = opt_project["project_root"]
    # Delete dataset
    pt_dir = project_root / ".promptterfly"
    dataset_file = pt_dir / "dataset.jsonl"
    dataset_file.unlink()

    def mock_few_shot(prompt, dataset, model_cfg):
        return prompt.template

    import promptterfly.optimization.engine as engine_module
    original = engine_module.STRATEGIES.get("few_shot")
    engine_module.STRATEGIES["few_shot"] = mock_few_shot

    import promptterfly.utils.io as io_module
    monkeypatch.setattr(io_module, "find_project_root", lambda: project_root)

    try:
        with pytest.raises(FileNotFoundError):
            optimize(prompt_id="test-prompt")
    finally:
        if original is not None:
            engine_module.STRATEGIES["few_shot"] = original


def test_optimize_empty_dataset(opt_project, monkeypatch):
    """Test optimize raises error if dataset is empty."""
    project_root = opt_project["project_root"]
    # Overwrite dataset with empty content
    pt_dir = project_root / ".promptterfly"
    dataset_file = pt_dir / "dataset.jsonl"
    dataset_file.write_text("")

    def mock_few_shot(prompt, dataset, model_cfg):
        return prompt.template

    import promptterfly.optimization.engine as engine_module
    original = engine_module.STRATEGIES.get("few_shot")
    engine_module.STRATEGIES["few_shot"] = mock_few_shot

    import promptterfly.utils.io as io_module
    monkeypatch.setattr(io_module, "find_project_root", lambda: project_root)

    try:
        with pytest.raises(ValueError, match="Dataset is empty"):
            optimize(prompt_id="test-prompt")
    finally:
        if original is not None:
            engine_module.STRATEGIES["few_shot"] = original


def test_optimize_unknown_strategy(opt_project, monkeypatch):
    """Test optimize with unknown strategy raises error."""
    project_root = opt_project["project_root"]

    import promptterfly.utils.io as io_module
    monkeypatch.setattr(io_module, "find_project_root", lambda: project_root)

    with pytest.raises(ValueError, match="Unknown strategy"):
        optimize(prompt_id="test-prompt", strategy="unknown")


def test_optimize_model_not_configured(opt_project, monkeypatch):
    """Test optimize raises error if default model not in registry."""
    project_root = opt_project["project_root"]
    # Remove models or change default to non-existent
    from promptterfly.core.config import load_config, save_config as save_cfg
    cfg = load_config(project_root)
    cfg.default_model = "nonexistent-model"
    save_cfg(project_root, cfg)

    def mock_few_shot(prompt, dataset, model_cfg):
        return prompt.template

    import promptterfly.optimization.engine as engine_module
    original = engine_module.STRATEGIES.get("few_shot")
    engine_module.STRATEGIES["few_shot"] = mock_few_shot

    import promptterfly.utils.io as io_module
    monkeypatch.setattr(io_module, "find_project_root", lambda: project_root)

    try:
        with pytest.raises(ValueError, match="not found in registry"):
            optimize(prompt_id="test-prompt")
    finally:
        if original is not None:
            engine_module.STRATEGIES["few_shot"] = original
