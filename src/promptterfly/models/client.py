"""Unified LLM client wrapper."""
import os
from typing import Optional
import litellm

from ..core.models import ModelConfig


class LLMClient:
    """Unified client for making LLM API calls via LiteLLM."""

    @staticmethod
    def call(prompt: str, model: ModelConfig, **kwargs) -> str:
        """Call the LLM with a single prompt.

        Args:
            prompt: The prompt text to send.
            model: ModelConfig with provider, model name, and settings.
            **kwargs: Additional arguments to pass to litellm.completion
                      (e.g., stream, max_tokens override, etc.)

        Returns:
            The response text from the LLM.

        Raises:
            ValueError: If API key is required but not found.
            Exception: For API errors from litellm.
        """
        # Handle API key from environment variable if specified
        api_key = None
        if model.api_key_env:
            api_key = os.getenv(model.api_key_env)
            if api_key is None:
                raise ValueError(
                    f"API key not found in environment variable '{model.api_key_env}'. "
                    f"Set it before calling the model."
                )

        # Prepare messages format
        messages = [{"role": "user", "content": prompt}]

        # Prepare completion parameters
        completion_kwargs = {
            "model": model.model,
            "messages": messages,
            "temperature": model.temperature,
            "max_tokens": model.max_tokens,
        }

        # Add API key if present
        if api_key:
            completion_kwargs["api_key"] = api_key

        # Merge any additional kwargs
        completion_kwargs.update(kwargs)

        try:
            response = litellm.completion(**completion_kwargs)
            # Extract text from response
            # LiteLLM returns an object with choices[0].message.content
            if hasattr(response, 'choices') and response.choices:
                return response.choices[0].message.content
            elif isinstance(response, dict) and 'choices' in response:
                return response['choices'][0]['message']['content']
            else:
                raise ValueError(f"Unexpected response format from LiteLLM: {response}")
        except Exception as e:
            # Re-raise with more context
            raise Exception(f"LLM call failed for model '{model.name}': {e}") from e
