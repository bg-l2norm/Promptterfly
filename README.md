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

---

## Installation

Run the setup script once to install Promptterfly and its dependencies:

```bash
./setup.sh
```

It will:
- Create a virtual environment (`.venv/`) if needed
- Install the package and optional extras (test/dev) of your choice
- Mark the installation as complete

## Launch

After installation, start the interactive Promptterfly shell:

```bash
./start.sh
```

You can also run single commands directly without entering the REPL:

```bash
./start.sh prompt list
./start.sh version history <id>
```

Or activate the virtual environment manually and use the CLI:

```bash
source .venv/bin/activate
promptterfly --help
```

---

## Getting Started: First Steps

If you're new to Promptterfly, follow these steps:

1. **Initialize your project** (run inside your project directory):
   ```bash
   init
   ```
   This creates a `.promptterfly/` directory with default configuration and a `prompts/` subfolder.

2. **Add an LLM model** (required for optimization):
   ```bash
   model add mymodel --provider openai --model gpt-4 --api-key-env OPENAI_API_KEY
   model set-default mymodel
   ```
   You can use any LiteLLM-supported provider (Anthropic, Google, local, etc.).

3. **Create your first prompt**:
   ```bash
   prompt create
   ```
   You'll be prompted for a name, optional description, tags, and the template (use `{variable}` placeholders).

4. **Render with variables** (optional):
   Create a JSON file with values for your template variables, e.g.:
   ```json
   { "name": "Alice", "count": 5 }
   ```
   Then run:
   ```bash
   prompt render <prompt_id> vars.json
   ```

5. **Optimize your prompt**:
   ```bash
   optimize improve <prompt_id> --strategy few_shot
   ```
   Requires a dataset (default: `.promptterfly/dataset.jsonl`). See "Optimization" below.

6. **Explore version history**:
   ```bash
   version history <prompt_id>
   version restore <prompt_id> <version_number>
   ```

---

## Inside the REPL

The interactive shell (`./start.sh`) offers a richer experience:

- Colored banner with a random programmer quote each start
- Onboarding tips on first run
- Context-sensitive hints (e.g., after `prompt create`, suggests optimization)
- Command aliases for faster typing (see below)
- Ctrl+C friendly; returns to prompt

Type `help` inside the REPL to see all commands and aliases.

### Visual Experience

Promptterfly's REPL is designed to be both informative and delightful:

- **Startup Banner**: A colorful ASCII art butterfly with sparkles greets you on launch, accompanied by a random programmer quote.
- **Spiky Loading Animation**: During optimization (and other long-running operations), a custom "spiky" spinner made of Braille characters pulses.
- **Rich Terminal UI**: Tables, colored text, and panels enhance readability.

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

---

## Quick Reference

### Commands (inside REPL, without prefix)

```text
init [--path dir]              Initialize project
prompt list                    List prompts
prompt show <id>               Show prompt template + metadata
prompt create                  Create prompt interactively
prompt update <id>             Edit prompt
prompt delete <id>             Delete prompt
prompt render <id> [vars.json] Render with variables from JSON
version history <id>           Show version history
version restore <id> <ver>     Restore a previous version
optimize improve <id> [--strategy few_shot] [--dataset path] Run optimization
model list                     List configured models
model add <name> [--provider ...] Add model (interactive or flags)
model remove <name>            Remove a model
model set-default <name>       Set default model for optimization
config show                    Show configuration
config set <key> <value>       Update configuration value
help                           Show this help (includes all aliases)
exit / quit                    Leave REPL
```

### Command Aliases

The REPL supports short aliases for common commands:

- `ls` → `prompt list`
- `new` or `create` → `prompt create`
- `show <id>` → `prompt show <id>`
- `del` → `prompt delete`
- `run` → `prompt render`
- `hist` → `version history`
- `restore` → `version restore`
- `opt` → `optimize improve`
- `models` → `model list`
- `addmodel` → `model add`
- `setmodel` → `model set-default`

Type `help` inside the REPL to see the full alias mapping.

