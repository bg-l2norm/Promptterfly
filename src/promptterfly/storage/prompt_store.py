"""Prompt storage and CRUD operations with auto-versioning."""
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

from ..core.models import Prompt
from ..utils.io import atomic_write_json, read_json


class PromptStore:
    """Manages prompt persistence in the local filesystem."""

    def __init__(self, project_root: Path):
        """
        Initialize PromptStore.

        Args:
            project_root: Project root directory (contains .promptterfly/)
        """
        self.project_root = project_root
        self.promptterfly_dir = project_root / ".promptterfly"
        self.prompts_dir = self.promptterfly_dir / "prompts"
        self.versions_base_dir = self.promptterfly_dir / "versions"

    def get_prompt_path(self, prompt_id: str) -> Path:
        """
        Get filesystem path for a prompt's JSON file.

        Args:
            prompt_id: Unique prompt identifier

        Returns:
            Path to the prompt JSON file
        """
        return self.prompts_dir / f"{prompt_id}.json"

    def get_versions_dir(self, prompt_id: str) -> Path:
        """
        Get directory containing version snapshots for a prompt.

        Args:
            prompt_id: Unique prompt identifier

        Returns:
            Path to the versions directory for this prompt
        """
        return self.versions_base_dir / prompt_id

    def _prompt_to_dict(self, prompt: Prompt) -> dict:
        """
        Convert Prompt model to a JSON-serializable dict.

        Handles datetime serialization to ISO format.

        Args:
            prompt: Prompt instance

        Returns:
            Dictionary ready for JSON serialization
        """
        data = prompt.model_dump(mode='json')
        # Ensure datetime fields are ISO strings
        if isinstance(data.get('created_at'), datetime):
            data['created_at'] = data['created_at'].isoformat()
        if isinstance(data.get('updated_at'), datetime):
            data['updated_at'] = data['updated_at'].isoformat()
        return data

    def _dict_to_prompt(self, data: dict) -> Prompt:
        """
        Convert dictionary (from JSON) to Prompt model.

        Handles datetime string parsing.

        Args:
            data: Dictionary from JSON

        Returns:
            Prompt instance
        """
        # Ensure datetime strings are parsed if needed
        # Pydantic should handle this automatically with datetime fields
        return Prompt.model_validate(data)

    def save_prompt(self, prompt: Prompt) -> None:
        """
        Save a prompt atomically to disk.

        Args:
            prompt: Prompt instance to save
        """
        data = self._prompt_to_dict(prompt)
        target_path = self.get_prompt_path(prompt.id)
        atomic_write_json(target_path, data)

    def load_prompt(self, prompt_id: str) -> Prompt:
        """
        Load a prompt from disk.

        Args:
            prompt_id: Prompt identifier

        Returns:
            Prompt instance

        Raises:
            FileNotFoundError: If prompt doesn't exist
            json.JSONDecodeError: If JSON is malformed
            ValidationError: If data doesn't match Prompt schema
        """
        path = self.get_prompt_path(prompt_id)
        data = read_json(path)
        return self._dict_to_prompt(data)

    def list_prompts(self) -> List[Prompt]:
        """
        List all prompts in the prompts directory.

        Returns:
            List of Prompt instances sorted by updated_at (newest first)
        """
        prompts = []
        if not self.prompts_dir.exists():
            return prompts

        for json_file in self.prompts_dir.glob("*.json"):
            try:
                data = read_json(json_file)
                prompt = self._dict_to_prompt(data)
                prompts.append(prompt)
            except Exception:
                # Skip invalid files
                continue

        # Sort by updated_at descending
        prompts.sort(key=lambda p: p.updated_at, reverse=True)
        return prompts

    def create_snapshot(self, prompt_id: str, message: Optional[str] = None) -> None:
        """
        Create a version snapshot of the current prompt.

        Copies the current prompt JSON to the versions directory with
        a version number and metadata.

        Args:
            prompt_id: Prompt identifier
            message: Optional commit message for this version

        Raises:
            FileNotFoundError: If the prompt doesn't exist
        """
        # Ensure versions directory exists
        versions_dir = self.get_versions_dir(prompt_id)
        versions_dir.mkdir(parents=True, exist_ok=True)

        # Load the current prompt
        current_prompt = self.load_prompt(prompt_id)

        # Determine next version number
        existing_versions = list(versions_dir.glob("*.json"))
        if existing_versions:
            # Extract version numbers from filenames (e.g., "001.json")
            version_numbers = []
            for vfile in existing_versions:
                try:
                    num = int(vfile.stem)
                    version_numbers.append(num)
                except ValueError:
                    continue
            next_version = max(version_numbers) + 1 if version_numbers else 1
        else:
            next_version = 1

        # Create version snapshot
        snapshot = {
            "version": next_version,
            "prompt_id": prompt_id,
            "snapshot": current_prompt.model_dump(mode='json'),
            "message": message,
            "created_at": datetime.now().isoformat()
        }

        # Write snapshot
        version_path = versions_dir / f"{next_version:03d}.json"
        atomic_write_json(version_path, snapshot)

    def delete_prompt(self, prompt_id: str) -> None:
        """
        Delete a prompt and all its versions.

        Args:
            prompt_id: Prompt identifier
        """
        # Delete main prompt file
        path = self.get_prompt_path(prompt_id)
        if path.exists():
            path.unlink()

        # Delete versions directory
        versions_dir = self.get_versions_dir(prompt_id)
        if versions_dir.exists():
            shutil.rmtree(versions_dir)
