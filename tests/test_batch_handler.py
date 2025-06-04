"""Tests for batch processing functionality."""

from unittest.mock import Mock, patch
from pydantic import BaseModel
from pathlib import Path


from ns_extract.pipelines.api import APIPromptExtractor


class TestSchema(BaseModel):
    text: str
    value: int


class TestDataset:
    """Mock dataset for testing."""
    def __init__(self, data):
        self.data = data

    def get_text(self, study_id):
        """Get text for a study."""
        if study_id in self.data:
            return self.data[study_id]
        return None


class MockStudy:
    """Mock study for testing."""
    def __init__(self, text):
        self.text = text
        self.pubget = Mock()
        self.pubget.text = text


class TestAPIPromptExtractor:
    """Tests for batch processing in APIPromptExtractor."""

    class TestExtractor(APIPromptExtractor):
        """Test implementation of APIPromptExtractor."""
        _prompt = "Test prompt"
        _version = "1.0.0"
        _output_schema = TestSchema

    def test_sync_mode(self):
        """Test synchronous processing."""
        # Setup test inputs
        inputs = {
            "study-1": {"text": "Test text 1"},
            "study-2": {"text": "Test text 2"}
        }

        # Create extractor with mocked client
        client = Mock()
        extractor = self.TestExtractor(
            extraction_model="gpt-4",
            batch=False,
            env_variable="OPENAI_API_KEY"
        )
        extractor.client = client

        # Mock extract_from_text results
        expected_results = [
            {"text": "Result 1", "value": 1},
            {"text": "Result 2", "value": 2}
        ]
        
        with patch('ns_extract.pipelines.api.extract_from_text') as mock_extract:
            mock_extract.side_effect = expected_results
            
            # Run transform
            results = extractor._transform(inputs)

            # Verify results
            assert len(results) == 2
            assert isinstance(results["study-1"], dict)
            assert results["study-1"]["text"] == "Result 1"
            assert results["study-1"]["value"] == 1
            assert isinstance(results["study-2"], dict)
            assert results["study-2"]["text"] == "Result 2"
            assert results["study-2"]["value"] == 2

    def test_batch_mode(self):
        """Test batch processing."""
        # Setup test inputs
        inputs = {
            "study-1": {"text": "Test text 1"},
            "study-2": {"text": "Test text 2"},
            "study-3": {"text": "Test text 3"}
        }

        # Create extractor with batch mode
        client = Mock()
        extractor = self.TestExtractor(
            extraction_model="gpt-4",
            batch=True,
            batch_size=2,  # Process in batches of 2
            env_variable="OPENAI_API_KEY"
        )
        extractor.client = client

        # Mock extract_from_text
        with patch('ns_extract.pipelines.api.extract_from_text') as mock_extract:
            mock_extract.return_value = {"text": "Test Result", "value": 1}

            # Run transform
            results = extractor._transform(inputs)

            # Verify results structure
            assert len(results) == 3
            assert all(study_id in results for study_id in inputs.keys())
            assert all(isinstance(result, dict) for result in results.values())

    def test_transform_dataset(self, tmp_path):
        """Test full dataset transformation."""
        # Create test data with MockStudy instances
        test_data = {
            "study-1": MockStudy("Test text 1"),
            "study-2": MockStudy("Test text 2")
        }
        dataset = TestDataset(test_data)

        # Create extractor
        client = Mock()
        extractor = self.TestExtractor(
            extraction_model="gpt-4",
            env_variable="OPENAI_API_KEY"
        )
        extractor.client = client

        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # Mock extract_from_text
        with patch('ns_extract.pipelines.api.extract_from_text') as mock_extract:
            mock_extract.return_value = {"text": "Result", "value": 1}
            
            # Mock study loading
            with patch('ns_extract.pipelines.base.IndependentPipeline._filter_unprocessed_studies') as mock_filter:
                mock_filter.return_value = dataset

                # Run transform_dataset
                result_dir = extractor.transform_dataset(dataset, output_dir)

                # Verify output directory was created
                assert result_dir.exists()

    def test_error_handling(self):
        """Test error handling in both modes."""
        inputs = {"study-1": {"text": "Test text"}}
        client = Mock()
        
        # Test sync mode error
        extractor = self.TestExtractor(
            extraction_model="gpt-4",
            batch=False,
            env_variable="OPENAI_API_KEY"
        )
        extractor.client = client

        extract_path = 'ns_extract.pipelines.api.extract_from_text'
        with patch(extract_path, side_effect=Exception("Test error")):
            results = extractor._transform(inputs)
            assert not results  # Should return empty dict on error

        # Test batch mode error
        extractor = self.TestExtractor(
            extraction_model="gpt-4",
            batch=True,
            env_variable="OPENAI_API_KEY"
        )
        extractor.client = client

        with patch(extract_path, side_effect=Exception("Test error")):
            results = extractor._transform(inputs)
            assert not results  # Should return empty dict on error

    def test_batch_size_chunking(self):
        """Test that inputs are properly chunked based on batch size."""
        # Create large input set
        inputs = {f"study-{i}": {"text": f"Test text {i}"} for i in range(5)}

        # Create extractor with small batch size
        extractor = self.TestExtractor(
            extraction_model="gpt-4",
            batch=True,
            batch_size=2,
            env_variable="OPENAI_API_KEY"
        )
        extractor.client = Mock()

        with patch('ns_extract.pipelines.api.extract_from_text') as mock_extract:
            mock_extract.return_value = {"text": "Result", "value": 1}
            
            # Process inputs
            results = extractor._transform(inputs)

            # Verify all studies were processed
            assert len(results) == 5
            assert all(f"study-{i}" in results for i in range(5))
