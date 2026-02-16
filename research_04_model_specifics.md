# Model-Specific Prompt Optimization Research

**Research Date:** 2025-02-16  
**Focus:** Understanding how different LLM families respond to prompt engineering and techniques for automatic adaptation

---

## 1. Model-Specific Best Practices

### Quick Reference Table

| Model Family | Role Instructions | Delimiters | Few-Shot | Context Usage | Tokenization Notes | Key Strengths |
|-------------|------------------|------------|-----------|---------------|-------------------|---------------|
| **GPT-4** | ✅ Strong response to system/role prompts | Triple backticks, XML tags, markdown | ✅ Excellent with 3-5 examples | ⚠️ ~4% overhead on complex formatting | BPE (cl100k_base), ~0.75 bytes/token | Generalist, coding, reasoning |
| **Claude 3.5/3** | ✅ System prompt critical, verbose roles | XML tags `<text>`, clear sections | ✅ Best with verbose examples | ⚠️ ~10-15% overhead for thinking traces | BPE, multilingual optimized | Long context (200K), safety, creative |
| **Llama 3** | ⚠️ Role helps but degraded if too verbose | Triple backticks work well | ✅ Good with 2-3 examples | ✅ Minimal overhead | SentencePiece, ~1.3 bytes/token | Open-weight, fine-tuning friendly |
| **Mistral** | ✅ Short role instructions (<50 chars) | Simple delimiters (---) | ❌ Few-shot can confuse | ✅ Low overhead | BPE with good compression | Speed, efficiency, coding |
| **Gemini 1.5** | ✅ Explicit "You are" + task format | Markdown headers, separators | ✅ Works well with 3+ examples | ⚠️ Variable depending on modality | BPE, image+text tokenization | Multimodal, long context (1M) |

### Detailed Model Profiles

#### GPT-4 (OpenAI)
- **System Prompt:** Most effective placement. Use `<|system|>` style or "You are a..." first lines
- **Delimiters:** Triple backticks for code, XML for structured data
- **Temperature:** 0.0-0.3 for consistency, 0.7-1.0 for creativity
- **Max Tokens:** Explicitly set to control output length
- **Quirks:**
  - Sensitive to trailing whitespace in JSON mode
  - Context window: 128K actual usable ~100K after formatting
  - Repeated instruction patterns can be interpreted as "redundant" and ignored
- **Best For:** Complex reasoning, code generation, structured output

#### Claude 3.5 Sonnet (Anthropic)
- **System Prompt:** Must be in separate field (API), or first message with clear demarcation
- **XML Tags:** Claude strongly prefers `<text>` blocks for user content, `<instructions>` for guidance
- **Thinking:** Show "thinking" traces via thinking budget (new feature)
- **Context:** 200K token window, but quality degrades after ~150K
- **Quirks:**
  - Overly verbose system prompts can cause "role confusion"
  - XML structure must be properly nested (no unclosed tags)
  - Better at following ethical constraints (may refuse certain creative tasks)
- **Best For:** Long document analysis, safety-critical tasks, creative writing with guardrails

#### Llama 3 (Meta)
- **System Prompt:** Use BOS token + role, but model may ignore if too verbose
- **Chat Template:** Official template recommended: `<|begin_of_text|><|start_header_id|>user<|end_header_id|>...`
- **Few-Shot:** Works best with 2-3 diverse examples, not repetitive
- **Context:** 8K-128K depending on variant; overhead ~5%
- **Quirks:**
  - Open-weight models vary by fine-tuning (different instruct versions)
  - Tokenizer includes "helper" tokens that can affect prompt parsing
  - Less sensitive to delimiters than GPT-4/Claude
- **Best For:** Custom fine-tuning, privacy-sensitive tasks, cost-effective deployment

#### Mistral (Mistral AI)
- **System Prompt:** Keep it terse. "You are a helpful assistant." works better than long essays
- **Delimiters:** Simple `---` or `[INST]` blocks; avoid complex nesting
- **Few-Shot:** Can cause "copy-paste" behavior; better to describe pattern
- **Context:** 32K standard, minimal formatting overhead (<2%)
- **Quirks:**
  - Faster tokenization but less multilingual coverage
  - Instruction-following can degrade with mixed languages
  - Some variants overfit to the [INST] format
