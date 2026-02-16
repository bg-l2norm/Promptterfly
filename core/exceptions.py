"""
Custom exceptions for Promptterfly.

All Promptterfly-specific errors inherit from PromptterflyError.
"""


class PromptterflyError(Exception):
    """Base exception for all Promptterfly errors."""
    pass


class PromptNotFound(PromptterflyError):
    """Raised when a requested prompt cannot be found."""
    def __init__(self, prompt_id: str):
        super().__init__(f"Prompt with ID '{prompt_id}' not found")
        self.prompt_id = prompt_id


class InvalidConfig(PromptterflyError):
    """Raised when configuration is invalid or cannot be loaded."""
    pass


class ValidationError(PromptterflyError):
    """Raised when data validation fails."""
    def __init__(self, message: str):
        super().__init__(f"Validation error: {message}")


class VersionNotFound(PromptterflyError):
    """Raised when a requested version cannot be found."""
    def __init__(self, prompt_id: str, version: int):
        super().__init__(f"Version {version} for prompt '{prompt_id}' not found")
        self.prompt_id = prompt_id
        self.version = version


class ModelNotFound(PromptterflyError):
    """Raised when a requested model configuration is not found."""
    def __init__(self, model_name: str):
        super().__init__(f"Model configuration '{model_name}' not found")
        self.model_name = model_name


class StorageError(PromptterflyError):
    """Raised when a storage operation fails."""
    pass
