# Promptterfly

A self-evolving prompt manager that automatically optimizes your prompts — smart, easy access, and always improving.

**Local-first, terminal-based prompt versioning & optimization with DSPy.**

---

## Why Promptterfly?

- **No Git required** – automatic local versioning with snapshots
- **DSPy-powered optimization** – improve prompts with few-shot learning in one command
- **Zero hassle setup** – one script installs, another launches
- **Model-agnostic** – configure any LLM provider (OpenAI, Anthropic, etc.)
- **Terminal-native** – works where you work, rich UI, no web app

## Installation

Run the setup script once to install Promptterfly and its dependencies:

```bash
./setup.sh
```

It will:
- Create a virtual environment (`.venv/`) if needed
- Install the package and optional extras (test/dev) of your choice
- Mark the installation as complete

## Usage

After installation, launch an interactive shell with Promptterfly ready:

```bash
./start.sh
```

This opens a shell with the virtual environment activated. Inside, run `promptterfly` commands:

```bash
promptterfly --help
promptterfly init
promptterfly prompt create
promptterfly optimize improve <id>
```

You can also pass a command directly:

```bash
./start.sh prompt list
./start.sh version history <id>
```

**Manual activation (alternative):**

```bash
source .venv/bin/activate
promptterfly --help
```

## Quick Start

```bash
# Inside the start.sh shell:

# Initialize in your project
promptterfly init

# Create a prompt (interactive)
promptterfly prompt create

# List prompts
promptterfly prompt list

# Render a prompt with variables
promptterfly render <prompt_id> variables.json

# Optimize it (uses DSPy + your configured model)
promptterfly optimize improve <prompt_id> --strategy few_shot

# View version history
promptterfly version history <prompt_id>

# Restore a previous version
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

Plain files, no Git required.

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

## How Optimization Works

1. `optimize improve` takes your prompt and a dataset (default `.promptterfly/dataset.jsonl`) of input/output examples.
2. DSPy builds a signature from your prompt’s variables and compiles a few-shot module via `BootstrapFewShot`.
3. The best demonstrations are selected and appended as an `Examples:` section.
4. A new prompt version is saved automatically.

You provide quality examples; the tool selects the most effective ones.

## Development & Testing

```bash
# Run test suite (after setup)
./scripts/test_all.sh

# Or manually
source .venv/bin/activate
pytest -v --cov=promptterfly --cov-report=term-missing
```

Architecture and implementation details are in `docs/development.md`.

## Requirements

- Python 3.11+
- (optional) virtual environment tooling (`venv`)
- LLM provider API key for optimization (e.g., `OPENAI_API_KEY`)

## License

MIT
