# Promptterfly

A self-evolving prompt manager that automatically optimizes your prompts — smart, easy access, and always improving.

**Local-first, terminal-based prompt versioning & optimization with DSPy.**

---

## Why Promptterfly?

- **No Git required** – automatic local versioning with snapshots
- **DSPy-powered optimization** – improve prompts with few-shot learning in one command
- **Zero hassle setup** – `./start.sh` guides you through first-time install
- **Model-agnostic** – configure any LLM provider (OpenAI, Anthropic, etc.)
- **Terminal-native** – works where you work, rich UI, no web app

## Installation

### One-command bootstrap (recommended)

```bash
./start.sh
```

The script will:
- Create a virtual environment (`.venv/`) or reuse existing
- Install package and optional dependencies (test/dev)
- Configure your environment
- Auto-activate on future runs

Afterwards, simply use:

```bash
./start.sh --help
./start.sh init
./start.sh prompt create
```

### Manual install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"   # core + test deps
# or: pip install -e .     # core only
```

## Quick Start

```bash
# 1. Initialize in your project
promptterfly init

# 2. Create a prompt (interactive)
promptterfly prompt create

# 3. List prompts
promptterfly prompt list

# 4. Render with variables
promptterfly render <prompt_id> variables.json

# 5. Optimize it (uses DSPy + your configured model)
promptterfly optimize improve <prompt_id> --strategy few_shot

# 6. View version history
promptterfly version history <prompt_id>

# 7. Rollback if needed
promptterfly version restore <prompt_id> 1
```

## Configuration

After `init`, configuration lives in `.promptterfly/config.yaml`:

```yaml
auto_version: true
default_model: gpt-3.5-turbo
prompts_dir: prompts
optimization: {}
```

You can edit it directly or use `promptterfly config set <key> <value>`.

**Model registry:** Add models via `promptterfly model add` and set a default. LiteLLM integration means any supported provider works (OpenAI, Anthropic, Google, Together, local, etc.).

## Storage Layout

```
.project-root/
├── .promptterfly/
│   ├── config.yaml
│   ├── models.yaml
│   ├── prompts/
│   │   └── <prompt_id>.json        # current state
│   └── versions/
│       └── <prompt_id>/
│           ├── 001.json             # snapshots (auto-version)
│           ├── 002.json
│           └── ...
```

No Git noise; everything is plain files you can inspect.

## Commands

### Prompt management
- `prompt list` – table of all prompts
- `prompt show <id>` – display template and metadata
- `prompt create` – interactive creation
- `prompt update <id>` – edit fields
- `prompt delete <id>` – remove prompt and its versions
- `prompt render <id> [vars.json]` – render with variables

### Versioning
- `version history <id>` – list snapshots
- `version restore <id> <version>` – rollback to a snapshot

### Optimization
- `optimize improve <id> [--strategy few_shot] [--dataset path]` – run DSPy optimization (creates new version)

### Model management
- `model list` – show configured models
- `model add <name>` – interactive add (provider, model, api_key_env)
- `model remove <name>` – delete a model
- `model set-default <name>` – set default for optimization

### Project & config
- `init [--path dir]` – initialize project
- `config show` – print configuration
- `config set <key> <value>` – update configuration

Run `promptterfly --help` or `promptterfly <command> --help` for details.

## How Optimization Works (Under the Hood)

1. `optimize improve` takes your prompt template and a small dataset of input/output examples (default: `.promptterfly/dataset.jsonl`).
2. DSPy builds a signature from your prompt’s variable names and compiles a few-shot module using `BootstrapFewShot`.
3. The best demonstrations are selected and appended to your prompt as an `Examples:` section.
4. A new prompt version is saved automatically.

You provide the dataset; the tool picks the examples. The result is a prompt that performs better with minimal effort.

## Development & Testing

```bash
# Run test suite
./scripts/test_all.sh

# Or manually
source .venv/bin/activate
pytest -v --cov=promptterfly --cov-report=term-missing
```

Project structure and architecture are documented in `docs/development.md`.

## Requirements

- Python 3.11+
- (optional) virtual environment tooling (`venv`)
- LLM provider API key for optimization (e.g., `OPENAI_API_KEY`)

## License

MIT
