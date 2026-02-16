"""CLI integration tests using Typer's CliRunner."""
import os
import json
import pytest
from typer.testing import CliRunner
from promptterfly.cli import app
from pathlib import Path
from promptterfly.storage.prompt_store import PromptStore

runner = CliRunner()


def test_init_command(tmp_path: Path):
    """Test that 'init' creates .promptterfly with config."""
    result = runner.invoke(app, ["init"], cwd=tmp_path)
    assert result.exit_code == 0
    pt_dir = tmp_path / ".promptterfly"
    assert pt_dir.exists()
    assert (pt_dir / "config.yaml").exists()
    assert (pt_dir / "prompts").exists()


def test_config_show(tmp_path: Path):
    """Test 'config' command shows current configuration."""
    # Initialize first
    runner.invoke(app, ["init"], cwd=tmp_path)
    result = runner.invoke(app, ["config"], cwd=tmp_path)
    assert result.exit_code == 0
    assert "prompts_dir:" in result.stdout
    assert "auto_version:" in result.stdout
    assert "default_model:" in result.stdout


def test_config_set(tmp_path: Path):
    """Test 'config set' updates configuration."""
    runner.invoke(app, ["init"], cwd=tmp_path)
    result = runner.invoke(app, ["config", "set", "auto_version", "false"], cwd=tmp_path)
    assert result.exit_code == 0
    result = runner.invoke(app, ["config"], cwd=tmp_path)
    assert "auto_version: false" in result.stdout


def test_prompt_create_and_list(tmp_path: Path):
    """Test creating a prompt and listing it."""
    runner.invoke(app, ["init"], cwd=tmp_path)
    # Input for interactive create: name, description, tags, template
    input_data = b"My Test Prompt\nA sample prompt\ntest, sample\nHello {name}, you have {count} messages\n"
    result = runner.invoke(app, ["prompt", "create"], input=input_data, cwd=tmp_path)
    assert result.exit_code == 0
    assert "Created prompt" in result.stdout

    # List prompts
    result = runner.invoke(app, ["prompt", "list"], cwd=tmp_path)
    assert result.exit_code == 0
    assert "My Test Prompt" in result.stdout
    assert "test, sample" in result.stdout or "test" in result.stdout


def test_prompt_show(tmp_path: Path):
    """Test 'prompt show' displays prompt details."""
    runner.invoke(app, ["init"], cwd=tmp_path)
    # Create a prompt and capture the ID from the output? Alternatively, we can read the prompts file.
    input_data = b"Show Test\nDescription here\ntag1\nTemplate: {var}\n"
    runner.invoke(app, ["prompt", "create"], input=input_data, cwd=tmp_path)
    # Find prompt id by listing prompts directory
    prompts_dir = tmp_path / ".promptterfly" / "prompts"
    prompt_file = next(prompts_dir.glob("*.json"))
    prompt_id = prompt_file.stem

    result = runner.invoke(app, ["prompt", "show", prompt_id], cwd=tmp_path)
    assert result.exit_code == 0
    assert "Show Test" in result.stdout
    assert "Template: {var}" in result.stdout


def test_prompt_update(tmp_path: Path):
    """Test updating an existing prompt."""
    runner.invoke(app, ["init"], cwd=tmp_path)
    # Create prompt
    input_data = b"Original Name\nDesc\ntags\nOriginal template\n"
    runner.invoke(app, ["prompt", "create"], input=input_data, cwd=tmp_path)
    prompts_dir = tmp_path / ".promptterfly" / "prompts"
    prompt_file = next(prompts_dir.glob("*.json"))
    prompt_id = prompt_file.stem

    # Update: leave blank for most fields, change template only by providing new template and EOF
    # Input: name (Enter for same), description (Enter), tags (Enter), template (new line then EOF)
    input_update = b"\n\n\nUpdated template\n"
    result = runner.invoke(app, ["prompt", "update", prompt_id], input=input_update, cwd=tmp_path)
    assert result.exit_code == 0
    # Verify update
    result = runner.invoke(app, ["prompt", "show", prompt_id], cwd=tmp_path)
    assert result.exit_code == 0
    assert "Updated template" in result.stdout


