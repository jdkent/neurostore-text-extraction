"""Pipeline output handling utilities.

This module provides functionality for managing pipeline outputs and results.
"""
from pathlib import Path
from typing import Any, Dict, Optional, Union
import shutil

from ..data_models.pipeline_info import PipelineMetadata, PipelineStatus
from .file_ops import atomic_write, safe_json_read, safe_json_write
from ..pipelines.utils.errors import FileOperationError


class PipelineOutputManager:
    """Manager for handling pipeline output files and metadata."""

    def __init__(self, output_dir: Path):
        """Initialize with output directory for pipeline results.
        
        Args:
            output_dir: Base directory for storing pipeline outputs
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir = self.output_dir / "metadata"
        self.metadata_dir.mkdir(exist_ok=True)
        self.results_dir = self.output_dir / "results"
        self.results_dir.mkdir(exist_ok=True)

    def get_pipeline_metadata(self, pipeline_id: str) -> PipelineMetadata:
        """Get metadata for a specific pipeline run.
        
        Args:
            pipeline_id: Pipeline run identifier
            
        Returns:
            Pipeline metadata object
            
        Raises:
            FileOperationError: If metadata file cannot be read
        """
        metadata_path = self.metadata_dir / f"{pipeline_id}.json"
        data = safe_json_read(metadata_path)
        return PipelineMetadata.parse_obj(data)

    def save_pipeline_metadata(self, metadata: PipelineMetadata) -> None:
        """Save pipeline metadata to file.
        
        Args:
            metadata: Pipeline metadata object to save
            
        Raises:
            FileOperationError: If metadata cannot be saved
        """
        pipeline_id = metadata.name
        metadata_path = self.metadata_dir / f"{pipeline_id}.json"
        safe_json_write(metadata_path, metadata.dict())

    def update_pipeline_status(
        self, pipeline_id: str, status: PipelineStatus
    ) -> None:
        """Update status for a pipeline run.
        
        Args:
            pipeline_id: Pipeline run identifier
            status: New status object
            
        Raises:
            FileOperationError: If status update fails
        """
        try:
            metadata = self.get_pipeline_metadata(pipeline_id)
            metadata.execution_history.append(status)
            self.save_pipeline_metadata(metadata)
        except FileOperationError as e:
            raise FileOperationError(
                f"Failed to update status for pipeline {pipeline_id}: {str(e)}"
            ) from e

    def save_pipeline_result(
        self, 
        pipeline_id: str,
        result_type: str,
        data: Union[str, bytes, Dict[str, Any]],
        file_ext: str = "json"
    ) -> Path:
        """Save pipeline result data to file.
        
        Args:
            pipeline_id: Pipeline run identifier
            result_type: Type of result (e.g., "analysis", "visualization")
            data: Result data to save
            file_ext: File extension for result file
            
        Returns:
            Path to saved result file
            
        Raises:
            FileOperationError: If result cannot be saved
        """
        result_dir = self.results_dir / pipeline_id
        result_dir.mkdir(parents=True, exist_ok=True)
        
        result_path = result_dir / f"{result_type}.{file_ext}"
        
        try:
            if isinstance(data, (str, bytes)):
                mode = "wb" if isinstance(data, bytes) else "w"
                atomic_write(result_path, data, mode=mode)
            else:
                safe_json_write(result_path, data)
            return result_path
        except Exception as e:
            raise FileOperationError(
                f"Failed to save {result_type} result for pipeline {pipeline_id}: {str(e)}"
            ) from e

    def archive_pipeline_outputs(
        self, pipeline_id: str, archive_dir: Optional[Path] = None
    ) -> Path:
        """Archive all outputs from a pipeline run.
        
        Args:
            pipeline_id: Pipeline run identifier
            archive_dir: Optional directory for archive file
            
        Returns:
            Path to created archive file
            
        Raises:
            FileOperationError: If archiving fails
        """
        if archive_dir is None:
            archive_dir = self.output_dir / "archives"
            archive_dir.mkdir(exist_ok=True)

        source_dir = self.results_dir / pipeline_id
        if not source_dir.exists():
            raise FileOperationError(f"No results found for pipeline {pipeline_id}")

        archive_path = archive_dir / f"{pipeline_id}.tar.gz"
        try:
            shutil.make_archive(
                str(archive_path.with_suffix("")),
                "gztar",
                root_dir=source_dir.parent,
                base_dir=source_dir.name
            )
            return archive_path
        except Exception as e:
            raise FileOperationError(
                f"Failed to create archive for pipeline {pipeline_id}: {str(e)}"
            ) from e

    def clear_pipeline_outputs(
        self, pipeline_id: str, keep_metadata: bool = True
    ) -> None:
        """Remove all output files for a pipeline run.
        
        Args:
            pipeline_id: Pipeline run identifier
            keep_metadata: Whether to preserve metadata files
            
        Raises:
            FileOperationError: If removal fails
        """
        try:
            # Remove results
            result_dir = self.results_dir / pipeline_id
            if result_dir.exists():
                shutil.rmtree(result_dir)

            # Remove metadata if requested
            if not keep_metadata:
                metadata_path = self.metadata_dir / f"{pipeline_id}.json"
                if metadata_path.exists():
                    metadata_path.unlink()
        except Exception as e:
            raise FileOperationError(
                f"Failed to clear outputs for pipeline {pipeline_id}: {str(e)}"
            ) from e


class PipelineOutputsMixin:
    """Mixin class providing pipeline output management functionality.
    
    This mixin provides access to pipeline output file management through
    a PipelineOutputManager instance.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the mixin.
        
        Args:
            output_dir: Output directory for pipeline results (if not provided in kwargs)
        """
        super().__init__(*args, **kwargs)
        self._output_manager = None

    @property
    def output_manager(self) -> PipelineOutputManager:
        """Get or create the pipeline output manager instance."""
        if self._output_manager is None:
            output_dir = getattr(self, 'output_dir', Path())
            self._output_manager = PipelineOutputManager(output_dir)
        return self._output_manager

    def get_pipeline_metadata(self, pipeline_id: str) -> PipelineMetadata:
        """Get metadata for a specific pipeline run."""
        return self.output_manager.get_pipeline_metadata(pipeline_id)

    def save_pipeline_metadata(self, metadata: PipelineMetadata) -> None:
        """Save pipeline metadata to file."""
        self.output_manager.save_pipeline_metadata(metadata)

    def update_pipeline_status(
        self,
        pipeline_id: str,
        status: PipelineStatus
    ) -> None:
        """Update status for a pipeline run."""
        self.output_manager.update_pipeline_status(pipeline_id, status)

    def save_pipeline_result(
        self,
        pipeline_id: str,
        result_type: str,
        data: Union[str, bytes, Dict[str, Any]],
        file_ext: str = "json"
    ) -> Path:
        """Save pipeline result data to file."""
        return self.output_manager.save_pipeline_result(
            pipeline_id, result_type, data, file_ext
        )

    def archive_pipeline_outputs(
        self,
        pipeline_id: str,
        archive_dir: Optional[Path] = None
    ) -> Path:
        """Archive all outputs from a pipeline run."""
        return self.output_manager.archive_pipeline_outputs(
            pipeline_id, archive_dir
        )

    def clear_pipeline_outputs(
        self,
        pipeline_id: str,
        keep_metadata: bool = True
    ) -> None:
        """Remove all output files for a pipeline run."""
        self.output_manager.clear_pipeline_outputs(
            pipeline_id, keep_metadata
        )
