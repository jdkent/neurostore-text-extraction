"""Core extractor functionality.

This module provides the base Extractor class and its supporting components
for transforming study data. It includes:
- Base Extractor class with validation and post-processing
- Version tracking and schema validation
- Common utilities for data transformation

Example:
    >>> class CustomExtractor(BaseExtractor):
    ...     _version = "1.0.0"
    ...     _output_schema = CustomOutputSchema
    ...
    ...     def _transform(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
    ...         # Custom transformation logic
    ...         return transformed_data
"""
from __future__ import annotations

from abc import ABC, abstractmethod
import logging
from typing import Any, Dict, Optional, Type, TypeVar, Generic
from datetime import datetime

from pydantic import BaseModel, Field

from ns_extract.pipelines.utils.errors import ValidationError, ProcessingError
from ns_extract.pipelines.utils.types import ValidationResult

# Type variable for output schema
T = TypeVar('T', bound=BaseModel)


class ExtractorMetadata(BaseModel):
    """Metadata about an extractor run."""
    version: str = Field(..., description="Extractor version")
    timestamp: datetime = Field(default_factory=datetime.now)
    validation_status: bool = Field(default=False)
    processing_stats: Optional[Dict[str, Any]] = Field(default=None)


class BaseExtractor(Generic[T], ABC):
    """Base class for extractors with validation and versioning.
    
    This class provides core functionality for:
    - Data transformation with validation
    - Version tracking and compatibility
    - Schema-based output validation
    - Post-processing capabilities
    
    Attributes:
        _version (str): Version string for the extractor
        _output_schema (Type[T]): Pydantic model defining output format
    """
    
    _version: str
    _output_schema: Type[T]
    
    def __init__(self):
        """Initialize the extractor."""
        if not self._version:
            raise ValueError("Extractor must define _version")
        if not self._output_schema:
            raise ValueError("Extractor must define _output_schema")
            
        self._metadata = ExtractorMetadata(
            version=self._version,
            validation_status=False
        )

    @abstractmethod
    def _transform(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Core transformation logic to be implemented by subclasses.
        
        Args:
            data: Input data to transform
            
        Returns:
            Transformed data matching output schema
            
        Raises:
            ProcessingError: If transformation fails
        """
        pass

    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Validate data against output schema.
        
        Args:
            data: Data to validate
            
        Returns:
            Tuple of (is_valid, validated_data)
        """
        try:
            validated = self._output_schema.model_validate(data)
            return True, validated.model_dump()
        except Exception as e:
            logging.error(f"Validation error: {str(e)}")
            return False, data

    def post_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Post-process data after transformation.
        
        This method can be overridden by subclasses to implement
        data cleaning, normalization, or other post-processing steps.
        
        Args:
            data: Data to post-process
            
        Returns:
            Post-processed data
        """
        return data

    def transform(
        self, 
        data: Dict[str, Any],
        validate: bool = True
    ) -> Dict[str, Any]:
        """Transform input data with validation and post-processing.
        
        This method orchestrates the full transformation pipeline:
        1. Core transformation
        2. Post-processing
        3. Validation (optional)
        
        Args:
            data: Input data to transform
            validate: Whether to validate output
            
        Returns:
            Transformed and validated data
            
        Raises:
            ProcessingError: If transformation fails
            ValidationError: If validation fails and validation is required
        """
        try:
            # Core transformation
            transformed = self._transform(data)
            
            # Post-processing
            processed = self.post_process(transformed)
            
            # Validation
            if validate:
                is_valid, validated = self.validate(processed)
                self._metadata.validation_status = is_valid
                
                if not is_valid and validate:
                    raise ValidationError(
                        "Output validation failed",
                        details={"data": processed}
                    )
                return validated
                
            return processed
            
        except Exception as e:
            if not isinstance(e, (ValidationError, ProcessingError)):
                raise ProcessingError(str(e))
            raise

    @property
    def metadata(self) -> ExtractorMetadata:
        """Get extractor metadata."""
        return self._metadata

    @property 
    def version(self) -> str:
        """Get extractor version."""
        return self._version
        
    def get_schema(self) -> Dict[str, Any]:
        """Get JSON schema for output format."""
        return self._output_schema.model_json_schema()
