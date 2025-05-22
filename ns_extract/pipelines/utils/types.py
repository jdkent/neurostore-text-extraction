"""Type definitions for the pipeline system.

This module provides common type definitions and type aliases used throughout
the pipeline system to ensure consistent typing and improve code clarity.
"""
from typing import Any, Dict, List, Optional, Union, TypeVar, Callable
from pathlib import Path


# Base types
PathLike = Union[str, Path]
JsonDict = Dict[str, Any]
ConfigDict = Dict[str, Any]

# Generic type variable for pipeline data
T = TypeVar('T')

# Pipeline specific types
PipelineInput = Union[PathLike, Dict[str, Any], str]
PipelineOutput = Dict[str, Any]
PipelineConfig = Dict[str, Any]
PipelineMetadata = Dict[str, Any]

# Validation types
ValidationResult = Dict[str, List[str]]
ValidationFunction = Callable[[Any], Optional[List[str]]]

# Processing types
ProcessingResult = Dict[str, Any]
ProcessingMetadata = Dict[str, Any]

# Study specific types
StudyId = str
StudyData = Dict[str, Any]
StudyMetadata = Dict[str, Any]
StudyResults = Dict[str, Any]

# Pipeline specific data structures
PipelineResults = Dict[str, Any]
PipelineInputs = Union[str, Dict[str, Any], List[str]]

# File operation types
FileContent = Union[str, bytes]
FileMetadata = Dict[str, Any]

# Status and progress types
Status = Dict[str, Union[str, float, int]]
Progress = Dict[str, Union[int, float]]

# Callback types
ProgressCallback = Callable[[float, str], None]
StatusCallback = Callable[[Dict[str, Any]], None]
