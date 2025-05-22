"""Core pipeline implementation.

This module provides the base Pipeline class and its specialized implementations for
different processing patterns:

- Pipeline: Base abstract class defining core interface
- IndependentPipeline: For processing each study independently
- DependentPipeline: For processing studies as a group
- Shared utilities for pipeline operations
"""
from abc import ABC, abstractmethod
from datetime import datetime
import hashlib
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, TypeVar, Iterator
import concurrent.futures

from ..utils.errors import (
    ConfigurationError,
    ProcessingError,
    ValidationError
)
from ..utils.types import (
    PathLike,
    ConfigDict,
    PipelineInput,
    PipelineOutput,
    ValidationResult,
    ProcessingResult,
)

# Type variable for generic pipeline outputs
T = TypeVar('T')

logger = logging.getLogger(__name__)


class Pipeline(ABC):
    """Base class for all pipeline implementations.
    
    This class defines the core interface that all pipelines must implement,
    providing common functionality and enforcing consistent behavior across
    different pipeline types.

    Attributes:
        config: Pipeline configuration dictionary
        version: Pipeline version string
        name: Pipeline name (defaults to class name)
    """

    def __init__(
        self,
        config: Optional[ConfigDict] = None,
        version: str = "latest",
    ) -> None:
        """Initialize pipeline with configuration.
        
        Args:
            config: Optional configuration dictionary for the pipeline
            version: Pipeline version string
        
        Raises:
            ConfigurationError: If configuration validation fails
        """
        self.config = config or {}
        self.version = version
        self._validate_config()
        self._setup()

    def _validate_config(self) -> None:
        """Validate pipeline configuration.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        try:
            validation_result = self.validate_config()
            if validation_result:
                raise ConfigurationError(
                    "Configuration validation failed",
                    details=validation_result
                )
        except Exception as e:
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")

    def _setup(self) -> None:
        """Set up pipeline internal state.
        
        This method is called after configuration validation to set up any
        internal state or resources needed by the pipeline. Override this
        method to implement custom setup logic.
        """
        pass

    @abstractmethod
    def validate_config(self) -> Optional[ValidationResult]:
        """Validate pipeline configuration.
        
        Returns:
            Optional validation result dictionary with errors, or None if valid

        This method should be implemented by subclasses to validate their
        specific configuration requirements.
        """
        pass

    @abstractmethod
    def process(self, input_data: PipelineInput) -> PipelineOutput:
        """Process input data through the pipeline.
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed output data
            
        Raises:
            ProcessingError: If processing fails
            ValidationError: If output validation fails
        """
        pass

    def cleanup(self) -> None:
        """Clean up pipeline resources.
        
        This method should be called when the pipeline is no longer needed
        to clean up any resources or state. Override this method to implement
        custom cleanup logic.
        """
        pass

    @property
    def name(self) -> str:
        """Get pipeline name.
        
        Returns:
            Name of the pipeline (defaults to class name)
        """
        return self.__class__.__name__

    def generate_output_path(self, base_path: PathLike) -> Path:
        """Generate unique output path for pipeline results.
        
        Args:
            base_path: Base path for output directory

        Returns:
            Path object pointing to unique output directory
        """
        # Create hash from pipeline config and version
        config_str = str(sorted(self.config.items()))
        hash_input = f"{config_str}_{self.version}_{self.name}"
        hash_value = hashlib.shake_256(hash_input.encode()).hexdigest(6)
        
        # Construct path with version and hash
        return Path(base_path) / self.name / self.version / hash_value

    def _get_metadata(self) -> Dict[str, Any]:
        """Get pipeline metadata.
        
        Returns:
            Dictionary containing pipeline metadata
        """
        return {
            "name": self.name,
            "version": self.version,
            "config": self.config,
            "timestamp": datetime.now().isoformat(),
            "class": self.__class__.__name__
        }

    def __enter__(self) -> 'Pipeline':
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit with cleanup."""
        self.cleanup()

    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.name}(version={self.version})"


