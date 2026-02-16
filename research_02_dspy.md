# DSPy Framework Research Report
**For Promptterfly Integration** | Date: 2025-02-16

---

## Executive Summary

DSPy (Demonstrate, Search, Predict) is a Stanford-developed framework for **programmatic prompt optimization** that treats LLM pipelines as compilable programs rather than static prompt strings. It separates LM instructions from the code logic, enabling automatic optimization of prompts based on task performance metrics. For Promptterfly, DSPy offers a sophisticated backend for intelligent prompt management that goes beyond static templates to adaptive, self-improving prompt strategies.

**Key Value Proposition**: Instead of manually tuning prompts, DSPy compiles your pipeline to generate optimal prompts for specific tasks and models, validated against your examples and metrics.

---

## 1. DSPy Core Concepts

### 1.1 Signatures

Signatures define the **input/output schema** for LM calls in a declarative, type-safe way. They are the contract between your code and the LM.

```python
import dspy

class Summarize(dspy.Signature):
    """Summarize text into key points."""
    doc = dspy.InputField(prefix="Document:", desc="Text to summarize")
    summary = dspy.OutputField(prefix="Summary:", desc="3-5 bullet points")
```

**Key Features**:
- Field-level prefixes and descriptions guide the LM
- Optional `desc` provides semantic guidance
- Supports single or multiple inputs/outputs
- Enforces validation and parsing via `dspy.Ensure` constraints

### 1.2 Modules

Modules are **reusable, composable building blocks** that implement signatures. Each module encapsulates a specific LM interaction pattern.

**Pre-built Modules**:
- `dspy.ChainOfThought` - Reasoning with step-by-step thought
- `dspy.ProgramOfThought` - Code-based reasoning
- `dspy.ReAct` - Tool-use reasoning
- `dspy.MultiChainComparison` - Multiple reasoning paths, pick best
- `dspy.Retrieve` - RAG retrieval + reasoning
- `dspy.Transform` - General-purpose text transformation

**Custom Modules**:
```python
class Rewrite(dspy.Module):
    def __init__(self):
        super().__init__()
        self.generate = dspy.ChainOfThought(RewriteSignature)
    
    def forward(self, text, style):
        return self.generate(text=text, style=style)
```

### 1.3 Teleprompters (Optimizers)

Teleprompters are **optimization algorithms** that tune module prompts based on labeled examples and a metric. They are the "brain" that improves your pipeline.

**Available Teleprompters**:
- `dspy.BootstrapFewShot` - Automatic few-shot example selection (most common)
- `dspy.BootstrapFewShotWithRandomSearch` - Few-shot + prompt variation search
- `dspy.BayesianSignatureOptimizer` - Optimizes signature descriptions
- `dspy.MIPRO` - Instruction prompt optimization (gradient-free)
- `dspy.BayesianOptimization` - Parameter optimization with Gaussian Processes
- `dspy.GRPO` / `dspy.ReLAA` - Reinforcement learning approaches

**How Teleprompters Work**:
1. Take your module(s) and a `Trainset` (labeled examples)
2. Evaluate baseline performance using a `metric` function
3. Iteratively propose prompt changes (examples, instructions, formatting)
4. Validate on trainset/onspontsets and keep best version
5. Output a **compiled** module with optimized prompt

---

## 2. How DSPy Optimizes Prompts

### 2.1 The Compilation Process

```python
# Define pipeline
class RAGPipeline(dspy.Module):
    def __init__(self):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=5)
        self.generate = dspy.ChainOfThought(AnswerSignature)
    
    def forward(self, question):
        context = self.retrieve(question).passages
        return self.generate(question=question, context=context)

# Prepare data
trainset = [...]  # List of Example objects with gold answers
metric = lambda pred, gold: ...  # Score 0-1

# Optimize with teleprompter
teleprompter = dspy.BootstrapFewShot(metric=metric, max_bootstrapped_demos=4)
compiled_rag = teleprompter.compile(RAGPipeline(), trainset, valset=None)
```

**What Gets Optimized**:

1. **Demo Selection** (BootstrapFewShot):
   - Chooses which few-shot examples to include
   - Selects diverse, high-performing examples
   - Formats them as in-context learning shots

2. **Instruction Tuning** (MIPRO, BayesianSignatureOptimizer):
   - Optimizes signature field descriptions
   - Replaces generic prompts with task-specific wording
   - A/B tests instruction variations

