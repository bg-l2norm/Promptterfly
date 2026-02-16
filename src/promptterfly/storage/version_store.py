"""Version management operations."""
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from ..core.models import Prompt, Version
from ..utils.io import read_json, atomic_write_json


class VersionStore:
    """Manages prompt version history and restoration."""

    def __init__(self, project_root: Path):
        """
        Initialize VersionStore.

        Args:
            project_root: Project root directory (contains .promptterfly/)
        """
        self.project_root = project_root
        self.promptterfly_dir = project_root / ".promptterfly"
        self.versions_base_dir = self.promptterfly_dir / "versions"

    def list_versions(self, prompt_id: str) -> List[Version]:
        """
        List all versions for a prompt, sorted by version number (ascending).

        Args:
            prompt_id: Prompt identifier

        Returns:
            List of Version instances, oldest first

        Raises:
            FileNotFoundError: If the versions directory doesn't exist
        """
        versions_dir = self.versions_base_dir / prompt_id
        if not versions_dir.exists():
            return []

        versions = []
        for json_file in sorted(versions_dir.glob("*.json")):
            try:
                data = read_json(json_file)
                version = Version.model_validate(data)
                versions.append(version)
            except Exception:
                # Skip invalid version files
                continue

        # Sort by version number (ascending)
        versions.sort(key=lambda v: v.version)
        return versions

    def restore_version(self, prompt_id: str, version_number: int) -> Prompt:
        """
        Restore a prompt to a specific version.

        Copies the version snapshot back to the current prompt file.

        Args:
            prompt_id: Prompt identifier
            version_number: Version number to restore (1-indexed)

        Returns:
            Restored Prompt instance

        Raises:
            FileNotFoundError: If version doesn't exist
            ValueError: If version number is invalid
        """
        versions_dir = self.versions_base_dir / prompt_id
        version_path = versions_dir / f"{version_number:03d}.json"

        if not version_path.exists():
            raise FileNotFoundError(f"Version {version_number} not found for prompt {prompt_id}")

        # Load version snapshot
        data = read_json(version_path)
        version = Version.model_validate(data)

        # Reconstruct Prompt from snapshot
        prompt_data = version.snapshot.copy()
        # Ensure timestamps are present
        if 'created_at' in prompt_data and isinstance(prompt_data['created_at'], str):
            prompt_data['created_at'] = prompt_data['created_at']
        if 'updated_at' in prompt_data and isinstance(prompt_data['updated_at'], str):
            prompt_data['updated_at'] = prompt_data['updated_at']

        prompt = Prompt.model_validate(prompt_data)

        # Save restored prompt as current version (atomic write)
        from .prompt_store import PromptStore
        prompt_store = PromptStore(self.project_root)
        prompt_store.save_prompt(prompt)

        return prompt

    def get_version_details(self, prompt_id: str, version_number: int) -> Optional[Version]:
        """
        Get details for a specific version.

        Args:
            prompt_id: Prompt identifier
            version_number: Version number

        Returns:
            Version instance or None if not found
        """
        versions_dir = self.versions_base_dir / prompt_id
        version_path = versions_dir / f"{version_number:03d}.json"

        if not version_path.exists():
            return None

        try:
            data = read_json(version_path)
            return Version.model_validate(data)
        except Exception:
            return None