class IndependentPipeline(Pipeline):
    """Pipeline implementation for independent study processing.
    
    This pipeline processes each study independently, allowing for:
    - Parallel processing across multiple studies
    - Independent validation per study
    - Isolated error handling
    """

    def process_study(self, study_input: PipelineInput) -> ProcessingResult:
        """Process a single study independently.
        
        Args:
            study_input: Input data for a single study
            
        Returns:
            Processing result for the study
            
        Raises:
            ProcessingError: If study processing fails
        """
        try:
            return self.process(study_input)
        except Exception as e:
            raise ProcessingError(f"Study processing failed: {str(e)}")

    def process_parallel(
        self,
        studies: List[PipelineInput],
        max_workers: int = 4
    ) -> Iterator[ProcessingResult]:
        """Process multiple studies in parallel.
        
        Args:
            studies: List of study inputs to process
            max_workers: Maximum number of parallel workers
            
        Returns:
            Iterator yielding results as they complete
        """
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self.process_study, study): study 
                for study in studies
            }
            
            for future in concurrent.futures.as_completed(futures):
                try:
                    yield future.result()
                except Exception as e:
                    logger.error(f"Failed to process study: {str(e)}")


class DependentPipeline(Pipeline):
    """Pipeline implementation for dependent study processing.
    
    This pipeline processes studies as a group, allowing for:
    - Cross-study analysis and aggregation
    - Global validation across all studies
    - Shared state between studies
    """

    def prepare_batch(self, studies: List[PipelineInput]) -> Dict[str, Any]:
        """Prepare studies for batch processing.
        
        This method can be overridden to implement custom batch preparation logic,
        such as pre-processing or arranging studies in a specific order.
        
        Args:
            studies: List of study inputs
            
        Returns:
            Prepared batch data
        """
        return {"studies": studies}

    def validate_batch(self, results: Dict[str, Any]) -> ValidationResult:
        """Validate results across all studies.
        
        This method should be overridden to implement custom validation logic
        that considers the entire batch of results.
        
        Args:
            results: Results from batch processing
            
        Returns:
            Validation result with any errors
        """
        return None

    def process_batch(
        self,
        studies: List[PipelineInput]
    ) -> Dict[str, ProcessingResult]:
        """Process multiple studies as a batch.
        
        Args:
            studies: List of study inputs to process
            
        Returns:
            Dictionary mapping study IDs to their results
            
        Raises:
            ProcessingError: If batch processing fails
            ValidationError: If batch validation fails
        """
        try:
            # Prepare batch
            batch_data = self.prepare_batch(studies)
            
            # Process batch
            results = self.process(batch_data)
            
            # Validate batch results
            validation_result = self.validate_batch(results)
            if validation_result:
                raise ValidationError(
                    "Batch validation failed",
                    details=validation_result
                )
                
            return results
            
        except Exception as e:
            if not isinstance(e, (ProcessingError, ValidationError)):
                raise ProcessingError(f"Batch processing failed: {str(e)}")
            raise


# Utility functions
def create_pipeline(
    pipeline_type: str,
    config: Optional[ConfigDict] = None,
    version: str = "latest"
) -> Pipeline:
    """Create pipeline instance of specified type.
    
    Args:
        pipeline_type: Type of pipeline to create ("independent" or "dependent")
        config: Optional pipeline configuration
        version: Pipeline version string
        
    Returns:
        Pipeline instance of requested type
        
    Raises:
        ValueError: If pipeline_type is invalid
    """
    pipeline_classes = {
        "independent": IndependentPipeline,
        "dependent": DependentPipeline
    }
    
    pipeline_class = pipeline_classes.get(pipeline_type.lower())
    if not pipeline_class:
        raise ValueError(
            f"Invalid pipeline type: {pipeline_type}. "
            f"Must be one of: {list(pipeline_classes.keys())}"
        )
        
    return pipeline_class(config=config, version=version)
