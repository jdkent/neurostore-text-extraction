"""Configuration data models for pipeline settings and validation.

This module provides Pydantic models for validating and managing pipeline configurations.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, validator


class FileConfig(BaseModel):
    """File system related configuration settings."""

    base_dir: Path = Field(..., description="Base directory for all file operations")
    input_dir: Path = Field(..., description="Directory containing input files")
    output_dir: Path = Field(..., description="Directory for storing outputs")
    temp_dir: Optional[Path] = Field(None, description="Directory for temporary files")
    max_retries: int = Field(3, description="Maximum retries for file operations")
    timeout: float = Field(30.0, description="Timeout in seconds for file operations")

    @validator("base_dir", "input_dir", "output_dir", "temp_dir")
    def validate_directory(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate directory paths exist and are accessible."""
        if v is not None:
            v = Path(v).resolve()
            if not v.exists():
                v.mkdir(parents=True, exist_ok=True)
            if not v.is_dir():
                raise ValueError(f"Path {v} is not a directory")
        return v


class PipelineConfig(BaseModel):
    """Pipeline execution configuration settings."""

    name: str = Field(..., description="Name of the pipeline")
    version: str = Field(..., description="Pipeline version")
    description: Optional[str] = Field(None, description="Pipeline description")
    file_config: FileConfig = Field(..., description="File system configuration")
    params: Dict[str, Any] = Field(default_factory=dict, description="Pipeline parameters")
    dependencies: List[str] = Field(
        default_factory=list, description="Required pipeline dependencies"
    )

    class Config:
        """Pydantic model configuration."""

        arbitrary_types_allowed = True
