# Promptterfly Usage Guide

## Quick Tutorial

This tutorial walks you through the typical workflow: initializing a project, creating a prompt, optimizing it, and managing versions.

### 1. Initialize a Project

```bash
cd /path/to/your/project
promptterfly init
```

This creates a `.promptterfly/` directory with default configuration.

### 2. Create Your First Prompt

```bash
promptterfly prompt create
```

You'll be prompted interactively:

```
Name: Customer Support Greeting
Description: Greets a customer and asks how we can help
Tags: support, greeting
Template:
Hello {customer_name}! Thank you for contacting {company}. How can I assist you today?
(End with EOF or empty line)
```

A unique integer ID (e.g., 1) is generated and the prompt is saved.

### 3. List and View Prompts

```bash
promptterfly prompt list
promptterfly prompt show <prompt_id>
```

### 4. Render a Prompt with Variables

Create a JSON file with values for the template variables:

```json
{
  "customer_name": "Alice",
  "company": "Acme Inc"
}
```

Then run:

```bash
promptterfly render <prompt_id> vars.json
```

The prompt is rendered by substituting `{customer_name}` and `{company}` from the JSON.

**Note:** All variables used in the template must be present in the JSON; missing ones cause an error. Extra keys are ignored.

### 5. Optimize a Prompt

First, add at least one LLM model:

```bash
promptterfly model add openai-gpt4 --provider openai --model gpt-4 --api-key-env OPENAI_API_KEY
promptterfly model set-default openai-gpt4
```

Create a dataset of examples (`.promptterfly/dataset.jsonl`):

```json
{"input": "I have a question about billing", "completion": "I'd be happy to help with billing. Could you provide more details?"}
{"input": "My product arrived damaged", "completion": "I'm sorry to hear that. Let's process a replacement for you."}
```

Then run:

```bash
promptterfly optimize improve <prompt_id> --strategy few_shot
```

This creates a version snapshot, runs few-shot optimization using DSPy, and saves the optimized prompt as the new current version. A version history entry is recorded.

### 6. Manage Versions

View history:

```bash
promptterfly version history <prompt_id>
```

Restore an earlier version:

```bash
promptterfly version restore <prompt_id> <version_number>
```

### 7. Update and Delete Prompts

```bash
promptterfly prompt update <prompt_id>   # edit interactively
promptterfly prompt delete <prompt_id>   # with confirmation
```

---

## Commands Reference

### Initialization

```bash
promptterfly init [--path <dir>]
```
Creates `.promptterfly/` with default configuration in the current or specified directory.

### Prompt Management

```bash
promptterfly prompt list [--tag <tag>]
```
List all prompts in a Rich table.

```bash
promptterfly prompt show <id>
```
Display prompt template and metadata.

```bash
promptterfly prompt create
```
Interactive prompt creation (name, description, template, tags).

```bash
promptterfly prompt update <id>
```
Edit prompt fields interactively.

```bash
promptterfly prompt delete <id>
```
Remove a prompt (with confirmation).

```bash
promptterfly prompt render <id> <variables.json>
```
Render the prompt template with variables from a JSON file and print to stdout.

### Versioning

```bash
promptterfly version history <id>
```
List all versions with dates and messages.

```bash
promptterfly version restore <id> <version>
```
Restore prompt to a specific version (creates a new current version).

### Optimization

```bash
promptterfly optimize improve <id> [--strategy <strategy>]
```
Run optimization using the specified strategy (default: `few_shot`). Creates a new prompt version automatically.

### Model Management

```bash
promptterfly model list
```
List configured models.

```bash
promptterfly model add <name>
```
Interactive addition of a new model (provider, model name, API key env, temperature, etc.).

```bash
promptterfly model remove <name>
```
Remove a model from the registry.

```bash
promptterfly model set-default <name>
```
Set the default model for optimization and rendering.

### Configuration

```bash
promptterfly config show
```
Display current project configuration.

```bash
promptterfly config set <key> <value>
```
Update a configuration value.

---

## Storage Layout

All project-specific data is stored in `.promptterfly/`:

```
.promptterfly/
├── config.yaml           # Project configuration
├── models.yaml           # Model registry
├── counter               # Last used integer ID (simple persistence)
├── prompts/              # Current prompt states
│   └── <prompt_id>.json  # e.g., 1.json, 2.json
└── versions/             # Historical snapshots
    └── <prompt_id>/
        ├── 001.json
        ├── 002.json
        └── ...
```

Global configuration can be placed in `~/.promptterfly/config.yaml` and `~/.promptterfly/models.yaml`.

## Concepts

### Integer IDs

Each prompt is identified by a sequential integer (1, 2, 3...). IDs are assigned automatically using a counter stored in `.promptterfly/counter`. This makes IDs:

- **Stable**: Once assigned, never reused.
- **Simple**: Short numbers are easy to type and reference.
- **Predictable**: Useful for scripting and documentation.

You can see a prompt's ID in the `prompt list` output and use it in commands like `prompt show 5` or `optimize improve 12`.

### Variables and Rendering

Prompt templates use `{variable}` placeholders. At render time, you supply a JSON file mapping variable names to values.

**Example**:

Template:
```
Hello {customer_name}! Thank you for contacting {company}. How can we assist you today?
```

JSON:
```json
{
  "customer_name": "Alice",
  "company": "Acme Inc"
}
```

Render:
```bash
promptterfly render <id> vars.json
```

All required variables must be present; missing ones cause an error.

### Tags vs Description

- **Description** is a free-form summary of what the prompt does. It's for humans and appears in `prompt show`. Optional.
- **Tags** are short labels (e.g., `support`, `marketing`) used for organization and filtering. Multiple tags allowed; filter with `prompt list --tag <tag>`.

Use description for context and tags for quick lookup.

### Command Aliases (REPL)

The interactive REPL (`./start.sh`) supports aliases for faster typing:

- `ls` → `prompt list`
- `new` / `create` → `prompt create`
- `show <id>` → `prompt show <id>`
- `del` → `prompt delete`
- `run` → `prompt render`
- `hist` → `version history`
- `restore` → `version restore`
- `opt` → `optimize improve`
- `models` → `model list`
- `addmodel` → `model add`
- `setmodel` → `model set-default`

Type `help` inside the REPL to see the full list with explanations.

---

## Tips

- Use tags to organize prompts
- Auto-versioning is enabled by default; every create/update creates a version
- Optimization requires at least one model configured and working API keys for the provider
- Render output can be piped to files or other tools
- The dataset for optimization should be in JSONL format with input fields and a `completion` field