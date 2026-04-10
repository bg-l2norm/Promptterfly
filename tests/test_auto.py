import pytest
from typer.testing import CliRunner
from promptterfly.cli import app
from pathlib import Path
import os
import promptterfly.utils.io as pt_io
import json

runner = CliRunner()

def test_auto_generate(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pt_io, 'find_project_root', lambda *args, **kwargs: tmp_path)

    # Initialize project
    runner.invoke(app, ["init", "--path", "."], input="n\n")

    # Add a model
    runner.invoke(
        app,
        ["model", "add", "mock-model", "--provider", "openai", "--model", "gpt-4"], input="n\n"
    )
    runner.invoke(app, ["model", "set-default", "mock-model"])

    # Mock litellm completion
    import litellm
    original_completion = litellm.completion

    def mock_completion(*args, **kwargs):
        class MockMessage:
            def __init__(self, content):
                self.content = content

        class MockChoice:
            def __init__(self, message):
                self.message = message

        class MockResponse:
            def __init__(self, choices):
                self.choices = choices

        messages = kwargs.get("messages", [])
        last_content = messages[-1].get("content", "")
        if "from 1 to 100 based on clarity" in last_content:
            content = "95"
        elif "descriptive title" in last_content:
            content = "Mock Title"
        else:
            content = "This is a mock template with {variable}"

        return MockResponse([MockChoice(MockMessage(content))])

    monkeypatch.setattr(litellm, "completion", mock_completion)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")

    result = runner.invoke(app, ["auto", "generate", "I want a prompt", "--iterations", "1"])
    print(result.stdout)
    assert result.exit_code == 0
    assert "Saved optimized prompt 'Mock Title'" in result.stdout

    # Verify saved
    result_show = runner.invoke(app, ["prompt", "show", "1"])
    assert "Mock Title" in result_show.stdout
    assert "This is a mock template with {variable}" in result_show.stdout


def test_auto_generate_fallback(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pt_io, 'find_project_root', lambda *args, **kwargs: tmp_path)

    # Initialize project
    runner.invoke(app, ["init", "--path", "."], input="n\n")

    # Add a model
    runner.invoke(
        app,
        ["model", "add", "mock-model", "--provider", "openai", "--model", "gpt-4"], input="n\n"
    )
    runner.invoke(app, ["model", "set-default", "mock-model"])

    # Mock litellm completion to fail or return bad score
    import litellm
    original_completion = litellm.completion

    def mock_completion(*args, **kwargs):
        class MockMessage:
            def __init__(self, content):
                self.content = content

        class MockChoice:
            def __init__(self, message):
                self.message = message

        class MockResponse:
            def __init__(self, choices):
                self.choices = choices

        messages = kwargs.get("messages", [])
        last_content = messages[-1].get("content", "")
        if "from 1 to 100 based on clarity" in last_content:
            content = "badscore" # Will cause ValueError inside `int()`
        elif "descriptive title" in last_content:
            content = "Fallback Title"
        else:
            content = "This is a fallback template"

        return MockResponse([MockChoice(MockMessage(content))])

    monkeypatch.setattr(litellm, "completion", mock_completion)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")

    result = runner.invoke(app, ["auto", "generate", "I want a prompt", "--iterations", "1"])
    assert result.exit_code == 0
    assert "Saved optimized prompt 'Fallback Title'" in result.stdout

def test_auto_generate_fallback(tmp_path: Path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(pt_io, 'find_project_root', lambda *args, **kwargs: tmp_path)

    # Initialize project
    runner.invoke(app, ["init", "--path", "."], input="n\n")

    # Add a model
    runner.invoke(
        app,
        ["model", "add", "mock-model", "--provider", "openai", "--model", "gpt-4"], input="n\n"
    )
    runner.invoke(app, ["model", "set-default", "mock-model"])

    # Mock litellm completion to fail or return bad score
    import litellm
    original_completion = litellm.completion

    def mock_completion(*args, **kwargs):
        class MockMessage:
            def __init__(self, content):
                self.content = content

        class MockChoice:
            def __init__(self, message):
                self.message = message

        class MockResponse:
            def __init__(self, choices):
                self.choices = choices

        messages = kwargs.get("messages", [])
        last_content = messages[-1].get("content", "")
        if "from 1 to 100 based on clarity" in last_content:
            content = "badscore" # Will cause ValueError inside `int()`
        elif "descriptive title" in last_content:
            content = "Fallback Title"
        else:
            content = "This is a fallback template"

        return MockResponse([MockChoice(MockMessage(content))])

    monkeypatch.setattr(litellm, "completion", mock_completion)
    monkeypatch.setenv("OPENAI_API_KEY", "fake")

    result = runner.invoke(app, ["auto", "generate", "I want a prompt", "--iterations", "1"])
    assert result.exit_code == 0
    assert "Saved optimized prompt 'Fallback Title'" in result.stdout
