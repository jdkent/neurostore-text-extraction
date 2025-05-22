# Pipeline Components

This directory contains the core pipeline implementation and specific extractors for NeuroStore data processing.

## Structure

- `core/`: Core pipeline abstractions and base classes
- `utils/`: Shared utilities, types and error handling
- Specific pipeline implementations (e.g., `nv_task/`, `participant_demographics/`)

## Key Components

- `Pipeline`: Base class for handling I/O operations
- `Extractor`: Base class for implementing data transformation logic
- `IndependentPipeline`: For processing studies independently
- `DependentPipeline`: For processing studies as a group

## Usage

```python
from ns_extract.pipelines.core import BasePipeline, BaseExtractor
from ns_extract.pipelines.utils import PipelineConfig

# Create a custom extractor
class MyExtractor(BaseExtractor):
    _version = "1.0.0"
    
    def _transform(self, inputs, **kwargs):
        # Transform implementation
        pass

# Use with pipeline
pipeline = BasePipeline(extractor=MyExtractor())
pipeline.transform_dataset(dataset, output_directory)
```

## Migration Guide

If you're using imports from `base.py`, please update to use the new module structure:

```python
# Old imports (deprecated)
from ns_extract.pipelines.base import Pipeline, Extractor

# New imports
from ns_extract.pipelines.core import BasePipeline as Pipeline
from ns_extract.pipelines.core import BaseExtractor as Extractor
