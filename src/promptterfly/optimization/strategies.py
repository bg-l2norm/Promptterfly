"""Built-in optimization strategies."""
import dspy
from typing import List, Dict, Any, Type
from ..core.models import Prompt, ModelConfig


def few_shot(prompt: Prompt, dataset: List[Dict[str, Any]], model_cfg: ModelConfig) -> str:
    """
    Optimize a prompt using few-shot learning with DSPy.

    Args:
        prompt: The original Prompt object with template.
        dataset: List of example dictionaries, each containing input fields and 'completion'.
        model_cfg: Model configuration for DSPy LM.

    Returns:
        An optimized prompt template string with in-context examples.
    """
    # Configure DSPy LM from model_cfg
    # Note: We'll use a simple mapping; in production, this might use litellm
    lm_params = {
        "model": model_cfg.model,
        "temperature": model_cfg.temperature,
        "max_tokens": model_cfg.max_tokens,
    }
    # Determine the DSPy model string based on provider
    if model_cfg.provider == "openai":
        dspy_model = f"openai/{model_cfg.model}"
    elif model_cfg.provider == "anthropic":
        dspy_model = f"anthropic/{model_cfg.model}"
    else:
        # Fallback to generic format; assume it's a LiteLLM-compatible string
        dspy_model = model_cfg.model

    # Handle API keys via environment variable if specified
    if model_cfg.api_key_env:
        import os
        api_key = os.getenv(model_cfg.api_key_env)
        if api_key:
            lm_params["api_key"] = api_key

    # Initialize DSPy LM
    lm = dspy.LM(dspy_model, **lm_params)
    dspy.configure(lm=lm)

    # Extract input field names from prompt.template by finding {variable} patterns
    # Simple approach: use string.Formatter
    import string
    formatter = string.Formatter()
    field_names = []
    try:
        for _, field_name, _, _ in formatter.parse(prompt.template):
            if field_name is not None:
                field_names.append(field_name)
    except Exception:
        # Fallback: no variables detected
        field_names = []
    field_names = list(set(field_names))  # deduplicate

    # Ensure 'completion' is not considered an input field; it's the output
    input_fields = [f for f in field_names if f != "completion"]

    # Dynamically create a Signature class
    class FewShotSignature(dspy.Signature):
        """The docstring becomes the task description; we set it below."""
        pass

    # Add input fields as dspy.InputField
    for field in input_fields:
        setattr(FewShotSignature, field, dspy.InputField())
    # Add output field
    FewShotSignature.completion = dspy.OutputField()

    # Set the docstring to the original prompt template
    # This tells the model what task to perform
    FewShotSignature.__doc__ = prompt.template

    # Create a Module (Predictor) with this Signature
    predictor = dspy.Predict(FewShotSignature)

    # Convert dataset to dspy.Example objects
    trainset = []
    for item in dataset:
        # Each item should have keys for all input fields and a 'completion' key
        example = dspy.Example(
            **{field: item[field] for field in input_fields if field in item},
            completion=item.get("completion", "")
        )
        trainset.append(example)

    if not trainset:
        # No examples, return original prompt
        return prompt.template

    # Use BootstrapFewShot to compile the predictor
    # It will select good demonstrations from trainset
    teleprompter = dspy.BootstrapFewShot(
        metric=dspy.evaluate.SeeIfCatch(
            predict=lambda pred, example: pred.completion == example.completion
        ),
        max_bootstrapped_demos=min(4, len(trainset)),  # up to 4 examples
        max_labeled_demos=min(4, len(trainset)),
    )
    try:
        compiled_predictor = teleprompter.compile(predictor, trainset=trainset)
    except Exception:
        # On failure, fallback to original
        return prompt.template

    # Extract demonstrations from compiled predictor
    # In dspy, the compiled predictor has a 'demos' attribute (list of Example)
    if hasattr(compiled_predictor, "demos") and compiled_predictor.demos:
        demos = compiled_predictor.demos
    else:
        # No demos selected, return original
        return prompt.template

    # Format examples as a string to append to the prompt
    examples_section = "\n\nExamples:\n"
    for demo in demos:
        # Format each example: show input fields and the completion
        example_lines = []
        for field in input_fields:
            if hasattr(demo, field):
                val = getattr(demo, field)
                example_lines.append(f"{field}: {val}")
        if hasattr(demo, "completion"):
            example_lines.append(f"completion: {demo.completion}")
        examples_section += "\n" + "\n".join(example_lines) + "\n"

    # Construct new template: original instruction + examples
    new_template = prompt.template + examples_section

    return new_template