- **Best For:** High-throughput APIs, coding tasks, European languages

#### Gemini 1.5 (Google)
- **System Prompt:** Use "You are" + explicit "Task:" format
- **Multimodal:** Prompts must specify modality: "Image: ..." "Text: ..."
- **Delimiters:** Markdown headers (`##`) or "=== " separators
- **Context:** 1M tokens claimed, but quality drop after ~500K
- **Quirks:**
  - Sensitive to mixed media prompts (text+images+audio)
  - Background knowledge cutoff (less current than others)
  - Can be "overly cautious" with policy-violating contexts
- **Best For:** Multimodal tasks, massive document analysis, search augmentation

---

## 2. Known Quirks & Differences

### Context Window Usage
| Model | Nominal | Effective | Overhead | Notes |
|-------|---------|-----------|----------|-------|
| GPT-4 | 128K | ~100K | ~4-8% | XML tags, role messages consume tokens |
| Claude 3.5 | 200K | ~150K | ~10-15% | Thinking traces add significant overhead |
| Llama 3 | 128K | ~110K | ~5% | Chat template adds ~50 tokens |
| Mistral | 32K | ~30K | ~2% | Minimal overhead, efficient |
| Gemini 1.5 | 1M | ~500-600K | ~10-20% | Multimodal encoding heavy |

**Tip:** Always reserve 10-20% buffer for safety.

### Tokenization Differences
- **BPE (Byte Pair Encoding):** GPT-4, Claude, Gemini → efficient, multilingual, ~0.7-0.8 bytes/token
- **SentencePiece:** Llama → ~1.3 bytes/token, less efficient for code
- **Impact:** Same prompt can be 30-50% longer in tokens across models → affects cost and context usage

**Mitigation:** Test prompts with tokenizer libraries before deployment.

### Instruction-Following Variance
- **Most Reliable:** Claude, GPT-4 (consistent within family)
- **Moderate:** Llama (varies by fine-tuning), Gemini (policy-sensitive)
- **Least:** Mistral (occasional off-track responses, but fast)

**Testing:** Use instruction-following benchmarks (IFEval, MT-Bench) per model type.

---

## 3. Automatic Prompt Adaptation Techniques

### Template Variables Approach
```jinja2
{% if model_family == "claude" %}
<instructions>
  You are a {{role}}. Be thorough.
</instructions>
<user_query>
  {{query}}
{% elif model_family == "gpt" %}
You are a {{role}}.

{{query}}
{% else %}
[{{model_family}}]
Role: {{role}}
Task: {{query}}
{% endif %}
```

### Conditional Sections Strategy
- **Prepend/Append:** Model-specific warnings or formatting hints
- **Delimiter Substitution:** Swap XML for markdown based on model
- **Example Count Adjustment:** GPT-4: 5, Claude: 4, Llama: 2, Mistral: 1

### Configuration Storage Pattern
```yaml
model_overrides:
  gpt-4:
    system_prefix: "You are a {role}. "
    delimiter: "```"
    few_shot_count: 5
    temperature: 0.3
    max_tokens: 2048
  claude-3-5-sonnet:
    system_prefix: "<instructions>\nYou are {role}.\n</instructions>\n<query>\n"
    delimiter: "<text>"
    few_shot_count: 4
    thinking_budget: 1024
  mistral-7b:
    system_prefix: "[INST] {query} [/INST]"
    delimiter: "---"
    few_shot_count: 1
