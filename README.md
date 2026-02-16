# Promptterfly

A self-evolving prompt manager that automatically optimizes your prompts — smart, easy access, and always improving.

**Local-first, terminal-based prompt versioning & optimization with DSPy.**

---

## Why Promptterfly?

- **No Git required** – automatic local versioning with snapshots
- **DSPy-powered optimization** – improve prompts with few-shot learning in one command
- **Zero hassle setup** – one script installs, another launches
- **Model-agnostic** – configure any LLM provider (OpenAI, Anthropic, etc.)
- **Terminal-native** – works where you work, rich TUI, no web app

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

After installation, launch the interactive Promptterfly shell:

```bash
./start.sh
```

Inside the REPL, type commands **without** the `promptterfly` prefix:

```text
❯ help
❯ init
❯ prompt create
❯ optimize improve myprompt
❯ version history myprompt
❯ exit
```

The REPL features:
- Colored banner with a random programmer quote each start
- Onboarding tips on first run
- Context-sensitive hints (e.g., after `prompt create`, suggests optimization)
- Ctrl+C friendly; returns to prompt

### Visual Experience

Promptterfly's REPL is designed to be both informative and delightful:

- **Startup Banner**: A colorful ASCII art butterfly with sparkles greets you on launch, accompanied by a random programmer quote to set the tone.
- **Spiky Loading Animation**: During optimization (and other long-running operations), a custom "spiky" spinner made of Braille characters pulses, giving visual feedback that work is in progress.
- **Rich Terminal UI**: Tables, colored text, and panels enhance readability and create an engaging experience.

Example banner:

```
        ✦   ✧
    ✦     ⋆
    ✧   ✨
        ...
[bold cyan]╔═══════════════════════════════════════════════════╗[/bold cyan]
[bold cyan]║[/bold cyan]  [bold magenta]    __  __  ____   ___  ____   ____ ___ [/bold magenta]  [bold cyan]║[/bold cyan]
...
```

You can also run a single command directly:

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
# Inside the REPL:

# Initialize in your project
init

# Create a prompt (interactive)
prompt create

# List prompts
prompt list

# Render a prompt with variables
render <prompt_id> variables.json

# Optimize it (uses DSPy + your configured model)
optimize improve <prompt_id> --strategy few_shot

# View version history
version history <prompt_id>

# Restore a previous version
version restore <prompt_id> 1
```

## Configuration

After `init`, configuration lives in `.promptterfly/config.yaml`:

```yaml
auto_version: true
default_model: gpt-3.5-turbo
prompts_dir: prompts
optimization: {}
```

You can edit it directly or use `config set <key> <value>`.

**Model registry:** Add models via `model add` and set a default. LiteLLM integration means any supported provider works (OpenAI, Anthropic, Google, Together, local, etc.).

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

Run `help` inside the REPL or `promptterfly --help` for full details.

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
