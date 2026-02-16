# Promptterfly

A self-evolving prompt manager that automatically optimizes your prompts — smart, easy access, and always improving.

---

A local CLI tool for managing and optimizing prompts with simple versioning and model-based optimization. Designed as a lightweight, terminal-first application with file-based persistence — no Git required.

## Features

- Prompt management with templates and variable rendering
- Automatic versioning on every change (zero-config)
- Model-agnostic optimization using DSPy
- Local-first: all data stored in `.promptterfly/`
- Rich terminal UI with tables and syntax highlighting

## Installation & Usage

**First run:**

```bash
./start.sh
```

The `start.sh` script will:
- Detect if it's your first time
- Ask if you want to create a virtual environment (recommended)
- Let you choose optional dependencies (test, dev)
- Set up the `promptterfly` command
- Automatically activate the environment on subsequent runs

After setup, you can simply run:

```bash
./start.sh --help
./start.sh init
./start.sh prompt create
```

Or, if you prefer, you can activate the venv manually and use the command directly:

```bash
source .venv/bin/activate
promptterfly --help
```

**Manual install (alternative):**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test,dev]"  # or just -e . for core
```

## Quick Start

```bash
# Initialize in current project
promptterfly init

# Create a new prompt
promptterfly prompt create

# List prompts
promptterfly prompt list

# Render a prompt with variables
promptterfly render <prompt_id> variables.json

# Optimize a prompt
promptterfly optimize improve <prompt_id> --strategy few_shot

# View version history
promptterfly version history <prompt_id>

# Restore to a previous version
promptterfly version restore <prompt_id> 1
```

## Configuration

After `promptterfly init`, configuration is stored in `.promptterfly/config.yaml`. Default settings can be overridden per project or globally (`~/.promptterfly/`).

## Documentation

See `docs/usage.md` for detailed usage and `docs/development.md` for contributor notes.

## License

MIT
