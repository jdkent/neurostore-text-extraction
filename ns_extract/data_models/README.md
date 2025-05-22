# Data Models

This directory contains the core data models used throughout the NeuroStore extraction system. These models provide structured data validation and serialization using Pydantic.

## Core Models

### PipelineConfig

Configuration model for pipeline execution:
```python
from ns_extract.data_models import PipelineConfig

config = PipelineConfig(
    version="1.0.0",
    parameters={
        "threshold": 0.5,
        "max_tokens": 1000
    }
)
```

### PipelineOutputInfo

Metadata about pipeline execution results:
```python
from ns_extract.data_models import PipelineOutputInfo

info = PipelineOutputInfo(
    date="2025-05-21",
    version="1.0.0",
    config_hash="abc123",
    extractor="TaskExtractor",
    extractor_kwargs={"model": "gpt-4"},
    transform_kwargs={"threshold": 0.5},
    input_pipelines={}
)
```

### StudyOutputJson

Information about individual study processing:
```python
from ns_extract.data_models import StudyOutputJson

study_info = StudyOutputJson(
    date="2025-05-21",
    inputs={
        "text.txt": "md5hash123",
        "coords.csv": "md5hash456"
    },
    valid=True
)
```

## Validation

All models enforce validation on initialization:
```python
try:
    config = PipelineConfig(invalid_data)
except ValidationError as e:
    print(f"Invalid configuration: {e}")
```

## Best Practices

1. Use type hints with models
2. Validate data at boundaries
3. Document model fields
4. Handle validation errors appropriately

## Migration Guide

If you're using raw dictionaries, migrate to these models for better type safety and validation:

```python
# Old approach (error-prone)
config = {
    "version": "1.0.0",
    "params": {}  # Typo in key name!
}

# New approach (validated)
config = PipelineConfig(
    version="1.0.0",
    parameters={}  # ValidationError if wrong key used
)
