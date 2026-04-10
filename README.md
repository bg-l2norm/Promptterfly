# Promptterfly

Promptterfly is your smart, easy-to-use, local prompt manager that automatically optimizes and versions your prompts.

## Quick Start

### 1. Install & Launch
```bash
./setup.sh
./start.sh
```

### 2. Configure Your LLM
Inside the terminal UI, type:
```
model add
```
Follow the simple interactive prompts to select a provider (OpenAI, Anthropic, Ollama, etc.) and enter your API key.

### 3. Create a Prompt
```
prompt create
```
Promptterfly will guide you. Use `{variables}` in your templates.

### 4. Improve a Prompt Automatically
If you have a vague prompt and want an LLM to automatically generate a highly optimized template for you, run:
```
auto generate "I want a prompt that summarizes text into bullet points"
```

If you already have a prompt created and a dataset with a few examples (`.promptterfly/dataset.jsonl`), run:
```
optimize improve <id>
```
Promptterfly will use DSPy behind the scenes to magically find the best few-shot examples and create a new version of your prompt.

### 5. Render
Test your prompt with variables using a JSON file:
```
prompt render <id> vars.json
```

## Features
- **Auto-prompt naming:** Lazily create prompts and the LLM will name them for you!
- **Auto-improve generation:** Ask for a prompt and a memory-less sub-agent will build, evaluate, and save the best one!
- **Budget Planning:** Set maximum cost/token budgets so your optimizations stay cheap.
- **Local Versioning:** No Git required! Every change creates a snapshot you can rollback to using `version history` and `version restore`.

Type `help` in the terminal for all commands. Enjoy!
