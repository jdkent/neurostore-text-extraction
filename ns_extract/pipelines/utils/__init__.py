"""Utility functions and types for NeuroStore pipelines."""

from .errors import (
    FileOperationError,
    InputError,
    ProcessingError,
    ValidationError
)
from .types import (
    PipelineConfig,
    StudyResults,
    PipelineResults,
    ValidationResult,
    PipelineInputs
)

__all__ = [
    # Errors
    "FileOperationError",
    "InputError",
    "ProcessingError",
    "ValidationError",
    
    # Types
    "PipelineConfig",
    "StudyResults",
    "PipelineResults", 
    "ValidationResult",
    "PipelineInputs"
]

__version__ = "1.0.0"
