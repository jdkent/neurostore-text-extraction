"""Pipeline metadata and execution information models.

This module provides data models for tracking pipeline execution state and metadata.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class PipelineStatus(BaseModel):
    """Pipeline execution status information."""

    pipeline_id: UUID = Field(..., description="Unique identifier for pipeline run")
    start_time: datetime = Field(
        default_factory=datetime.utcnow, description="Pipeline start time"
    )
    end_time: Optional[datetime] = Field(None, description="Pipeline completion time")
    status: str = Field("pending", description="Current execution status")
    error: Optional[str] = Field(None, description="Error message if failed")
    progress: float = Field(0.0, description="Progress percentage (0-100)")
    artifacts: Dict[str, str] = Field(
        default_factory=dict, description="Generated artifact locations"
    )

    class Config:
        """Pydantic model configuration."""

        json_encoders = {
            datetime: lambda v: v.isoformat(),
            UUID: lambda v: str(v),
        }


class PipelineMetadata(BaseModel):
    """Pipeline metadata including configuration and execution history."""

    name: str = Field(..., description="Pipeline name")
    version: str = Field(..., description="Pipeline version")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )
    execution_history: List[PipelineStatus] = Field(
        default_factory=list, description="History of pipeline executions"
    )
    config_hash: str = Field(..., description="Hash of pipeline configuration")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Pipeline parameters"
    )


class InputPipelineInfo(BaseModel):
    """Information about input data for a pipeline."""

    study_id: str = Field(..., description="Unique identifier for the study")
    data_path: str = Field(..., description="Path to input data")
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional metadata about the input"
    )
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this input was created"
    )


class PipelineOutputInfo(BaseModel):
    """Information about pipeline execution outputs."""

    study_id: str = Field(..., description="Study identifier")
    pipeline_id: UUID = Field(..., description="Pipeline run identifier")
    output_path: str = Field(..., description="Path to output data")
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this output was created"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional output metadata"
    )
    status: str = Field("completed", description="Output status")
