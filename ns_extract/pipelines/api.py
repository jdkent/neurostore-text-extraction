"""Pipeline for extracting information using LLM APIs."""

from typing import Optional, Type, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor
import json
import logging
import os
from pathlib import Path
from pydantic import BaseModel
from openai import OpenAI
from .base import IndependentPipeline, Extractor
from .batch_handler import BatchHandler
from publang.extract import extract_from_text


logger = logging.getLogger(__name__)


class APIPromptExtractor(Extractor, IndependentPipeline):
    """Pipeline that uses a prompt and a pydantic schema to extract information from text."""

    _prompt: str = None  # Prompt template for extraction
    _extraction_schema: Type[BaseModel] = None  # Schema used for LLM extraction
    _data_pond_inputs = {("pubget", "ace"): ("text",)}
    _pipeline_inputs = {}

    def __init__(
        self,
        extraction_model: str,
        batch: bool = False,
        batch_size: int = 20,
        completion_window: str = "24h",
        temp_dir: Optional[Path] = None,
        env_variable: Optional[str] = None,
        env_file: Optional[str] = None,
        client_url: Optional[str] = None,
        **kwargs,
    ):
        """Initialize the prompt-based pipeline.

        Args:
            extraction_model: Model to use for extraction (e.g., 'gpt-4')
            batch: Whether to use batch processing (default: False)
            batch_size: Maximum requests per batch (default: 20)
            completion_window: Time window for batch completion (default: '24h')
            temp_dir: Directory for temporary batch files
            env_variable: Environment variable containing API key
            env_file: Path to file containing API key
            client_url: Optional URL for OpenAI client
            **kwargs: Additional arguments for the completion function
        """
        if not self._prompt:
            raise ValueError("Subclass must define _prompt template")
        if not self._extraction_schema:
            self._extraction_schema = self._output_schema

        self.extraction_model = extraction_model
        self.batch = batch
        self.batch_size = batch_size
        self.completion_window = completion_window
        self.temp_dir = temp_dir
        self.env_variable = env_variable
        self.env_file = env_file
        self.client_url = client_url
        self.kwargs = kwargs

        # Initialize OpenAI client
        self.client = self._load_client()

        super().__init__()

    def _load_client(self) -> OpenAI:
        """Load the OpenAI client.

        Returns:
            OpenAI client instance

        Raises:
            ValueError: If no API key provided
        """
        api_key = self._get_api_key()
        if not api_key:
            raise ValueError("No API key provided")
        return OpenAI(api_key=api_key, base_url=self.client_url)

    def _get_api_key(self) -> Optional[str]:
        """Read the API key from environment variable or file."""
        if self.env_variable:
            api_key = os.getenv(self.env_variable)
            if api_key:
                return api_key

        if self.env_file:
            try:
                with open(self.env_file) as f:
                    key_parts = f.read().strip().split("=")
                    if len(key_parts) == 2:
                        return key_parts[1]
                    logger.warning("Invalid format in API key file")
            except FileNotFoundError:
                logger.error(f"API key file not found: {self.env_file}")

        return None

    def _prepare_messages(self, text: str) -> List[Dict[str, str]]:
        """Prepare message list for chat completion.

        Args:
            text: Input text content

        Returns:
            List of message objects for chat completion
        """
        # Replace $ with $$ to escape $ signs in the prompt
        text = text.replace("$", "$$")

        return [
            {
                "role": "user",
                "content": self._prompt + "\n Call the extractData function to save the output.",
            }
        ]

    def _process_single_request(self, study_id: str, study_inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single request, either in batch or sync mode."""
        text = study_inputs["text"]
        completion_config = {
            **self.kwargs,
            "messages": self._prepare_messages(text),
            "output_schema": self._extraction_schema.model_json_schema(),
            "model": self.extraction_model,
            "client": self.client,
        }

        try:
            result = extract_from_text(text, **completion_config)
            if result:
                return {study_id: result}
            logger.warning(f"No results for study {study_id}")
        except Exception as e:
            logger.error(f"Error processing study {study_id}: {str(e)}")
        
        return {}

    def _transform(self, inputs: Dict[str, Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Execute LLM-based extraction using processed inputs."""
        if not self.batch:
            results = {}
            for study_id, study_inputs in inputs.items():
                result = self._process_single_request(study_id, study_inputs)
                results.update(result)
            return results

        # Process in batches using threads
        results = {}
        batch_chunks = []
        current_chunk = {}

        # Split inputs into batch-sized chunks
        for study_id, study_inputs in inputs.items():
            current_chunk[study_id] = study_inputs
            if len(current_chunk) >= self.batch_size:
                batch_chunks.append(current_chunk)
                current_chunk = {}
        if current_chunk:
            batch_chunks.append(current_chunk)

        # Process chunks in parallel
        with ThreadPoolExecutor(max_workers=min(len(batch_chunks), 5)) as executor:
            futures = []
            for chunk in batch_chunks:
                future = executor.submit(lambda x: {
                    sid: self._process_single_request(sid, sinputs)[sid]
                    for sid, sinputs in x.items()
                    if self._process_single_request(sid, sinputs)
                }, chunk)
                futures.append(future)

            # Collect results
            for future in futures:
                try:
                    chunk_results = future.result()
                    results.update(chunk_results)
                except Exception as e:
                    logger.error(f"Error processing batch: {str(e)}")

        return results