3. **Chain Formatting** (CoT, MultiChain):
   - Optimizes thought delimiter syntax
   - Adjusts step-by-step prompting structure
   - Tunes temperature and sampling parameters per call

4. **Multi-module Coordination**:
   - For pipelines, optimizes the prompt at each stage
   - Balances module interactions
   - Propagates gradient-free signal across stages

### 2.2 Metrics-Driven Optimization

The **metric function** is central. It's a Python function that scores predictions against gold answers:

```python
def metric_qa(pred, gold, passage_match_threshold=0.85):
    score = 0
    # Exact match for answers
    if pred.answer.lower().strip() == gold.answer.lower().strip():
        score = 1.0
    # Optional: semantic similarity for fuzzy matches
    elif similarity(pred.answer, gold.answer) > passage_match_threshold:
        score = 0.5
    return score
```

Metrics can combine multiple criteria (accuracy, faithfulness, latency penalization).

---

## 3. Data Requirements

### 3.1 Example Format

DSPy uses `dspy.Example` objects with arbitrary fields matching signature inputs/outputs:

```python
from dspy import Example

train_examples = [
    Example(
        question="What is the capital of France?",
        context=["France is a country in Europe. Its capital is Paris."],
        answer="Paris"
    ).with_inputs("question", "context"),
    Example(
        question="Explain photosynthesis",
        context=["Photosynthesis converts sunlight to glucose..."],
        answer="Photosynthesis is the process by which plants convert light energy..."
    ).with_inputs("question", "context")
]
```

**Requirements**:
- Inputs must match signature input field names
- Gold outputs must match signature output field names
- Can include metadata fields not in signature (ignored during compile)
- `.with_inputs(*field_names)` marks which fields are inputs (rest are outputs/labels)

### 3.2 Dataset Splits

```python
trainset = examples[:50]      # Used for optimization
valset = examples[50:70]     # Validation during early stopping
testset = examples[70:]      # Held-out for final evaluation (not used in compile)
```

**Size Guidelines**:
- Few-shot selection (Bootstrap): 20–100 examples sufficient
- MIPRO/Bayesian: 50–500 examples recommended
- Smaller datasets risk overfitting; larger improves generalization

### 3.3 Metric Design

The metric function signature:

```python
def metric(example: dspy.Example, prediction: dspy.Prediction, trace: Any = None) -> float:
    """
    Returns score in [0, 1] range. Higher is better.
    - example: the gold Example
    - prediction: module forward() output (dict-like or typed object)
    - trace: intermediate steps info (optional)
    """
    return score
```

**Best Practices**:
- Return float in [0, 1] for optimizer compatibility
- Include multiple dimensions if needed (e.g., accuracy + BLEU)
- Cache expensive computations (embeddings, API calls) for speed
- Consider `dspy.evaluate` for built-in metrics (e.g., `dspy.evaluate.qa_exact_match`)

---

## 4. Persistence and Versioning of Optimized Prompts

### 4.1 Serialization

DSPy compiled modules can be **saved and loaded**:

```python
# Save compiled module
compiled_rag.save("compiled_rag.json")

# Load in another session
from dspy import Predict
loaded = dspy.load("compiled_rag.json", module=RAGPipeline())
```

**What Gets Saved**:
- Optimized module parameters (selected demos, instructions)
- LM hyperparameters (temperature, top_p, max_tokens) if set
- Signature metadata
- Does NOT save the LM itself (requires reinitialization)

### 4.2 Versioning Strategy

Promptterfly should implement:

1. **Artifact Storage**:
```
promptterfly/
├── compiled_modules/
│   ├── rag_pipeline/
│   │   ├── v1.0.0.json
│   │   ├── v1.1.0.json
│   │   └── current -> v1.1.0.json
│   └── summarizer/
│       └── v2.3.1.json
├── datasets/
│   ├── trainset_rag_20250216.jsonl
│   └── trainset_summarizer_20250216.jsonl
├── metrics/
│   ├── metric_qa.py
│   └── metric_summarization.py
└── metadata/
    └── config_20250216.yaml  # LM settings, optimizer params
```

2. **Git-Based Tracking**:
- Commit compiled JSON + source code + dataset snapshot + config
- Tag releases: `dspy-v1.2.0-rag`
- Enables rollback and diffing of prompt changes

