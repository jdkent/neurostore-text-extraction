"""Module for handling batch processing with OpenAI API."""

import asyncio
import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Type, Any

from openai import OpenAI
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BatchHandler:
    """
    Handles batched requests to OpenAI API with temporary file management,
    status monitoring, and result mapping.
    """

    def __init__(
        self,
        client: OpenAI,
        extraction_model: str,
        output_schema: Type[BaseModel],
        batch_size: int = 20,
        completion_window: str = "24h",
        temp_dir: Optional[Path] = None,
    ):
        """Initialize BatchHandler.

        Args:
            client: OpenAI client instance
            extraction_model: Name of the model to use (e.g., 'gpt-4')
            output_schema: Pydantic model for validating results
            batch_size: Maximum requests per batch (default: 20, max: 50000)
            completion_window: Time window for batch completion ('24h')
            temp_dir: Directory for temporary files (default: /tmp/openai_batch)
        """
        self.client = client
        self.extraction_model = extraction_model
        self.output_schema = output_schema
        self.batch_size = min(batch_size, 50000)  # OpenAI limit
        self.completion_window = completion_window
        self.temp_dir = temp_dir or Path("/tmp/openai_batch")
        self.current_batch = []
        self.pending_batches = {}  # batch_id -> file_id mapping
        self.results = {}
        self.errors = {}
        self.current_batch_id = None

    def prepare_batch_request(
        self,
        text: str,
        custom_id: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Dict[str, Any]:
        """Format a single request for batch processing.

        Args:
            text: Input text content
            custom_id: Unique identifier for tracking request
            messages: List of message objects for chat completion
            **kwargs: Additional parameters for the completion request

        Returns:
            Dict containing formatted request for batch API
        """
        return {
            "custom_id": custom_id,
            "method": "POST",
            "url": "/v1/chat/completions",
            "body": {
                "model": self.extraction_model,
                "messages": messages,
                **kwargs
            }
        }

    async def add_request(
        self,
        custom_id: str,
        text: str,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> bool:
        """Add request to current batch.

        Args:
            custom_id: Unique identifier for tracking request
            text: Input text content
            messages: List of message objects for chat completion
            **kwargs: Additional parameters for the completion request

        Returns:
            True if batch is full and was submitted, False otherwise

        Raises:
            ValueError: If batch_size exceeds OpenAI limit
        """
        if self.batch_size > 50000:
            raise ValueError("Batch size cannot exceed 50000 requests")

        request = self.prepare_batch_request(text, custom_id, messages, **kwargs)
        self.current_batch.append(request)

        if len(self.current_batch) >= self.batch_size:
            batch_id = await self.submit_current_batch()
            if batch_id:
                self.current_batch_id = batch_id
                return True
        return False

    async def submit_current_batch(self) -> Optional[str]:
        """Submit current batch to OpenAI API.

        Returns:
            Batch ID if successful, None otherwise

        Raises:
            IOError: If file operations fail
            Exception: If batch submission fails
        """
        if not self.current_batch:
            return None

        # Create temp JSONL file
        batch_id = uuid.uuid4().hex
        batch_file = self.temp_dir / f"{batch_id}.jsonl"
        self.temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Write requests to JSONL
            with open(batch_file, "w") as f:
                for request in self.current_batch:
                    json.dump(request, f)
                    f.write("\n")

            # Upload file
            file = await self.client.files.create(
                file=batch_file.open("rb"),
                purpose="batch"
            )

            # Create batch
            batch = await self.client.batches.create(
                input_file_id=file.id,
                endpoint="/v1/chat/completions",
                completion_window=self.completion_window
            )

            self.pending_batches[batch.id] = file.id
            self.current_batch = []

            return batch.id

        except Exception as e:
            logger.error(f"Failed to submit batch: {str(e)}")
            raise
        finally:
            # Cleanup temp file
            if batch_file.exists():
                batch_file.unlink()

    async def monitor_batch(self, batch_id: str) -> bool:
        """Monitor batch status until completion.

        Args:
            batch_id: ID of the batch to monitor

        Returns:
            True if batch completed successfully, False otherwise
        """
        while True:
            try:
                batch = await self.client.batches.retrieve(batch_id)

                if batch.status == "completed":
                    await self._process_batch_results(batch)
                    return True

                elif batch.status in ("failed", "expired", "cancelled"):
                    await self._process_batch_errors(batch)
                    return False

                # Poll every 5 seconds
                await asyncio.sleep(5)

            except Exception as e:
                logger.error(f"Error monitoring batch {batch_id}: {str(e)}")
                return False

    async def _process_batch_results(self, batch) -> None:
        """Process completed batch results.

        Args:
            batch: Completed batch object from OpenAI API
        """
        try:
            file_content = await self.client.files.content(batch.output_file_id)

            for line in file_content.text.splitlines():
                result = json.loads(line)
                custom_id = result["custom_id"]

                if result["response"]["error"]:
                    self.errors[custom_id] = result["response"]["error"]
                else:
                    self.results[custom_id] = result["response"]["body"]

        except Exception as e:
            logger.error(f"Error processing batch results: {str(e)}")
            raise

    async def _process_batch_errors(self, batch) -> None:
        """Process errors from failed batch.

        Args:
            batch: Failed batch object from OpenAI API
        """
        try:
            if batch.error_file_id:
                error_content = await self.client.files.content(batch.error_file_id)
                for line in error_content.text.splitlines():
                    error = json.loads(line)
                    custom_id = error["custom_id"]
                    self.errors[custom_id] = error["error"]
        except Exception as e:
            logger.error(f"Error processing batch errors: {str(e)}")
            raise

    def get_results(self) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Get processed results and errors.

        Returns:
            Tuple containing:
            - Dict mapping study IDs to validated results
            - Dict mapping study IDs to error messages
        """
        validated_results = {}

        for study_id, result in self.results.items():
            try:
                validated = self.output_schema.model_validate(result)
                validated_results[study_id] = validated
            except Exception as e:
                self.errors[study_id] = f"Validation error: {str(e)}"

        return validated_results, self.errors

    async def cleanup(self) -> None:
        """Clean up temporary files and API resources."""
        # Submit any remaining requests
        if self.current_batch:
            await self.submit_current_batch()

        # Clean up temp directory
        try:
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
        except Exception as e:
            logger.error(f"Error cleaning up temporary files: {str(e)}")
