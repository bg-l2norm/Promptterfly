"""Custom exceptions for Promptterfly."""


class PromptterflyError(Exception):
    """Base exception for Promptterfly errors."""
    pass


class PromptNotFound(PromptterflyError):
    """Raised when a prompt is not found."""
    pass


class InvalidConfig(PromptterflyError):
    """Raised when configuration is invalid."""
    pass
