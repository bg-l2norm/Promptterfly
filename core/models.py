"""
Core Pydantic v2 models for Promptterfly.

These models define the data structures for prompts, versions, model configurations,
and project settings.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class ModelConfig(BaseModel):
    """
    Configuration for a language model provider.

    Attributes:
        name: Unique identifier for this model config (e.g., "gpt-4-turbo")
        provider: Provider name (openai, anthropic, google, etc.)
        model: The actual model identifier (e.g., "gpt-4", "claude-3-opus")
        api_key_env: Environment variable name that holds the API key (optional)
        temperature: Sampling temperature (default: 0.7)
        max_tokens: Maximum tokens to generate (default: 1024)
    """
    model_config = ConfigDict(extra='ignore')

    name: str
    provider: str = Field(..., description="openai, anthropic, etc.")
    model: str = Field(..., description="e.g. gpt-4, claude-3-opus")
    api_key_env: Optional[str] = Field(None, description="Env var name for API key")
    temperature: float = 0.7
    max_tokens: int = 1024


class Prompt(BaseModel):
    """
    A prompt template with metadata.

    Attributes:
        id: Unique identifier (UUID or short hash)
        name: Human-readable name
        description: Optional description of the prompt's purpose
        template: The prompt template string with {variable} placeholders
        tags: List of tags for categorization
        created_at: Creation timestamp
        updated_at: Last update timestamp
        model_config: Preferred model config name (optional)
        metadata: Arbitrary additional metadata
    """
    model_config = ConfigDict(extra='allow')

    id: str
    name: str
    description: Optional[str] = None
    template: str
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    model_config: Optional[str] = None
    metadata: Dict[str, Any] = {}


class Version(BaseModel):
    """
    A version snapshot of a prompt.

    Attributes:
        version: Version number (1, 2, 3, ...)
        prompt_id: ID of the prompt this version belongs to
        snapshot: Full Prompt model data at that time (dict)
        message: Optional commit message describing the change
        created_at: Timestamp when this version was created
        strategy: Optional optimization strategy used (if any)
        metrics: Optional metrics/performance data
    """
    model_config = ConfigDict(extra='allow')

    version: int
    prompt_id: str
    snapshot: Dict[str, Any]
    message: Optional[str] = None
    created_at: datetime
    strategy: Optional[str] = None
    metrics: Dict[str, float] = {}


class ProjectConfig(BaseModel):
    """
    Project-level configuration for Promptterfly.

    Attributes:
        prompts_dir: Relative path to prompts directory (default: "prompts")
        auto_version: Whether to auto-create versions on prompt updates (default: True)
        default_model: Name of default model config to use (default: "gpt-3.5-turbo")
        optimization: Dictionary of optimization settings
    """
    model_config = ConfigDict(extra='allow')

    prompts_dir: Path = Path("prompts")
    auto_version: bool = True
    default_model: str = "gpt-3.5-turbo"
    optimization: Dict[str, Any] = {}
