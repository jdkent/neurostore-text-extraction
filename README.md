# NeuroStore Text Extraction

A Python package for extracting structured information from neuroscience papers.

## Project Organization

```
ns_extract/
├── io/                  # Input/Output operations
│   ├── file_ops.py     # File handling utilities
│   ├── study_inputs.py # Study data loading
│   └── pipeline_outputs.py # Result output handling
├── data_models/        # Data structure definitions
│   ├── config.py      # Configuration models
│   ├── pipeline_info.py # Pipeline metadata
│   └── study_info.py  # Study information models
└── pipelines/         # Pipeline implementations
    ├── core/         # Core pipeline abstractions
    ├── utils/        # Shared utilities
    ├── nv_task/      # Task extraction pipeline
    ├── participant_demographics/ # Demographics pipeline
    └── ...           # Other pipeline implementations
```

## Installation

```bash
pip install ns-extract
```

## Quick Start

```python
from ns_extract import Dataset
from ns_extract.pipelines import TaskExtractor

# Create dataset
dataset = Dataset("path/to/studies")

# Initialize pipeline
pipeline = TaskExtractor()

# Process studies
pipeline.transform_dataset(dataset, "output/dir")
```

## Migration Guide

### Version 1.0 Changes

The codebase has been reorganized for better modularity and maintainability. Key changes include:

1. New Module Structure
```python
# Old imports (deprecated)
from ns_extract.pipelines.base import Pipeline, Extractor

# New imports (recommended)
from ns_extract.pipelines.core import BasePipeline, BaseExtractor
```

2. Improved Data Models
```python
# Old approach
config = {"version": "1.0", "params": {}}

# New approach
from ns_extract.data_models import PipelineConfig
config = PipelineConfig(version="1.0", parameters={})
```

3. Better I/O Organization
```python
# Old approach
from ns_extract.pipelines.base import Pipeline

# New approach
from ns_extract.io import FileOperationsMixin, StudyInputsMixin
```

### Deprecation Notice

The `base.py` module is maintained for backwards compatibility but will be removed in version 2.0. Update your imports to use the new module structure.

## Development

### Setting up the development environment

1. Clone the repository
```bash
git clone https://github.com/your-org/neurostore-text-extraction.git
cd neurostore-text-extraction
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies
```bash
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest tests/
```

## Documentation

Each major component has its own README with detailed documentation:
- [Pipeline Documentation](ns_extract/pipelines/README.md)
- [I/O Documentation](ns_extract/io/README.md)
- [Data Models Documentation](ns_extract/data_models/README.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.
