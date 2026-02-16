"""Unit tests for storage layer."""
import pytest
import json
from datetime import datetime
from pathlib import Path
from promptterfly.storage.prompt_store import PromptStore
from promptterfly.storage.version_store import VersionStore
from promptterfly.core.models import Prompt


class TestPromptStore:
    """Tests for PromptStore."""

    def test_save_and_load_prompt(self, temp_promptstore: PromptStore, sample_prompt: Prompt):
        """Test saving and loading a prompt."""
        temp_promptstore.save_prompt(sample_prompt)
        loaded = temp_promptstore.load_prompt(sample_prompt.id)
        assert loaded.id == sample_prompt.id
        assert loaded.name == sample_prompt.name
        assert loaded.template == sample_prompt.template
        # Compare timestamps approximately? They should be same if saved/loaded without modification
        # But loaded may have string->datetime conversion; they should be equal
        assert loaded.created_at == sample_prompt.created_at
        assert loaded.updated_at == sample_prompt.updated_at

    def test_load_nonexistent_prompt_raises(self, temp_promptstore: PromptStore):
        """Test loading a prompt that doesn't exist raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            temp_promptstore.load_prompt(999)

    def test_list_prompts_empty(self, temp_promptstore: PromptStore):
        """Test listing prompts when directory is empty."""
        prompts = temp_promptstore.list_prompts()
        assert prompts == []

    def test_list_prompts_sorted_by_updated(self, temp_project_root: Path):
        """Test that prompts are sorted by updated_at descending."""
        store = PromptStore(temp_project_root)
        # Create three prompts with different updated_at times
        times = [
            datetime(2023, 1, 1, 12, 0),
            datetime(2023, 1, 2, 12, 0),
            datetime(2023, 1, 3, 12, 0),
        ]
        prompts = []
        for i, t in enumerate(times):
            p = Prompt(
                id=i,  # integer IDs: 0,1,2
                name=f"Prompt {i}",
                template=f"T{i}",
                created_at=t,
                updated_at=t,
            )
            store.save_prompt(p)
            prompts.append(p)

        # Sleep small amount to ensure different order?
        # But we set explicit times; list should sort by updated_at descending
        listed = store.list_prompts()
        assert len(listed) == 3
        # Should be in descending order: newest first
        assert listed[0].updated_at >= listed[1].updated_at >= listed[2].updated_at
        # Since we saved p0 (oldest), p1, p2 (newest) in that order,
        # but sorting by updated_at descending gives: p2 (id=2), p1 (id=1), p0 (id=0)
        ids = [p.id for p in listed]
        assert ids == [2, 1, 0]

    def test_create_snapshot_creates_version_file(self, populated_promptstore: PromptStore, sample_prompt: Prompt):
        """Test that create_snapshot writes a version file."""
        vs = VersionStore(populated_promptstore.project_root)
        # Initially no versions
        versions = vs.list_versions(sample_prompt.id)
        assert len(versions) == 0

        # Create snapshot
        populated_promptstore.create_snapshot(sample_prompt.id, message="test version")

        versions = vs.list_versions(sample_prompt.id)
        assert len(versions) == 1
        v = versions[0]
        assert v.version == 1
        assert v.message == "test version"
        assert v.prompt_id == sample_prompt.id
        # Snapshot should contain prompt data
        assert v.snapshot["id"] == sample_prompt.id
        assert v.snapshot["name"] == sample_prompt.name

    def test_create_snapshot_increments_version_number(self, populated_promptstore: PromptStore, sample_prompt: Prompt):
        """Test that creating multiple snapshots increments version numbers."""
        store = populated_promptstore
        # Create 3 snapshots
        store.create_snapshot(sample_prompt.id, "v1")
        store.create_snapshot(sample_prompt.id, "v2")
        store.create_snapshot(sample_prompt.id, "v3")

        vs = VersionStore(store.project_root)
        versions = vs.list_versions(sample_prompt.id)
        assert len(versions) == 3
        version_numbers = [v.version for v in versions]
        assert version_numbers == [1, 2, 3]

    def test_delete_prompt_removes_files(self, populated_promptstore: PromptStore, sample_prompt: Prompt):
        """Test deleting a prompt removes its JSON and versions."""
        store = populated_promptstore
        # Create a snapshot first to test version deletion
        store.create_snapshot(sample_prompt.id, "before delete")
        # Verify prompt and version exist
        prompt_path = store.get_prompt_path(sample_prompt.id)
        versions_dir = store.get_versions_dir(sample_prompt.id)
        assert prompt_path.exists()
        assert versions_dir.exists()

        store.delete_prompt(sample_prompt.id)

        assert not prompt_path.exists()
        assert not versions_dir.exists()

    def test_atomic_write_json_creates_file(self, temp_promptstore: PromptStore, tmp_path: Path):
        """Test atomic_write_json writes valid JSON."""
        from promptterfly.utils.io import atomic_write_json
        test_file = tmp_path / "test.json"
        data = {"key": "value", "number": 42}
        atomic_write_json(test_file, data)
        assert test_file.exists()
        with open(test_file) as f:
            loaded = json.load(f)
        assert loaded == data


class TestVersionStore:
    """Tests for VersionStore."""

    def test_list_versions_empty(self, temp_project_root: Path):
        """Test listing versions when none exist."""
        vs = VersionStore(temp_project_root)
        versions = vs.list_versions(999)
        assert versions == []

    def test_restore_version(self, temp_project_root: Path):
        """Test restoring a prompt to a specific version."""
        # Create a PromptStore and add a prompt
        store = PromptStore(temp_project_root)
        prompt1 = Prompt(
            id=1,
            name="Original",
            template="Original template",
            created_at=datetime(2023, 1, 1),
            updated_at=datetime(2023, 1, 1),
        )
        store.save_prompt(prompt1)

        # Create a snapshot manually? Actually create_snapshot uses current prompt state.
        # We'll create a version by saving the prompt, then creating snapshot, then modify prompt, create another snapshot, then restore.
        store.create_snapshot(prompt1.id, "v1")
        # Modify prompt
        prompt2 = Prompt(
            id=1,
            name="Modified",
            template="Modified template",
            created_at=prompt1.created_at,
            updated_at=datetime(2023, 1, 2),
        )
        store.save_prompt(prompt2)
        store.create_snapshot(prompt1.id, "v2")

        # Now restore to version 1
        vs = VersionStore(temp_project_root)
        restored = vs.restore_version(prompt1.id, 1)

        assert restored.name == "Original"
        assert restored.template == "Original template"
        assert restored.updated_at.date() == datetime(2023, 1, 1).date()

        # The restored prompt should be saved as current
        current = store.load_prompt(prompt1.id)
        assert current.name == "Original"
        assert current.template == "Original template"

    def test_restore_nonexistent_version_raises(self, temp_project_root: Path):
        """Test restoring a version that doesn't exist raises FileNotFoundError."""
        vs = VersionStore(temp_project_root)
        with pytest.raises(FileNotFoundError):
            vs.restore_version(999, 1)

    def test_get_version_details(self, temp_project_root: Path):
        """Test getting details for a specific version."""
        store = PromptStore(temp_project_root)
        prompt = Prompt(
            id=1,
            name="Test",
            template="T",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        store.save_prompt(prompt)
        store.create_snapshot(prompt.id, "first version")

        vs = VersionStore(temp_project_root)
        details = vs.get_version_details(prompt.id, 1)
        assert details is not None
        assert details.version == 1
        assert details.message == "first version"

        # Non-existent version returns None
        assert vs.get_version_details(prompt.id, 999) is None
