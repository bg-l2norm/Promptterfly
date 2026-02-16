# Promptterfly: Architecture & Project Structure

## Architecture Overview

Promptterfly is a local CLI tool for managing and optimizing prompts with simple versioning and model-based optimization. It's designed as a lightweight, terminal-first application with file-based persistence — no Git required.

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Interface (Typer)               │
├─────────────────────────────────────────────────────────────┤
│                     Command Handlers                       │
├─────────────────────────────────────────────────────────────┤
│  Prompt Service  │  Versioning  │  Optimization  │  Model  │
├─────────────────────────────────────────────────────────────┤
│           Storage Layer (Local JSON Files)                │
│              ┌─────────────────────────┐                  │
│              │  .promptterfly/         │                  │
│              │  ├── prompts/          │                  │
│              │  ├── versions/         │                  │
│              │  └── models.yaml       │                  │
│              └─────────────────────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

**Core Principles:**
- Local-first: All data stored in `.promptterfly/` (project-local) or `~/.promptterfly/` (global)
- Zero-config versioning: Automatic snapshots on every change (no Git knowledge needed)
- DSPy-powered: Use DSPy under the hood with a simple, intuitive CLI
- Low-effort UX: Few commands, sensible defaults, rich output

---

## Tech Stack

- **Python**: 3.11+
- **CLI**: Typer (simple subcommands, auto-help)
- **Validation**: Pydantic v2 (models + settings)
- **LLM Integration**: LiteLLM (unified provider API)
- **Optimization**: dspy (as a backend library, wrapped simply)
- **Terminal UI**: rich (tables, syntax highlighting)
- **Config**: YAML (PyYAML)
- **Packaging**: hatchling (or setuptools)

**Dependencies** (pyproject.toml):
```toml
dependencies = [
    "typer>=0.9.0",
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "rich>=13.0",
    "litellm>=2.0",
    "dspy>=2.0",
    "pyyaml>=6.0",
]
```

---

## Module Breakdown

```
src/promptterfly/
├── __init__.py
├── __main__.py
├── cli.py                       # Typer app
│
├── core/
│   ├── models.py                # Prompt, Version, ModelConfig, Config
│   ├── config.py                # Settings loader
│   └── exceptions.py
│
├── storage/
│   ├── prompt_store.py          # CRUD + auto-versioning
│   └── version_store.py         # List/restore versions
│
├── optimization/
│   ├── engine.py                # Thin dspy wrapper (compile, improve)
│   └── strategies.py            # Built-in strategies (few_shot, cot)
│
├── models/
│   ├── registry.py              # Model list/add/remove
│   └── client.py                # Unified LLM call wrapper
│
├── utils/
│   ├── io.py                    # Paths, file ops
│   └── tui.py                   # Rich helpers
│
└── commands/
    ├── prompt.py                # list, show, create, update, delete, render
    ├── version.py               # history, restore
    ├── optimize.py              # improve
    └── model.py                 # model add, list, remove, set-default
```

---

## Data Models (Pydantic v2)

```python
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    name: str
    provider: str = Field(..., description="openai, anthropic, etc.")
    model: str = Field(..., description="e.g. gpt-4, claude-3-opus")
    api_key_env: Optional[str] = Field(None, description="Env var name for API key")
    temperature: float = 0.7
    max_tokens: int = 1024


class Prompt(BaseModel):
    id: str                          # auto-generated UUID or short hash
    name: str
    description: Optional[str] = None
    template: str                    # {variables} formatting
    tags: List[str] = []
    created_at: datetime
    updated_at: datetime
    model_config: Optional[str] = None  # preferred model name
    metadata: Dict[str, Any] = {}


class Version(BaseModel):
    version: int                     # 1, 2, 3...
    prompt_id: str
    snapshot: Dict[str, Any]         # full Prompt model at that time
    message: Optional[str] = None
    created_at: datetime
    # Optimization-related (optional)
    strategy: Optional[str] = None
    metrics: Dict[str, float] = {}


class ProjectConfig(BaseModel):
    prompts_dir: Path = Path("prompts")
    auto_version: bool = True
    default_model: str = "gpt-3.5-turbo"
    optimization: Dict[str, Any] = {}
```

---

## CLI Command Structure

```bash
promptterfly
├── init [--path <dir>]            # Create .promptterfly/ + config
├── config                        # View/edit config
│
├── prompt
│   ├── list [--tag <tag>]        # Table of prompts
│   ├── show <id>                 # Template + metadata
│   ├── create                    # Interactive: name, template, tags
│   ├── update <id>               # Edit template/metadata
│   ├── delete <id>               # Remove prompt
│   └── render <id> <vars.json>   # Render with variables (stdout)
│
├── version
│   ├── history <id>              # List versions (v1, v2, dates, messages)
│   └── restore <id> <version>    # Restore prompt to a past version
│
├── optimize
│   └── improve <id> [--strategy <strategy>]  # Run optimization (few_shot)
│                                          # Creates new version automatically
│
└── model
    ├── list
    ├── add <name>                # Interactive: provider, model, api_key_env
    ├── remove <name>
    └── set-default <name>
```

**Simplified example:**
```bash
promptterfly init
promptterfly prompt create
promptterfly optimize improve my_prompt --strategy few_shot
promptterfly version history my_prompt
promptterfly version restore my_prompt 1   # rollback to v1
```

---

## Storage Layout