def test_prompt_delete(tmp_path: Path):
    """Test deleting a prompt with confirmation."""
    runner.invoke(app, ["init"], cwd=tmp_path)
    # Create prompt
    input_data = b"To Delete\nDesc\ntags\nTemplate\n"
    runner.invoke(app, ["prompt", "create"], input=input_data, cwd=tmp_path)
    prompts_dir = tmp_path / ".promptterfly" / "prompts"
    prompt_file = next(prompts_dir.glob("*.json"))
    prompt_id = prompt_file.stem

    # Delete with confirmation 'y'
    result = runner.invoke(app, ["prompt", "delete", prompt_id], input="y\n", cwd=tmp_path)
    assert result.exit_code == 0
    assert "Deleted prompt" in result.stdout
    assert not prompt_file.exists()

    # Delete with 'n' should cancel
    # Need to recreate prompt
    runner.invoke(app, ["prompt", "create"], input=input_data, cwd=tmp_path)
    prompt_file = next(prompts_dir.glob("*.json"))
    prompt_id = prompt_file.stem
    result = runner.invoke(app, ["prompt", "delete", prompt_id], input="n\n", cwd=tmp_path)
    assert result.exit_code == 0
    assert "Cancelled" in result.stdout
    assert prompt_file.exists()


def test_version_history_and_restore(tmp_path: Path):
    """Test version history listing and restore using manual snapshots."""
    runner.invoke(app, ["init"], cwd=tmp_path)
    # Create a prompt
    input_data = b"Versioned Prompt\nDesc\ntags\nOriginal\n"
    runner.invoke(app, ["prompt", "create"], input=input_data, cwd=tmp_path)
    prompts_dir = tmp_path / ".promptterfly" / "prompts"
    prompt_file = next(prompts_dir.glob("*.json"))
    prompt_id = prompt_file.stem

    # Create snapshots manually to simulate version history
    store = PromptStore(tmp_path)
    store.create_snapshot(prompt_id, "Initial version")
    # Modify the prompt
    p = store.load_prompt(prompt_id)
    p.template = "First edited template"
    store.save_prompt(p)
    store.create_snapshot(prompt_id, "After first edit")
    # Modify again
    p = store.load_prompt(prompt_id)
    p.template = "Second edited template"
    store.save_prompt(p)
    store.create_snapshot(prompt_id, "After second edit")

    # Check history
    result = runner.invoke(app, ["version", "history", prompt_id], cwd=tmp_path)
    assert result.exit_code == 0
    assert "Version History" in result.stdout
    # Should list versions 1, 2, 3
    assert "1" in result.stdout and "2" in result.stdout and "3" in result.stdout
    # Check presence of messages (optional)
    assert "Initial version" in result.stdout
    assert "After first edit" in result.stdout

    # Current prompt should be "Second edited template"
    result = runner.invoke(app, ["prompt", "show", prompt_id], cwd=tmp_path)
    assert result.exit_code == 0
    assert "Second edited template" in result.stdout

    # Restore to version 1
    result = runner.invoke(app, ["version", "restore", prompt_id, "1"], input="y\n", cwd=tmp_path)
    assert result.exit_code == 0
    assert "Restored prompt" in result.stdout
    # Now show should have original template
    result = runner.invoke(app, ["prompt", "show", prompt_id], cwd=tmp_path)
    assert result.exit_code == 0
    assert "Original" in result.stdout
    assert "Second edited" not in result.stdout


def test_model_commands(tmp_path: Path):
    """Test model add, list, set-default, remove."""
    runner.invoke(app, ["init"], cwd=tmp_path)
    # Add a model
    result = runner.invoke(
        app,
        ["model", "add", "test-model", "--provider", "openai", "--model", "gpt-4", "--max-tokens", "2048"],
        cwd=tmp_path,
    )
    assert result.exit_code == 0
    assert "Added model 'test-model'" in result.stdout

    # List models
    result = runner.invoke(app, ["model", "list"], cwd=tmp_path)
    assert result.exit_code == 0
    assert "test-model" in result.stdout

    # Set default
    result = runner.invoke(app, ["model", "set-default", "test-model"], cwd=tmp_path)
    assert result.exit_code == 0
    assert "Default model set to 'test-model'" in result.stdout

    # List should show (default) marker
    result = runner.invoke(app, ["model", "list"], cwd=tmp_path)
    assert "(default)" in result.stdout

    # Remove should fail if it's default? According to implementation, we prevent removal of default.
    result = runner.invoke(app, ["model", "remove", "test-model"], cwd=tmp_path, input="y\n")
    # Actually our implementation checks default and errors out before confirmation.
    assert result.exit_code == 1
    assert "Cannot remove default model" in result.stdout

    # Change default to something else? But there is only one model. So first add another model.
    result = runner.invoke(
        app,
        ["model", "add", "other-model", "--provider", "anthropic", "--model", "claude-3-opus"],
        cwd=tmp_path,
    )
    assert result.exit_code == 0
    # Set default to other-model
    result = runner.invoke(app, ["model", "set-default", "other-model"], cwd=tmp_path)
    assert result.exit_code == 0
    # Now remove test-model should work
    result = runner.invoke(app, ["model", "remove", "test-model"], cwd=tmp_path, input="y\n")
    assert result.exit_code == 0
    assert "Removed model 'test-model'" in result.stdout


