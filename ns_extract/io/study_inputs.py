"""Study input handling utilities.

This module provides functionality for managing and validating study input files.
"""
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..data_models.study_info import StudyMetadata
from .file_ops import safe_json_read, safe_json_write
from ..pipelines.utils.errors import FileOperationError


class StudyInputManager:
    """Manager for handling study input files and metadata."""

    def __init__(self, base_dir: Path):
        """Initialize with base directory for study files.
        
        Args:
            base_dir: Base directory containing study files
        """
        self.base_dir = Path(base_dir)
        self.metadata_dir = self.base_dir / "metadata"
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def get_study_metadata(self, study_id: str) -> StudyMetadata:
        """Get metadata for a specific study.
        
        Args:
            study_id: Study identifier
            
        Returns:
            Study metadata object
            
        Raises:
            FileOperationError: If metadata file cannot be read
        """
        metadata_path = self.metadata_dir / f"{study_id}.json"
        data = safe_json_read(metadata_path)
        return StudyMetadata.parse_obj(data)

    def save_study_metadata(self, metadata: StudyMetadata) -> None:
        """Save study metadata to file.
        
        Args:
            metadata: Study metadata object to save
            
        Raises:
            FileOperationError: If metadata cannot be saved
        """
        study_id = str(metadata.identifier.study_id)
        metadata_path = self.metadata_dir / f"{study_id}.json"
        safe_json_write(metadata_path, metadata.dict())

    def get_study_files(self, study_id: str) -> Dict[str, Set[Path]]:
        """Get all files associated with a study.
        
        Args:
            study_id: Study identifier
            
        Returns:
            Dictionary mapping file types to sets of file paths
        """
        study_dir = self.base_dir / study_id
        if not study_dir.exists():
            return {}

        result: Dict[str, Set[Path]] = {
            "source": set(),
            "processed": set(),
            "metadata": set()
        }

        for path in study_dir.rglob("*"):
            if path.is_file():
                if "source" in path.parts:
                    result["source"].add(path)
                elif "processed" in path.parts:
                    result["processed"].add(path)
                elif path.suffix == ".json":
                    result["metadata"].add(path)

        return result

    def validate_study_files(
        self, study_id: str, required_files: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate presence and structure of study files.
        
        Args:
            study_id: Study identifier
            required_files: List of required file patterns
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        files = self.get_study_files(study_id)
        errors: List[str] = []

        # Check basic structure
        if not files:
            errors.append(f"No files found for study {study_id}")
            return False, errors

        # Validate required files if specified
        if required_files:
            for pattern in required_files:
                found = False
                for file_set in files.values():
                    if any(str(p).endswith(pattern) for p in file_set):
                        found = True
                        break
                if not found:
                    errors.append(f"Missing required file: {pattern}")

        # Check metadata consistency
        try:
            metadata = self.get_study_metadata(study_id)
            for file_type, paths in files.items():
                if file_type in ("source", "processed"):
                    stored_paths = getattr(metadata, f"{file_type}_files", {}).values()
                    for path in paths:
                        if str(path.relative_to(self.base_dir)) not in stored_paths:
                            errors.append(
                                f"File {path} not registered in metadata {file_type}_files"
                            )
        except FileOperationError as e:
            errors.append(f"Metadata validation failed: {str(e)}")

        return len(errors) == 0, errors


class StudyInputsMixin:
    """Mixin class providing study input management functionality.
    
    This mixin provides access to study input file management and validation
    through a StudyInputManager instance.
    """
    
    def __init__(self, *args, **kwargs):
        """Initialize the mixin.
        
        Args:
            base_dir: Base directory for study files (if not provided in kwargs)
        """
        super().__init__(*args, **kwargs)
        self._study_input_manager = None

    @property
    def study_input_manager(self) -> StudyInputManager:
        """Get or create the study input manager instance."""
        if self._study_input_manager is None:
            base_dir = getattr(self, 'base_dir', Path())
            self._study_input_manager = StudyInputManager(base_dir)
        return self._study_input_manager

    def get_study_metadata(self, study_id: str) -> StudyMetadata:
        """Get metadata for a specific study."""
        return self.study_input_manager.get_study_metadata(study_id)

    def save_study_metadata(self, metadata: StudyMetadata) -> None:
        """Save study metadata to file."""
        self.study_input_manager.save_study_metadata(metadata)

    def get_study_files(self, study_id: str) -> Dict[str, Set[Path]]:
        """Get all files associated with a study."""
        return self.study_input_manager.get_study_files(study_id)

    def validate_study_files(
        self,
        study_id: str,
        required_files: Optional[List[str]] = None
    ) -> Tuple[bool, List[str]]:
        """Validate presence and structure of study files."""
        return self.study_input_manager.validate_study_files(
            study_id, required_files
        )