3. **Metadata Logging**:
```yaml
compiled_at: "2025-02-16T12:43:00Z"
optimizer: "BootstrapFewShot"
trainset_size: 125
train_metric: 0.87
val_metric: 0.82
lm: "openai/gpt-4o"
temperature: 0.7
```

4. **Reproducibility Script**:
```python
# reproduce.py
import dspy
from my_module import MyPipeline
from metric import my_metric

module = MyPipeline()
compiled = dspy.load("v1.2.0.json", module=module)
print(compiled)  # Ready to use
```

---

## 5. Integration Architecture for Promptterfly

### 5.1 High-Level Architecture

```
┌─────────────────┐
│   Promptterfly  │  User Interface (CLI/GUI)
│   Frontend      │ - Define signatures
└────────┬────────┘ - Write module code
         │           - Upload examples
         │           - Select optimizer
         │           - Trigger compile
         ▼
┌─────────────────┐
│  Compilation    │  Orchestration Layer
│  Service        │ - Accepts compile request
└────────┬────────┘ - Loads user code + dataset
         │           - Instantiates optimizer
         │           - Runs optimization
         │           - Saves compiled artifact
         │           - Stores metadata
         ▼
┌─────────────────┐
│   DSPy Core     │  Actual optimization
│   Runtime       │ - Module evaluation
└─────────────────┘ - Teleprompter iterations
```

### 5.2 API Surface Design

#### REST-ish Endpoints (if web service)

```http
POST /api/v1/compile
{
  "pipeline_id": "rag_qa",
  "code_path": "/workspace/pipelines/rag.py",
  "trainset_path": "/datasets/rag_train.jsonl",
  "metric_path": "/metrics/qa.py",
  "optimizer": {
    "type": "BootstrapFewShot",
    "config": {
      "max_bootstrapped_demos": 4,
      "max_labeled_demos": 20
    }
  },
  "lm_config": {
    "model": "gpt-4o",
    "temperature": 0.0,
    "max_tokens": 1000
  }
}
→ 202 Accepted + job_id

GET /api/v1/compile/{job_id}
→ {"status": "running|succeeded|failed", "artifact_path": "...", "metric_score": 0.87}

GET /api/v1/pipelines/{pipeline_id}/versions
→ [{"version": "1.2.0", "created_at": "...", "train_metric": 0.87}]

POST /api/v1/pipelines/{pipeline_id}/deploy
{"version": "1.2.0"}  # Set as active
```

#### Python API (Library Mode)

```python
import promptterfly as ptf

# 1. Register LM (once per session)
lm = dspy.LM(model="openai/gpt-4o", api_key="...")
dspy.settings.configure(lm=lm)

# 2. Define or load module
from my_pipelines import RAGPipeline
pipeline = RAGPipeline()

# 3. Load dataset
trainset = dspy.load_train_jsonl("trainset.jsonl", MySignature)

# 4. Compile
compiler = ptf.Compiler(
    optimizer="BootstrapFewShot",
    metric="metrics.qa_exact_match",
    max_epochs=3,
    num_candidates=50
)
result = compiler.compile(
    pipeline,
    trainset=trainset,
    valsetsize=0.2
)

# 5. Deploy
ptf.deploy(result, pipeline_id="rag_qa", version="1.2.0")
```

#### CLI Commands

```bash
# Initialize project
ptf init --template python

# Define signature (interactive wizard)
ptf signature create QuestionAnswering

# Add training examples
ptf examples import trainset.jsonl --signature QuestionAnswering

# Run optimization
ptf compile run rag_pipeline \
  --optimizer BootstrapFewShot \
  --metric metrics.qa_exact_match \
  --lm openai/gpt-4o \
  --output compiled/rag_v1.json

# List versions
ptf versions list rag_pipeline

# Deploy
ptf deploy rag_pipeline --version 1.2.0 --target production
```

### 5.3 Storage Layer

**SQLite/PostgreSQL Schema**:

```sql
--pipelines
id | name | code_path | signature_class | created_at

--compiled_versions
id | pipeline_id | version | artifact_path | trainset_hash | metric_score | metadata | compiled_at

--datasets
id | pipeline_id | split | examples_jsonl | hash | created_at

--optimizer_runs
id | version_id | optimizer_type | config | status | logs_path | duration_sec
```

