"""Study metadata and information models.

This module provides data models for managing study-related information and metadata.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, validator


class StudyIdentifier(BaseModel):
    """Study identification information."""

    study_id: UUID = Field(..., description="Unique identifier for the study")
    source_id: str = Field(..., description="Original source identifier")
    version: str = Field(..., description="Study version")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )


class StudyMetadata(BaseModel):
    """Study metadata including source information and processing status."""

    identifier: StudyIdentifier = Field(..., description="Study identification info")
    title: str = Field(..., description="Study title")
    authors: List[str] = Field(..., description="Study authors")
    publication_date: Optional[datetime] = Field(None, description="Publication date")
    source_files: Dict[str, str] = Field(
        default_factory=dict, description="Source file locations"
    )
    processed_files: Dict[str, str] = Field(
        default_factory=dict, description="Processed file locations"
    )
    extraction_status: str = Field("pending", description="Text extraction status")
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )

    @validator("source_files", "processed_files")
    def validate_file_paths(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate that file paths are properly formatted."""
        for key, path in v.items():
            if not path.strip():
                raise ValueError(f"Empty path provided for {key}")
        return v

    class Config:
        """Pydantic model configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class StudyOutputJson(BaseModel):
    """Model for study output data in JSON format."""

    study_id: UUID = Field(..., description="Study identifier")
    title: str = Field(..., description="Study title")
    results: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extraction results"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional output metadata"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this output was created"
    )
    version: str = Field("1.0.0", description="Output format version")

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }

