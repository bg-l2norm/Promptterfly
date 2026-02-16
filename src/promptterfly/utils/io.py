"""I/O utilities for Promptterfly."""
import os
import json
import yaml
from pathlib import Path
from typing import Any, Optional, Union
import tempfile
import shutil


def find_project_root(start: Optional[Path] = None) -> Path:
    """Find project root by searching up for .promptterfly directory."""
    if start is None:
        start = Path.cwd()
    current = start.resolve()
    while current != current.parent:
        if (current / ".promptterfly").is_dir():
            return current
        current = current.parent
    raise FileNotFoundError("No .promptterfly directory found in parent directories")


def ensure_dir(path: Union[str, Path]) -> Path:
    """Create directory if it doesn't exist."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def atomic_write(path: Union[str, Path], data: str) -> None:
    """Atomically write text file using temp file + rename."""
    p = Path(path)
    ensure_dir(p.parent)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=p.parent, delete=False) as f:
        f.write(data)
        temp_path = f.name
    os.replace(temp_path, p)


def atomic_write_json(path: Union[str, Path], data: Any, indent: int = 2) -> None:
    """Atomically write JSON file."""
    json_str = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    atomic_write(path, json_str)


def read_json(path: Union[str, Path]) -> Any:
    """Read and parse JSON file."""
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_yaml(path: Union[str, Path]) -> Any:
    """Load YAML file."""
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Union[str, Path], data: Any) -> None:
    """Save data to YAML file."""
    yaml_str = yaml.dump(data, sort_keys=False, allow_unicode=True)
    atomic_write(path, yaml_str)