**File System Layout**:

```
shared_workspace/promptterfly/
├── projects/
│   ├── rag_qa/
│   │   ├── pipeline.py         # User-defined Module
│   │   ├── signature.py        # Signature classes
│   │   ├── metric.py           # Scoring function
│   │   └── config.yaml         # LM + optimizer defaults
│   └── summarization/
├── data/
│   ├── trainsets/
│   │   ├── rag_qa_20250216.jsonl
│   │   └── summarization_20250216.jsonl
│   └── validation/
├── compiled/
│   ├── rag_qa/
│   │   ├── v1.0.0.json
│   │   ├── v1.1.0.json
│   │   └── current.json -> v1.1.0.json
│   └── summarization/
├── metrics/
│   ├── qa.py
│   └── summarization.py
├── logs/
│   └── compile_20250216_1243.log
└── registry.db  # SQLite metadata store
```

---

## 6. Example Workflow

### 6.1 End-to-End: RAG Q&A Optimization

**Step 1: Define Signature**

```python
# projects/rag_qa/signature.py
import dspy

class RAGAnswer(dspy.Signature):
    """Answer question based on retrieved context."""
    question = dspy.InputField(prefix="Question:", desc="User query")
    context = dspy.InputField(prefix="Context:", desc="Retrieved passages")
    answer = dspy.OutputField(prefix="Answer:", desc="Concise answer with citation")
    confidence = dspy.OutputField(prefix="Confidence:", desc="0-1 score")
```

**Step 2: Define Pipeline Module**

```python
# projects/rag_qa/pipeline.py
import dspy
from .signature import RAGAnswer

class RAGPipeline(dspy.Module):
    def __init__(self, retrieve_k=5):
        super().__init__()
        self.retrieve = dspy.Retrieve(k=retrieve_k)
        self.generate = dspy.ChainOfThought(RAGAnswer)
    
    def forward(self, question):
        # Step 1: Retrieve
        retrieval_result = self.retrieve(question)
        context = retrieval_result.passages
        
        # Step 2: Generate with CoT
        prediction = self.generate(question=question, context=context)
        return prediction
```

**Step 3: Prepare Trainset**

```jsonl
{"question": "Who wrote 1984?", "context": ["George Orwell wrote 1984..."], "answer": "George Orwell"}
{"question": "What is photosynthesis?", "context": ["Photosynthesis converts sunlight..."], "answer": "Photosynthesis is the process by which plants convert light energy into chemical energy."}
```

**Step 4: Define Metric**

```python
# metrics/qa.py
import dspy
from sentence_transformers import SentenceTransformer, util

model = SentenceTransformer('all-MiniLM-L6-v2')

def qa_metric(example, prediction, trace=None):
    # Exact match
    exact = float(prediction.answer.lower().strip() == example.answer.lower().strip())
    
    # Semantic similarity fallback
    if exact < 1.0:
        emb1 = model.encode(prediction.answer)
        emb2 = model.encode(example.answer)
        sim = util.cos_sim(emb1, emb2).item()
        return max(exact, sim)
    return exact
```

**Step 5: Compile**

```python
# compile.py
import dspy
from projects.rag_qa.pipeline import RAGPipeline
from metrics.qa import qa_metric
from dspy.datasets import load_dataset

# Load data
trainset = load_dataset("data/trainsets/rag_qa_20250216.jsonl", RAGAnswer)

# Configure LM
dspy.settings.configure(lm=dspy.LM(model="openai/gpt-4o", temperature=0.0))

# Optimize
teleprompter = dspy.BootstrapFewShot(metric=qa_metric, max_bootstrapped_demos=4)
compiled_pipeline = teleprompter.compile(RAGPipeline(), trainset=trainset)

# Save
compiled_pipeline.save("compiled/rag_qa/v1.1.0.json")
```

**Step 6: Use Compiled Pipeline**

```python
# inference.py
import dspy
from projects.rag_qa.pipeline import RAGPipeline

# Load LM
dspy.settings.configure(lm=dspy.LM(model="openai/gpt-4o"))

# Load compiled
compiled = dspy.load("compiled/rag_qa/v1.1.0.json", module=RAGPipeline())

# Predict
result = compiled(question="What is the capital of Japan?")
print(result.answer, result.confidence)
```

---

## 7. Limitations and Compatibility

