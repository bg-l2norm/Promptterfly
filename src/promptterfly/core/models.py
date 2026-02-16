from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class ModelConfig(BaseModel):
    name: str
    provider: str
    model: str
    api_key_env: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1024
    metadata: Dict[str, Any] = {}

class Prompt(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    name: str
    description: Optional[str] = None
    template: str
    created_at: datetime
    updated_at: datetime
    model_name: Optional[str] = Field(default=None, alias="model")
    metadata: Dict[str, Any] = {}

class Version(BaseModel):
    version: int
    prompt_id: int
    snapshot: Dict[str, Any]
    message: Optional[str] = None
    created_at: datetime

class ProjectConfig(BaseModel):
    prompts_dir: Path = Path("prompts")
    auto_version: bool = True
    default_model: str = "gpt-3.5-turbo"
    optimization: Dict[str, Any] = {}
