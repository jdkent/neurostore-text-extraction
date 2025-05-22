"""Exception hierarchy for the pipeline system.

This module defines the core exceptions used throughout the pipeline system.
All custom exceptions inherit from PipelineError to allow for consistent error handling.
"""
from typing import Optional, Dict, Any


class PipelineError(Exception):
    """Base exception for all pipeline-related errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.details = details or {}
        self.message = message

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} (details: {self.details})"
        return self.message


class InputError(PipelineError):
    """Raised when there are issues with pipeline inputs."""
    pass


class ValidationError(PipelineError):
    """Raised when output validation fails."""
    pass


class ProcessingError(PipelineError):
    """Raised when study processing fails."""

    def __init__(self, study_id: str, message: str, details: Optional[Dict[str, Any]] = None):
        self.study_id = study_id
        super().__init__(f"Error processing study {study_id}: {message}", details)


class FileOperationError(PipelineError):
    """Raised when file operations (read/write) fail."""
    pass


class ConfigurationError(PipelineError):
    """Raised when pipeline configuration is invalid."""
    pass


# Additional pipeline-specific errors
class OutputError(PipelineError):
    """Raised when there is an error with pipeline output handling."""
    pass


class ResourceError(PipelineError):
    """Raised when there is an error with pipeline resources."""
    pass