### 7.1 LLM Provider Compatibility

**Supported Providers** (via DSPy's LM abstraction):

| Provider | Models | Setup |
|----------|--------|-------|
| OpenAI | gpt-4, gpt-4o, gpt-3.5-turbo | `dspy.LM("openai/gpt-4o")` |
| Anthropic | Claude 3.5 Sonnet, Opus | `dspy.LM("anthropic/claude-3-5-sonnet-20241022")` |
| Cohere | Command, Command R+ | `dspy.LM("cohere/command-r-plus")` |
| Google | Gemini Pro, Gemini Flash | `dspy.LM("google/gemini-1.5-pro")` |
| Together AI | Llama 2/3, Mixtral, etc. | `dspy.LM("together_ai/meta-llama/Llama-3-70b-chat-hf")` |
| Groq | Llama 3, Mixtral (ultra-fast) | `dspy.LM("groq/llama3-70b-8192")` |
| Local (vLLM/Ollama) | Any HuggingFace model | `dspy.LM("ollama/llama2")` |
| Azure OpenAI | GPT models on Azure | `dspy.LM("azure/gpt-4o", api_key=..., ...)` |

**Key Points**:
- DSPy uses langchain under the hood for provider abstraction
- API keys set via environment variables or pass to `dspy.LM()`
- Model names follow pattern: `provider/model_name`
- Streaming not yet fully supported in all optimizers
- Cost: Optimization runs many LM calls (trainset × iterations × candidates)

### 7.2 Performance Limitations

1. **Optimization Cost**:
   - BootstrapFewShot: ~ O(num_examples × num_candidates) LM calls
   - MIPRO: ~ O(num_examples × num_prompts × num_steps)
   - Can cost $50–$500+ depending on trainset size and optimizer
   - **Mitigation**: Use small, high-quality trainsets; early stopping; cheap models during optimization

2. **Latency**:
   - Compiled modules may add retrieval or multi-step overhead
   - Not suitable for sub-100ms requirements
   - **Mitigation**: Cache results, pre-retrieve, simplify modules

3. **Memory Footprint**:
   - Large demos (few-shot examples) can consume context window
   - Multi-module pipelines increase memory per call
   - **Mitigation**: Limit `max_bootstrapped_demos`, truncate contexts

4. **Determinism**:
   - Stochastic LMs (temperature > 0) introduce variance in optimization
   - Same trainset may yield different compiled prompts across runs
   - **Mitigation**: Set temperature=0 for optimization, use fixed seeds

### 7.3 Design Constraints

- **Signature fields must match exactly** between dataset and module
- **Teleprompters only optimize discrete choices** (which demos, which wording)
- Cannot change model weights (no fine-tuning)
- Limited to prompt engineering + few-shot selection
- **No continuous learning**: Must retrain from scratch for new data
- **Module composition depth**: >5 stages becomes expensive/hard to optimize

### 7.4 Known Issues

- **MIPRO optimization** can be unstable with small datasets (<50 examples)
- **Bayesian optimizers** require ≥100 examples for reliable search
- **Custom modules** must implement `.forward()` correctly; errors propagate silently
- **Multi-modal LMs** (vision) support is experimental
- **Async inference** not natively supported (can wrap but not optimized)

---

## 8. API Surface Design for Promptterfly

### 8.1 Minimal Viable API

```python
# core.py - simplified interface for end users

class Promptterfly:
    def __init__(self, project_root: str):
        self.project = Project(project_root)  # Load config, code, signatures
    
    def compile(self, pipeline_name: str, trainset_path: str,
                optimizer: str = "BootstrapFewShot",
                metric: str = None,
                lm_config: dict = None) -> CompilationResult:
        """
        Optimize a pipeline using DSPy.
        
        Args:
            pipeline_name: Name of pipeline module to compile
            trainset_path: JSONL path with examples
            optimizer: Type of teleprompter
            metric: Import path to metric function
            lm_config: Dict with 'model', 'temperature', 'api_key'
        
        Returns:
            CompilationResult with artifact_path, metric_score
        """
        ...
    
    def list_versions(self, pipeline_name: str) -> List[Version]:
        ...
    
    def deploy(self, pipeline_name: str, version: str) -> Deployment:
        ...
    
    def predict(self, pipeline_name: str, inputs: dict, version: str = "current") -> dict:
        ...
```

### 8.2 Advanced Features (Phase 2)

- **A/B Testing**: Deploy multiple versions, split traffic, compare metrics
- **Auto-retraining**: Trigger recompile when new data arrives (cron/webhook)
- **Metric Dashboard**: Track version performance over time
- **Prompt Diff**: Compare prompt templates between versions
- **Explainability**: Show which demos were selected and why
- **Cost Monitoring**: Track LM spend per compilation
- **Multi-model Optimization**: Find prompts that work across LMs

---

## 9. Key References

### Official Documentation
- **DSPy GitHub**: https://github.com/stanfordnlp/dspy
- **Documentation**: https://dspy-docs.vercel.app/
- **Examples Gallery**: https://github.com/stanfordnlp/dspy/tree/main/examples
- **Paper (ICLR 2024)**: https://arxiv.org/abs/2310.07089

### Critical Examples
- **Basic Optimization**: `examples/quickstart/BootstrapFewShot.py`
- **RAG Pipeline**: `examples/RAG/rag_optimization.py`
- **MIPRO**: `examples/prompt_optimization/MIPRO.py`
- **Multi-Module**: `examples/composition/qa_pipeline.py`
- **Metrics**: `dspy/evaluate/evaluate.py`

### Community Resources
- **DSPy Discord**: https://discord.gg/7V8fZJCq
- **Blog Post (StepFun)**: https://step.fm/teams/dspy
- **YouTube Tutorials**: Stanford NLP channel demos

---

## 10. Recommendations for Promptterfly

### 10.1 Phase 1: MVP (Weeks 1–4)

1. **Set up DSPy sandbox** with OpenAI key
2. **Implement basic compile** for single-module pipelines using `BootstrapFewShot`
3. **Build dataset import** from JSONL
4. **Implement save/load** with versioning folder structure
5. **CLI wrapper** with `ptf compile` command

**Deliverable**: `ptf compile run my_pipeline --trainset data.jsonl --optimizer BootstrapFewShot`

### 10.2 Phase 2: Enhanced Features (Weeks 5–8)

1. **Web UI**: Upload examples, visualize compiled prompt
2. **Multi-optimizer support**: MIPRO, BayesianSignatureOptimizer
3. **Metric registry**: Pre-built metrics for QA, summarization, classification
4. **Git integration**: Auto-commit compiled artifacts
5. **Deployment target**: HTTP endpoint that loads compiled module

**Deliverable**: Web dashboard for managing pipelines + quick deploy

### 10.3 Phase 3: Productionization (Weeks 9–12)

1. **Cost tracking**: LM call budget per optimization
2. **A/B testing framework**: Traffic splitting, statistical significance
3. **Explainability pane**: Show selected demos, instruction diffs
4. **CI/CD integration**: Auto-retrain on PR merge when dataset changes
5. **Monitoring**: Latency, error rate, metric drift per version

**Deliverable**: Production-ready Promptterfly with observability

### 10.4 Technology Stack Suggestions

- **Backend**: Python 3.10+, FastAPI (REST), Celery (async compile jobs)
- **Storage**: SQLite (dev) → PostgreSQL (prod), S3-compatible (artifacts)
- **Frontend**: React + Tailwind or Streamlit (internal rapid UI)
- **Queue**: Redis + Celery or RabbitMQ
- **Monitoring**: Prometheus + Grafana dashboards
- **Git**: All source code + compiled artifacts tracked

---

## 11. Conclusion

DSPy provides a **rigorous, automated approach** to prompt engineering that aligns perfectly with Promptterfly's vision of a systematic prompt management system. By treating prompts as compiled artifacts rather than static text strings, Promptterfly can offer:

- **Versioned, reproducible optimizations**
- **Data-driven prompt selection** (no more manual tweaking)
- **Multi-LLM compatibility** through provider abstraction
- **Self-improving pipelines** that adapt to new examples

**Key Integration Challenge**: DSPy's runtime requires the original Python module code + signatures; Promptterfly must store not just the compiled prompt but also the code that defines the pipeline structure. This is a feature, not a bug—it ensures that changes to signature/field names are tracked.

**Next Step**: Start with a simple BootstrapFewShot implementation to prove end-to-end flow, then expand to MIPRO and multi-module pipelines.

---

*Report generated: 2025-02-16 | Based on DSPy v0.4+ (current as of early 2025)*