def test_optimize_improve(tmp_path: Path, monkeypatch):
    """Test optimize improve command with mocked engine."""
    # Initialize project
    runner.invoke(app, ["init"], cwd=tmp_path)

    # Create a model
    runner.invoke(
        app,
        ["model", "add", "mock-model", "--provider", "openai", "--model", "gpt-4"],
        cwd=tmp_path,
    )
    # The config default_model is still gpt-3.5-turbo; we must also set default to mock-model
    runner.invoke(app, ["model", "set-default", "mock-model"], cwd=tmp_path)

    # Create a prompt
    input_data = b"Test Prompt\nDesc\ntags\nOriginal template {var}\n"
    runner.invoke(app, ["prompt", "create"], input=input_data, cwd=tmp_path)
    prompts_dir = tmp_path / ".promptterfly" / "prompts"
    prompt_file = next(prompts_dir.glob("*.json"))
    prompt_id = prompt_file.stem

    # Create dataset file
    pt_dir = tmp_path / ".promptterfly"
    dataset_path = pt_dir / "dataset.jsonl"
    with open(dataset_path, "w") as f:
        f.write(json.dumps({"var": "input1", "completion": "output1"}) + "\n")
        f.write(json.dumps({"var": "input2", "completion": "output2"}) + "\n")

    # Mock the engine's strategy to return a modified template without calling dspy
    from promptterfly.optimization import engine
    original_strategies = engine.STRATEGIES.copy()

    def mock_few_shot(prompt, dataset, model_cfg):
        return prompt.template + "\n\n[Optimized]"

    engine.STRATEGIES["few_shot"] = mock_few_shot

    try:
        result = runner.invoke(
            app,
            ["optimize", "improve", prompt_id],
            cwd=tmp_path,
        )
        assert result.exit_code == 0
        assert "Optimization complete" in result.stdout

        # Verify prompt template was updated
        current_prompt = json.loads(open(prompt_file).read())
        assert "[Optimized]" in current_prompt["template"]
        # Check version history: optimize should have created a snapshot before optimization
        versions_dir = pt_dir / "versions" / prompt_id
        assert versions_dir.exists()
        version_files = list(versions_dir.glob("*.json"))
        # At least one version snapshot with message containing "Before optimization"
        assert any("Before optimization" in vf.read_text() for vf in version_files)
    finally:
        # Restore original strategies
        engine.STRATEGIES.update(original_strategies)


def test_optimize_errors(tmp_path: Path):
    """Test error handling for optimize command."""
    runner.invoke(app, ["init"], cwd=tmp_path)
    # No model configured
    result = runner.invoke(app, ["optimize", "improve", "nonexistent"], cwd=tmp_path)
    assert result.exit_code == 1
    # Create a model but still no dataset
    runner.invoke(
        app,
        ["model", "add", "test-model", "--provider", "openai", "--model", "gpt-4"],
        cwd=tmp_path,
    )
    # Also set default? Actually optimize uses default model. We set default to test-model? config default is still gpt-3.5-turbo. We'll add a model that matches default? Better to also set default to test-model.
    runner.invoke(app, ["model", "set-default", "test-model"], cwd=tmp_path)

    # Create a prompt
    input_data = b"Prompt\nDesc\ntags\nTemplate\n"
    runner.invoke(app, ["prompt", "create"], input=input_data, cwd=tmp_path)
    prompts_dir = tmp_path / ".promptterfly" / "prompts"
    prompt_file = next(prompts_dir.glob("*.json"))
    prompt_id = prompt_file.stem

    # Dataset missing -> .promptterfly/dataset.jsonl not exist
    result = runner.invoke(app, ["optimize", "improve", prompt_id], cwd=tmp_path)
    assert result.exit_code == 1
    assert "Dataset file not found" in result.stdout

    # Provide dataset with invalid content (empty)
    pt_dir = tmp_path / ".promptterfly"
    dataset_path = pt_dir / "dataset.jsonl"
    with open(dataset_path, "w") as f:
        f.write("")  # empty
    result = runner.invoke(app, ["optimize", "improve", prompt_id], cwd=tmp_path)
    assert result.exit_code == 1
    assert "Dataset is empty or invalid" in result.stdout

    # Invalid strategy
    result = runner.invoke(app, ["optimize", "improve", prompt_id, "--strategy", "unknown"], cwd=tmp_path)
    assert result.exit_code == 1
    assert "Unknown strategy" in result.stdout
