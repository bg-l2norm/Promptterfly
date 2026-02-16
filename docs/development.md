# Development Guidelines

## Project Structure

```
src/promptterfly/
├── __init__.py
├── __main__.py
├── cli.py                       # Typer app and command wiring
├── core/
│   ├── models.py                # Pydantic data models
│   ├── config.py                # Configuration loading/saving
│   └── exceptions.py            # Custom exception classes
├── storage/
│   ├── prompt_store.py          # CRUD operations and versioning
│   └── version_store.py         # History and restore logic
├── optimization/
│   ├── engine.py                # DSPy wrapper and optimization
│   └── strategies.py            # Built-in optimization strategies
├── models/
│   ├── registry.py              # Model registry management
│   └── client.py                # LLM client wrapper using LiteLLM
├── utils/
│   ├── io.py                    # File and path operations
│   └── tui.py                   # Rich terminal UI helpers
└── commands/                    # Individual command modules
    ├── prompt.py
    ├── version.py
    ├── optimize.py
    └── model.py
```

## Architecture Recap

Promptterfly is a local CLI tool for managing and optimizing prompts with simple versioning. It follows a clean layered architecture:

- **CLI Layer**: Typer commands defined in `commands/` modules, aggregated in `cli.py`.
- **Core Layer**: Pydantic models defining data structures (`Prompt`, `Version`, `ModelConfig`, `ProjectConfig`).
- **Storage Layer**: `PromptStore` and `VersionStore` handle file-based persistence with atomic writes. All data is stored under `.promptterfly/` in the project root.
- **Optimization Layer**: `engine.py` uses DSPy to apply strategies (e.g., few-shot) to improve prompts based on a dataset. Strategies are in `strategies.py`.
- **Model Registry**: `registry.py` manages model configurations stored in `models.yaml`. A unified LLM client in `client.py` uses LiteLLM to make API calls.
- **Utilities**: `io.py` provides atomic file operations and project root discovery; `tui.py` uses Rich for terminal output.

Data flows from CLI commands through service/storage layers, with configuration loaded from YAML. Optimization is triggered via the `optimize improve` command.

## Coding Standards

- Python 3.11+
- Type hints required for all function signatures
- Pydantic v2 for data validation
- Use `rich` for all terminal output (tables, colored messages)
- Keep functions small and testable
- Prefer composition over inheritance
- Error handling: raise appropriate exceptions, catch at CLI layer to display user-friendly messages
- Logging: Use `typer.echo` or `rich.console` for user-facing output; avoid print()

## Testing

Run the full test suite with coverage:

```bash
./scripts/test_all.sh
```

Or manually:

```bash
export PYTHONPATH=src
pytest -v --cov=promptterfly --cov-report=term-missing
```

Unit tests reside in `tests/`:
- `test_models.py` validates Pydantic models.
- `test_storage.py` tests PromptStore and VersionStore with temporary directories.
- `test_cli.py` uses Typer's CliRunner for integration tests.
- `test_optimization.py` mocks DSPy and LLM calls to test engine.optimize.

Aim for >80% coverage on core logic. Mock external API calls and DSPy.

## Linting & Formatting

```bash
ruff check src/
black src/
```

## Adding a New Command

1. Add function in appropriate module under `commands/`
2. Import and wire in `cli.py`
3. Add tests in `tests/test_<module>.py`
4. Update `docs/usage.md` if user-facing

## Configuration Schema

Project config (`.promptterfly/config.yaml`):

```yaml
prompts_dir: prompts
auto_version: true
default_model: gpt-3.5-turbo
optimization:
  max_epochs: 10
  metric: accuracy
```

Model registry (`.promptterfly/models.yaml`):

```yaml
models:
  - name: openai-gpt4
    provider: openai
    model: gpt-4
    api_key_env: OPENAI_API_KEY
    temperature: 0.7
    max_tokens: 1024
default_model: openai-gpt4
```

## Releasing

Bump version in `pyproject.toml`, commit, and:

```bash
pip install -e .
python -m build
twine upload dist/*
```

## Notes

- The `optimization` module depends on `dspy`. Ensure it is installed and compatible.
- LiteLLM is used for provider-agnostic LLM calls.
- Version snapshots are stored as JSON files with zero-padded version numbers (001, 002).
- Atomic file writes prevent corruption on interruption.