```
.project-root/
├── .promptterfly/
│   ├── config.yaml
│   ├── models.yaml
│   ├── prompts/
│   │   ├── <prompt_id>.json        # current state
│   │   └── versions/
│   │       └── <prompt_id>/
│   │           ├── 001.json         # Version snapshot (full Prompt model)
│   │           ├── 002.json
│   │           └── ...
│   └── index.json                  # optional: prompt_id → latest version
│
├── (project files)
└── README.md
```

**Versioning logic:**
- On `prompt create/update`: increment last version number, copy previous prompt JSON to `versions/<id>/N.json`, then write new current JSON. N is zero-padded (001, 002).
- `version history <id>`: list files in `versions/<id>/` sorted by number.
- `version restore <id> N`: copy `versions/<id>/N.json` to `prompts/<id>.json`.

No Git involved. Simple, reliable, file-based.

---

## Project Scaffold

```
shared_workspace/promptterfly/
├── pyproject.toml
├── README.md
├── LICENSE
├── .gitignore
│
├── src/promptterfly/
│   ├── __init__.py
│   ├── __main__.py
│   ├── cli.py
│   ├── core/
│   │   ├── models.py
│   │   ├── config.py
│   │   └── exceptions.py
│   ├── storage/
│   │   ├── prompt_store.py
│   │   └── version_store.py
│   ├── optimization/
│   │   ├── engine.py
│   │   └── strategies.py
│   ├── models/
│   │   ├── registry.py
│   │   └── client.py
│   ├── utils/
│   │   ├── io.py
│   │   └── tui.py
│   └── commands/
│       ├── prompt.py
│       ├── version.py
│       ├── optimize.py
│       └── model.py
│
├── tests/
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_storage.py
│   ├── test_optimization.py
│   └── test_cli.py
│
└── docs/
    ├── usage.md
    └── development.md
```

**Entry point:** `promptterfly = "promptterfly.cli:app"`

---

## Implementation Plan (by modules)

1. **Core & Config** (Day 1-2)
   - Pydantic models (Prompt, Version, ModelConfig, ProjectConfig)
   - Config loader/writer (YAML ↔ Pydantic)
   - Paths management (where to store .promptterfly)

2. **Storage Layer** (Day 3-4)
   - `prompt_store.py`: save/load prompt JSON, list prompts, auto-version snapshot function
   - `version_store.py`: list_versions(prompt_id), restore_version(prompt_id, version_number)
   - Ensure atomic writes (temp file + rename)

3. **CLI Foundations** (Day 5)
   - `cli.py` with Typer app + global config loading
   - `init` command: create .promptterfly/, write default config
   - `config` commands: show, set

4. **Prompt Commands** (Day 6)
   - `prompt list` (Rich table)
   - `prompt show <id>` (print template nicely)
   - `prompt create` (interactive via questionary or simple inputs)
   - `prompt update <id>` (edit fields)
   - `prompt delete <id>` (with confirmation)

5. **Version Commands** (Day 7)
   - `version history <id>`: pretty table of versions
   - `version restore <id> <version>`: copy snapshot back to current

6. **Model Registry** (Day 8-9)
   - `models.yaml` schema (list of ModelConfig)
   - `model add` (interactive), `list`, `remove`, `set-default`
   - `client.py`: unified `call_model(prompt, model_config)` using LiteLLM

7. **Optimization Engine** (Day 10-12)
   - `engine.py`: `optimize(prompt_id, strategy)` function
     - Load prompt and training examples (from a small built-in or user dataset)
     - Use dspy: define Signature, Module, and Teleprompter (BootstrapFewShot)
     - Return optimized prompt template
   - `optimize improve <id> --strategy few_shot` command:
     - Calls `engine.optimize()`
     - Creates new version with `strategy` recorded in metadata
   - Keep simple: default strategy = few_shot; no separate `evaluate` command (user will test manually)

8. **Polish & Defaults** (Day 13)
   - Make `prompt create/update` auto-version if `auto_version=true`
   - Error handling (missing IDs, invalid YAML, LLM API errors)
   - Provide helpful error messages
   - Add `--verbose` flag for debugging (optional)

9. **Testing** (Day 14)
   - Unit tests: storage mocks (temp dirs), model validation
   - CLI tests via `typer.testing.CliRunner` (no real LLM calls)
   - Integration test: create prompt, optimize, restore (mocking LLM to return a fixed improved prompt)
   - Ensure 80%+ coverage for core logic

---

## Rationale

**Local versioning over Git:**
- No Git knowledge needed; works everywhere
- Snapshots are cheap; no commit noise in project Git
- Restore is just file copy

**DSPy wrapper:**
- dspy is powerful but has a learning curve; `ptf optimize improve` hides complexity
- Users just call a single command; we handle signatures/teleprompters internally
- If they want custom strategies, they can extend via Python API (advanced)

**Single optimization command:**
- `evaluate` and `compare` removed to match requirement: "build it without errors, I will personally test"
- Delivers immediate value: one command to get an improved prompt
- Under the hood: uses a small demo dataset of few-shot examples appropriate to the task

**CLI minimalism:**
- Command count kept low
- Defaults chosen for 80% use-case
- Rich output for pleasant UX

---

## Success Criteria

- [ ] `promptterfly init` creates `.promptterfly/` with valid config
- [ ] `prompt create` stores JSON and auto-versions (if enabled)
- [ ] `prompt list` shows table (id, name, tags, updated)
- [ ] `optimize improve` returns a new prompt version (mocked LLM for tests, real in prod)
- [ ] `version restore` correctly rolls back prompt file
- [ ] All commands have `--help` and graceful error messages
- [ ] Tests pass; core logic >80% coverage

---

*This architecture prioritizes simplicity, immediate utility, and a gentle learning curve. The entire MVP should be implementable in ~2 weeks by one developer.*