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

A unique ID is generated and the prompt is saved.

### 3. List and View Prompts

```bash
promptterfly prompt list
promptterfly prompt show <prompt_id>
```

### 4. Render a Prompt with Variables

```bash
echo '{"customer_name": "Alice", "company": "Acme Inc"}' > vars.json
promptterfly render <prompt_id> vars.json
```

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
├── prompts/              # Current prompt states
│   └── <prompt_id>.json
└── versions/             # Historical snapshots
    └── <prompt_id>/
        ├── 001.json
        ├── 002.json
        └── ...
```

Global configuration can be placed in `~/.promptterfly/config.yaml` and `~/.promptterfly/models.yaml`.

## Tips

- Use tags to organize prompts
- Auto-versioning is enabled by default; every create/update creates a version
- Optimization requires at least one model configured and working API keys for the provider
- Render output can be piped to files or other tools
- The dataset for optimization should be in JSONL format with input fields and a `completion` field
