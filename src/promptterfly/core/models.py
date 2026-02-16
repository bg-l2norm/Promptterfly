"""Core data models for Promptterfly."""
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ModelConfig(BaseModel):
    """Configuration for an LLM model."""
    name: str = Field(..., description="Unique model identifier")
    provider: str = Field(..., description="Provider: openai, anthropic, etc.")
    model: str = Field(..., description="Model name (e.g. gpt-4, claude-3-opus)")
    api_key_env: Optional[str] = Field(None, description="Env var name for API key")
    temperature: float = Field(0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(1024, gt=0)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Prompt(BaseModel):
    """A prompt template with metadata."""
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    description: Optional[str] = None
    template: str
    tags: List[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    model_name: Optional[str] = Field(default=None, alias="model_config")
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def render(self, **variables) -> str:
        """Render prompt with variables."""
        return self.template.format(**variables)


class Version(BaseModel):
    """A specific version of a prompt."""
    version: int
    prompt_id: int
    snapshot: Dict[str, Any]
    message: Optional[str] = None
    created_at: datetime


class ProjectConfig(BaseModel):
    """Project-level configuration (.promptterfly/config.yaml)."""
    prompts_dir: Path = Field(Path("prompts"), description="Relative prompts path")
    auto_version: bool = Field(True, description="Auto-version on changes")
    default_model: str = Field("gpt-3.5-turbo", description="Default LLM")
    optimization: Dict[str, Any] = Field(default_factory=dict)