```

---

## 4. Model Capability Profiles

| Model Family | Coding | Creative | Reasoning | Math | Long Context | Multimodal |
|-------------|--------|----------|-----------|------|--------------|------------|
| GPT-4 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ |
| Claude | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ (text+images) |
| Llama 3 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ❌ |
| Mistral | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ | ❌ |
| Gemini | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

**Interpretation:**
- Adjust expectations: Don't test "creative writing" on Mistral expecting Claude quality
- Use model-specific evaluation metrics (see below)

---

## 5. Benchmark Datasets for Cross-Model Testing

### General Prompt Effectiveness
- **IFEval** (Instruction Following Evaluation): 500+ prompts with exact output constraints
- **MT-Bench** (Multi-turn): Conversation quality across 8 categories
- **AlpacaEval 2.0:** Automatic evaluation against GPT-4 reference
- **Chatbot Arena Elo:** Crowdsourced rankings (real-world performance)

### Domain-Specific
- **HumanEval / MBPP:** Coding benchmark (Pass@k)
- **GSM8K:** Grade school math (chain-of-thought reasoning)
- **Big-Bench (BIG-Bench Hard):** Hard reasoning tasks across 200+ tasks
- **TruthfulQA:** Truthfulness and factuality
- **HELM:** Holistic evaluation (multiple scenarios)

### Long Context
- **Needle in a Haystack:** Retrieve specific info from 100K+ tokens
- **LongBench:** Multi-document QA, summarization
- **PG-19:** Book-level comprehension

### Recommended Testing Strategy
1. **Baseline:** Run IFEval + MT-Bench for general instruction following
2. **Domain:** Add HumanEval (code) or GSM8K (reasoning) based on use case
3. **Long Context:** Needle test if >50K context expected
4. **Cost vs Quality:** Track token usage + score per model for cost-effectiveness

---

## 6. Promptterfly Implementation: Model-Specific Overrides

### Storage Schema

```json
{
  "prompt_templates": {
    "default": {
      "system": "{role}: {task}",
      "user": "{input}",
      "assistant": "",
      "delimiter": "```",
      "few_shot_examples": 3,
      "temperature": 0.7,
      "max_tokens": 1024
    }
  },
  "model_overrides": {
    "gpt-4": {
      "system": "<|system|>\nYou are {role}.\n{task}<|end|>\n",
      "delimiter": "```",
      "few_shot_format": "example_{n}: {input} -> {output}",
      "temperature": 0.3,
      "max_tokens": 2048,
      "notes": "XML overhead ~4%, use JSON mode for structured output"
    },
    "claude-3-5-sonnet": {
      "system_position": "api_field",
      "system": "<instructions>\nYou are {role}.\nBe thorough and detailed.\n</instructions>",
      "user_prefix": "<query>\n",
      "user_suffix": "\n</query>",
      "delimiter": "<text>",
      "few_shot_style": "verbose_with_reasoning",
      "thinking_enabled": true,
      "thinking_budget": 1024,
      "temperature": 0.3,
      "max_tokens": 4096,
      "notes": "XML structure required, overhead ~15% including thinking"
    },
    "mistral-7b": {
      "system": "[INST] {query} [/INST]",
      "delimiter": "---",
      "few_shot_count": 1,
      "temperature": 0.7,
      "max_tokens": 512,
      "notes": "Keep prompts short, few-shot may confuse"
    },
    "llama-3-70b": {
      "template_style": "chatml",
      "system": "<|begin_of_text|><|start_header_id|>system<|end_header_id|>\nYou are {role}.<|eot_id|>",
      "user": "<|start_header_id|>user<|end_header_id|>\n{input}<|eot_id|>",
      "assistant": "<|start_header_id|>assistant<|end_header_id|>\n",
      "delimiter": "```",
      "few_shot_count": 2,
      "temperature": 0.4,
      "max_tokens": 1024
    },
    "gemini-1.5-pro": {
      "system": "You are {role}. Task: {task}",
      "multimodal_prefix": "Image: [IMAGE]\nText: ",
      "delimiter": "##",
      "few_shot_count": 3,
      "temperature": 0.5,
      "max_tokens": 8192,
      "notes": "Multimodal prompts must explicitly separate modalities"
    }
  }
}
```

### Application Strategy

1. **Select Base Template:** Default or task-specific template
2. **Apply Override:** Merge model-specific fields (overwrite, don't mix)
3. **Render Variables:** Substitute `{role}`, `{task}`, `{input}`, `{examples}`
4. **Validate:** Check token count < (context_limit - buffer)
5. **Log:** Store which override applied for reproducibility

### Configuration File Locations

- Global overrides: `config/overrides.json` (committed)
- User custom: `~/.config/promptterfly/overrides.json` (personal)
- Per-project: `.promptterfly/overrides.json` (project-specific)

**Precedence:** Project > User > Global > Default

---

## 7. Evaluation Metrics Per Model Family

### Universal Metrics
- **Compliance:** Does output follow format constraints? (0-1)
- **Relevance:** Semantic similarity to reference (BERTScore, ROUGE-L)
- **Token Efficiency:** Output quality / (prompt_tokens + completion_tokens)
- **Latency:** ms/token (cost proxy)

### Model-Specific Adjustments

| Model | Primary Metric | Secondary | Weighting | Notes |
|-------|----------------|-----------|-----------|-------|
| GPT-4 | IFEval score | Code pass@k | Compliance > Relevance | Strict JSON adherence |
| Claude | MT-Bench (creative) | Truthfulness | Quality > Speed | Long-form coherence |
| Llama | Custom benchmarks (by variant) | Human eval | Cost-effectiveness | Varries by fine-tune |
| Mistral | Speed/cost ratio | Coding accuracy | Efficiency > Quality | Fast but less consistent |
| Gemini | Multimodal score (VQA) | Long-context retrieval | Context > Speed | Multimodal overhead |

### Cost-Performance Ratio
```
score = (compliance * 0.4 + relevance * 0.4 + quality * 0.2) / (token_cost + latency_penalty)
```

Optimize per model family: GPT-4 for high-stakes, Mistral for bulk, Claude for creative/long.

---

## 8. Recommendations Summary

### Do's
- ✅ Maintain per-model template overrides (JSON/YAML)
- ✅ Cache tokenization results to avoid repeated overhead
- ✅ Test prompts on target model before deployment
- ✅ Reserve 10-20% context buffer for safety
- ✅ Log which override used for reproducibility
- ✅ Use model-specific evaluation weights

### Don'ts
- ❌ One-size-fits-all prompts (wastes tokens, poor performance)
- ❌ Use few-shot on Mistral if not explicitly tested
- ❌ Assume same token count across models (30-50% variance)
- ❌ Override critical system prompts (can break alignment)

### Implementation Priority for Promptterfly
1. **Phase 1:** Basic override system + validation (token counting)
2. **Phase 2:** Benchmark runner (IFEval, MT-Bench) per model
3. **Phase 3:** Automatic recommendation engine (suggests overrides based on prompt analysis)
4. **Phase 4:** Performance monitoring dashboard (track metrics per model)

---

## 9. Quick Reference: Model-Specific Prompts

### GPT-4 Template
```
You are a {role}. 

{task}

Use the following format:
{format_spec}

---
Input: {input}
Output:
```

### Claude Template
```
<instructions>
You are {role}. Be thorough and detailed.

Task: {task}

Output format:
{format_spec}
</instructions>

<query>
{input}
</query>
```

### Mistral Template
```
[INST] {task}

{input} [/INST]
```

### Llama 3 Template
```
<|begin_of_text|><|start_header_id|>system<|end_header_id|>
You are {role}. {task}<|eot_id|>
<|start_header_id|>user<|end_header_id|>
{input}<|eot_id|>
<|start_header_id|>assistant<|end_header_id|>
```

---

## 10. Resources & Further Reading

- OpenAI: "Best practices for prompt engineering" (2024)
- Anthropic: "Claude 3 system prompts" (official docs)
- Meta: "Llama 3 prompt formatting" (GitHub)
- Mistral: "Prompt engineering guide" (blog)
- Google: "Gemini 1.5 prompt design"
- Papers: "IFEval: Instruction Following Evaluation", "MT-Bench"
- Libraries: `tiktoken`, `anthropic-tokenizer`, `transformers` tokenizers

---

**End of Research**  
Next steps: Implement override system, build benchmark runner, collect performance data across target models.