---

## Concepts

### Integer IDs

Each prompt is identified by a simple sequential integer (1, 2, 3...). IDs are assigned automatically when you create a prompt and stored in a counter file (`.promptterfly/counter`). This approach has several benefits:

- **Predictable**: Easy to reference in scripts and documentation.
- **Human-friendly**: Short numbers are quicker to type than long hashes or UUIDs.
- **Stable**: Once assigned, an ID is never reused, even if the prompt is deleted.
- **Local-only**: IDs are unique within the project; no coordination needed.

When you run commands like `prompt show 5` or `optimize improve 12`, you're referring to these integer IDs. The `prompt list` command displays the current IDs alongside names.

### Variables and Rendering

Prompt templates use Python-style `{variable}` placeholders. At render time, you supply a JSON file containing key-value pairs for those variables.

Example:

Template:
```
Hello {customer_name}! Thank you for contacting {company}. How can we assist you today?
```

JSON (`vars.json`):
```json
{
  "customer_name": "Alice",
  "company": "Acme Inc"
}
```

Render command:
```bash
prompt render <prompt_id> vars.json
```

Output:
```
Hello Alice! Thank you for contacting Acme Inc. How can we assist you today?
```

Rules:
- All variables used in the template must be present in the JSON, otherwise a `KeyError` is raised.
- Extra keys in the JSON are ignored.
- You can also pipe the JSON via stdin if your shell supports it (e.g., `echo '{"x":1}' | prompt render <id> -` is not yet supported; currently a file path is required).

### Tags vs Description

- **Description**: A free-form text (up to a few sentences) that explains what the prompt is for. It appears in `prompt show` and is meant for human readers. Optional.
- **Tags**: One or more short labels (e.g., `support`, `marketing`, `creative`) used for categorization and filtering. Use commas to add multiple tags. You can list prompts by tag: `prompt list --tag support`.

**When to use which?**
- Add a description when you want to explain the prompt's purpose, scope, or how to use it.
- Add tags to group prompts by domain, project, or any scheme that helps you find them quickly.

### Optimization

Promptterfly uses DSPy to automatically improve your prompts.

**How it works:**
1. You provide a dataset of input/output examples (`.promptterfly/dataset.jsonl`). Each line is a JSON object with at least an `input` field (what the user says) and a `completion` field (the ideal output).
2. `optimize improve` builds a signature from your template's variables and uses `BootstrapFewShot` to select the most effective few-shot examples.
3. The optimized prompt is saved as a new version.

The original prompt is automatically snapshotted before optimization, so you can always roll back.

---

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

---

## Storage Layout

```
.project-root/
├── .promptterfly/
│   ├── config.yaml
│   ├── models.yaml
│   ├── counter                # stores last used integer ID
│   ├── prompts/
│   │   └── <prompt_id>.json   # current state (e.g., 1.json, 2.json)
│   └── versions/
│       └── <prompt_id>/
│           ├── 001.json       # snapshots (auto-version)
│           ├── 002.json
│           └── ...
```

Plain files, no Git required.

---

## Commands (Full List)

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

Run `help` inside the REPL or see the Quick Reference above for details.

---

## How Optimization Works

1. `optimize improve` takes your prompt and a dataset (default `.promptterfly/dataset.jsonl`) of input/output examples.
2. DSPy builds a signature from your prompt’s variables and compiles a few-shot module via `BootstrapFewShot`.
3. The best demonstrations are selected and appended as an `Examples:` section.
4. A new prompt version is saved automatically.

You provide quality examples; the tool selects the most effective ones.

---

## Development & Testing

```bash
# Run test suite (after setup)
./scripts/test_all.sh

# Or manually
source .venv/bin/activate
pytest -v --cov=promptterfly --cov-report=term-missing
```

Architecture and implementation details are in `docs/development.md`.

---

## Requirements

- Python 3.11+
- (optional) virtual environment tooling (`venv`)
- LLM provider API key for optimization (e.g., `OPENAI_API_KEY`)

---

## License

MIT
