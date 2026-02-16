"""Unit tests for data models."""
import pytest
from datetime import datetime
from pathlib import Path
from promptterfly.core.models import (
    ModelConfig,
    Prompt,
    Version,
    ProjectConfig,
)


class TestModelConfig:
    """Tests for ModelConfig."""

    def test_valid_model_config(self):
        """Test creating a valid ModelConfig."""
        config = ModelConfig(
            name="openai-gpt4",
            provider="openai",
            model="gpt-4",
            api_key_env="OPENAI_API_KEY",
            temperature=0.7,
            max_tokens=1024
        )
        assert config.name == "openai-gpt4"
        assert config.provider == "openai"
        assert config.model == "gpt-4"
        assert config.api_key_env == "OPENAI_API_KEY"
        assert config.temperature == 0.7
        assert config.max_tokens == 1024
        assert config.metadata == {}

    def test_defaults(self):
        """Test default values for optional fields."""
        config = ModelConfig(
            name="test-model",
            provider="test",
            model="test-model"
        )
        assert config.api_key_env is None
        assert config.temperature == 0.7
        assert config.max_tokens == 1024
        assert config.metadata == {}

    def test_temperature_range(self):
        """Test temperature must be between 0 and 2."""
        with pytest.raises(Exception):  # Pydantic validation error
            ModelConfig(
                name="test",
                provider="test",
                model="test",
                temperature=2.1
            )
        with pytest.raises(Exception):
            ModelConfig(
                name="test",
                provider="test",
                model="test",
                temperature=-0.1
            )

    def test_max_tokens_positive(self):
        """Test max_tokens must be > 0."""
        with pytest.raises(Exception):
            ModelConfig(
                name="test",
                provider="test",
                model="test",
                max_tokens=0
            )


class TestPrompt:
    """Tests for Prompt."""

    def test_valid_prompt(self):
        """Test creating a valid Prompt."""
        now = datetime.now()
        prompt = Prompt(
            id=123,
            name="My Prompt",
            description="Prompt description",
            template="Say: {text}",
            tags=["tag1", "tag2"],
            created_at=now,
            updated_at=now,
        )
        assert prompt.id == 123
        assert prompt.name == "My Prompt"
        assert prompt.template == "Say: {text}"
        assert prompt.tags == ["tag1", "tag2"]
        assert prompt.created_at == now
        assert prompt.updated_at == now
        assert prompt.metadata == {}

    def test_render_simple(self):
        """Test prompt rendering with variables."""
        prompt = Prompt(
            id=1,
            name="R",
            template="Hello {name}, you have {count} messages",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        result = prompt.render(name="Alice", count=5)
        assert result == "Hello Alice, you have 5 messages"

    def test_render_missing_variable(self):
        """Test render raises error when variable missing."""
        prompt = Prompt(
            id=1,
            name="R",
            template="Hello {name}",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        with pytest.raises(KeyError):
            prompt.render(count=0)

    def test_defaults(self):
        """Test default fields for Prompt."""
        now = datetime.now()
        prompt = Prompt(
            id=1,
            name="N",
            template="T",
            created_at=now,
            updated_at=now,
        )
        assert prompt.description is None
        assert prompt.tags == []
        assert prompt.model_name is None
        assert prompt.metadata == {}


class TestVersion:
    """Tests for Version."""

    def test_valid_version(self):
        """Test creating a Version."""
        now = datetime.now()
        version = Version(
            version=1,
            prompt_id=1,
            snapshot={"id": 1, "name": "P", "template": "T", "created_at": now.isoformat(), "updated_at": now.isoformat()},
            message="Initial version",
            created_at=now,
        )
        assert version.version == 1
        assert version.prompt_id == 1
        assert version.snapshot["name"] == "P"
        assert version.message == "Initial version"
        assert version.created_at == now

    def test_defaults(self):
        """Test default fields."""
        now = datetime.now()
        version = Version(
            version=2,
            prompt_id=1,
            snapshot={},
            created_at=now,
        )
        assert version.message is None
        # No metrics field in the model; ensure no extra attributes
        assert not hasattr(version, 'metrics')


class TestProjectConfig:
    """Tests for ProjectConfig."""

    def test_defaults(self):
        """Test default configuration values."""
        config = ProjectConfig()
        assert config.prompts_dir == Path("prompts")
        assert config.auto_version is True
        assert config.default_model == "gpt-3.5-turbo"
        assert config.optimization == {}

    def test_custom_values(self):
        """Test custom configuration."""
        config = ProjectConfig(
            prompts_dir=Path("my_prompts"),
            auto_version=False,
            default_model="claude-3-opus",
            optimization={"max_epochs": 20}
        )
        assert config.prompts_dir == Path("my_prompts")
        assert config.auto_version is False
        assert config.default_model == "claude-3-opus"
        assert config.optimization["max_epochs"] == 20
