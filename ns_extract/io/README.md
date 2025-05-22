# I/O Components

This directory contains components for handling input/output operations in the NeuroStore extraction system.

## Components

### FileOperationsMixin

Provides core file operations functionality:
- Reading/writing JSON files
- Calculating file hashes
- Managing directories

```python
from ns_extract.io import FileOperationsMixin

class MyHandler(FileOperationsMixin):
    def process(self):
        data = self.load_json("input.json")
        self.write_json("output.json", processed_data)
```

### StudyInputsMixin

Handles loading and validating study input data:
- Text extraction
- Coordinate data
- Metadata processing

```python
from ns_extract.io import StudyInputsMixin

class MyPipeline(StudyInputsMixin):
    def load_study(self, study_id):
        inputs = self.load_study_inputs(study_id)
        return self.process_inputs(inputs)
```

### PipelineOutputsMixin

Manages pipeline output operations:
- Writing results
- Maintaining output structure
- Version tracking

```python
from ns_extract.io import PipelineOutputsMixin

class MyOutputHandler(PipelineOutputsMixin):
    def save_results(self, results):
        self.write_pipeline_info(output_dir, pipeline_info)
        self.write_study_results(output_dir, study_id, results)
```

## Migration Guide

The I/O components are designed to be used as mixins. Each provides specific functionality that can be combined as needed:

```python
class MyPipeline(FileOperationsMixin, StudyInputsMixin, PipelineOutputsMixin):
    """Pipeline with complete I/O capabilities."""
    pass
```

## Best Practices

1. Use appropriate mixins for your needs
2. Handle exceptions from I/O operations
3. Validate input data before processing
4. Maintain consistent output structure
