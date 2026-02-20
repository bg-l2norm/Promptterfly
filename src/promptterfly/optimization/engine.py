"""DSPy optimization engine."""
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
from ..core.models import Prompt, ModelConfig
from ..storage.prompt_store import PromptStore
from ..core.config import load_config
from ..models.registry import get_model_by_name, load_models
from .strategies import few_shot


# Strategy registry
STRATEGIES = {
    "few_shot": few_shot,
}


def optimize(prompt_id: int, strategy: str = 'few_shot', dataset_path: Optional[str] = None) -> Prompt:
    """
    Optimize a prompt using a specified strategy.

    Args:
        prompt_id: Identifier of the prompt to optimize (integer).
        strategy: Optimization strategy name (default: 'few_shot').
        dataset_path: Path to dataset file (JSONL). If None, uses
                     .promptterfly/dataset.jsonl in project root.

    Returns:
        New Prompt instance with optimized template and updated updated_at.

    Raises:
        FileNotFoundError: If project root, prompt, or dataset not found.
        ValueError: If strategy not found or model not configured.
    """
    # Find project root
    from ..utils.io import find_project_root
    project_root = find_project_root()
    promptterfly_dir = project_root / ".promptterfly"

    # Initialize PromptStore
    store = PromptStore(project_root)

    # Load the original prompt
    try:
        original_prompt = store.load_prompt(prompt_id)
    except FileNotFoundError as e:
        raise FileNotFoundError(f"Prompt '{prompt_id}' not found") from e

    # Determine dataset path
    if dataset_path is None:
        dataset_file = promptterfly_dir / "dataset.jsonl"
    else:
        dataset_file = Path(dataset_path)
    if not dataset_file.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_file}")

    # Load dataset from JSONL
    dataset: List[Dict[str, Any]] = []
    with open(dataset_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    item = json.loads(line)
                    dataset.append(item)
                except json.JSONDecodeError:
                    # Skip invalid lines
                    continue

    if not dataset:
        raise ValueError("Dataset is empty or invalid")

    # Determine model to use: per-prompt override or default
    config = load_config(project_root)
    # Temporarily load prompt to check override
    try:
        _temp_p = store.load_prompt(prompt_id)
        model_override = getattr(_temp_p, 'model_name', None)
    except Exception:
        model_override = None
    if model_override:
        model_cfg = get_model_by_name(model_override, project_root)
        if not model_cfg:
            raise ValueError(f"Overridden model '{model_override}' not found in registry")
    else:
        default_model_name = config.default_model
        model_cfg = get_model_by_name(default_model_name, project_root)
    if model_cfg is None:
        raise ValueError(f"Default model '{default_model_name}' not found in registry. Add models with 'promptterfly model add'.")

    # Get strategy function
    if strategy not in STRATEGIES:
        raise ValueError(f"Unknown strategy '{strategy}'. Available: {list(STRATEGIES.keys())}")
    strategy_fn = STRATEGIES[strategy]

    # Run optimization
    optimized_template = strategy_fn(original_prompt, dataset, model_cfg)

    # Create new Prompt with updated template and updated_at
    new_prompt = Prompt(
        id=original_prompt.id,
        name=original_prompt.name,
        description=original_prompt.description,
        template=optimized_template,
        created_at=original_prompt.created_at,
        updated_at=datetime.now(),
        model_name=original_prompt.model_name,
        metadata={**original_prompt.metadata, "optimization_strategy": strategy}
    )

    return new_prompt
