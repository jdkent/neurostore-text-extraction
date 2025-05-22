"""Tests for package organization and backwards compatibility."""

import pytest

from ns_extract.pipelines import (
    Pipeline,
    IndependentPipeline,
    DependentPipeline,
    Extractor
)
from ns_extract.io import (
    FileOperationsMixin,
    StudyInputsMixin,
    PipelineOutputsMixin
)
from ns_extract.data_models import (
    PipelineConfig,
    PipelineOutputInfo
)


def test_backwards_compatibility_imports():
    """Test that old import paths still work but trigger warnings."""
    with pytest.warns(DeprecationWarning):
        from ns_extract.pipelines.base import Pipeline
        assert Pipeline is not None

    with pytest.warns(DeprecationWarning):
        from ns_extract.pipelines.base import Extractor
        assert Extractor is not None


def test_new_imports():
    """Test that new import paths work correctly."""
    # Import locally to test specific path
    from ns_extract.pipelines.core import BasePipeline
    
    assert BasePipeline is not None
    assert issubclass(BasePipeline, (FileOperationsMixin, StudyInputsMixin))


def test_io_components():
    """Test that I/O components are properly exposed."""
    assert hasattr(FileOperationsMixin, 'load_json')
    assert hasattr(StudyInputsMixin, 'load_study_inputs')
    assert hasattr(PipelineOutputsMixin, 'write_pipeline_info')


def test_data_models():
    """Test that data models work correctly."""
    config = PipelineConfig(
        version="1.0.0",
        parameters={"threshold": 0.5}
    )
    assert config.version == "1.0.0"
    assert config.parameters["threshold"] == 0.5

    info = PipelineOutputInfo(
        date="2025-05-21",
        version="1.0.0",
        config_hash="abc123",
        extractor="TestExtractor",
        extractor_kwargs={},
        transform_kwargs={},
        input_pipelines={}
    )
    assert info.version == "1.0.0"


def test_pipeline_inheritance():
    """Test that pipeline inheritance structure works."""
    assert issubclass(IndependentPipeline, Pipeline)
    assert issubclass(DependentPipeline, Pipeline)


def test_extractor_base_requirements():
    """Test that Extractor enforces required attributes."""
    with pytest.raises(ValueError):
        # Should fail without version and schema
        class InvalidExtractor(Extractor):
            pass
        
        InvalidExtractor()

    class ValidExtractor(Extractor):
        _version = "1.0.0"
        _output_schema = PipelineOutputInfo

    extractor = ValidExtractor()
    assert extractor._version == "1.0.0"
