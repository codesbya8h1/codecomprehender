"""Async LLM client for parallel code comprehender processing."""

import asyncio
from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from code_comprehender.config import (
    DEFAULT_MODEL,
    OPENAI_API_KEY,
    get_performance_profile,
)
from code_comprehender.java_parser import CodeChunk
from code_comprehender.logger import get_logger, log_warning
from code_comprehender.prompts import DOCUMENTATION_PROMPT


class AsyncLLMClient:
    """Async LLM client for parallel processing."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        performance_profile: str = "balanced",
    ):
        """Initialize the async LLM client.

        Args:
            model_name: Name of the model to use
            api_key: OpenAI API key (uses environment variable if not provided)
            performance_profile: Performance profile for concurrency settings

        Raises:
            ValueError: If API key is not provided or found in environment
        """
        self.logger = get_logger(self.__class__.__name__)

        if not api_key and not OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or provide api_key parameter."
            )

        self.model_name = model_name
        self.api_key = api_key or OPENAI_API_KEY

        # Get performance profile settings
        profile_settings = get_performance_profile(performance_profile)
        self.max_concurrent_requests = profile_settings["max_concurrent_llm_requests"]
        self.rate_limit_delay = profile_settings["rate_limit_delay"]

        # Create sync LLM for fallback
        self.llm = ChatOpenAI(
            model=model_name,
            api_key=self.api_key,
            temperature=0.1,
            max_tokens=None,
        )

        # Semaphore to limit concurrent requests
        self._semaphore = asyncio.Semaphore(self.max_concurrent_requests)

        # Dynamic rate limiting
        self._last_request_time = 0
        self._request_count = 0
        self._start_time = None

        # Remove verbose initialization logging

    async def document_code_async(self, code: str, chunk_name: str = "chunk") -> str:
        """Generate comprehensive documentation for Java code asynchronously.

        Args:
            code: Java source code to document
            chunk_name: Name of the chunk for logging

        Returns:
            Documented Java code with comprehensive comments

        Raises:
            Exception: If LLM request fails
        """
        async with self._semaphore:
            try:
                # Adaptive rate limiting
                await self._apply_rate_limiting()

                # Use langchain's async invoke
                messages = [
                    SystemMessage(content=DOCUMENTATION_PROMPT),
                    HumanMessage(
                        content=f"Please add comprehensive documentation to this Java code:\n\n{code}"
                    ),
                ]

                # Run the sync LLM call in a thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                response = await loop.run_in_executor(
                    None, lambda: self.llm.invoke(messages)
                )

                self._request_count += 1
                return response.content.strip()

            except Exception as e:
                self.logger.error(f"Failed to document {chunk_name}: {e}")
                raise Exception(
                    f"Failed to generate documentation for {chunk_name}: {e}"
                )

    async def _apply_rate_limiting(self):
        """Apply adaptive rate limiting based on request patterns."""
        import time

        if self._start_time is None:
            self._start_time = time.time()

        current_time = time.time()

        # Calculate current request rate
        elapsed_time = current_time - self._start_time
        if elapsed_time > 0:
            current_rate = self._request_count / elapsed_time

            # Adaptive delay based on request rate
            if current_rate > 10:  # More than 10 requests per second
                delay = self.rate_limit_delay * 2
            elif current_rate > 5:  # More than 5 requests per second
                delay = self.rate_limit_delay * 1.5
            else:
                delay = self.rate_limit_delay
        else:
            delay = self.rate_limit_delay

        # Ensure minimum time between requests
        time_since_last = current_time - self._last_request_time
        if time_since_last < delay:
            await asyncio.sleep(delay - time_since_last)

        self._last_request_time = time.time()

    async def document_chunks_async(self, chunks: List[CodeChunk]) -> List[str]:
        """Document multiple code chunks in parallel.

        Args:
            chunks: List of code chunks to document

        Returns:
            List of documented code strings
        """
        # Remove verbose chunk processing logging

        # Create tasks for all chunks
        tasks = []
        for i, chunk in enumerate(chunks):
            task = self._document_chunk_with_progress(chunk, i + 1, len(chunks))
            tasks.append(task)

        # Execute all tasks concurrently
        documented_chunks = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results and handle exceptions
        results = []
        for i, result in enumerate(documented_chunks):
            if isinstance(result, Exception):
                log_warning(f"Failed to document chunk {chunks[i].name}: {result}")
                # Include original code if documentation fails
                results.append(chunks[i].content)
            else:
                results.append(result)

        # Remove verbose completion logging
        return results

    async def _document_chunk_with_progress(
        self, chunk: CodeChunk, current: int, total: int
    ) -> str:
        """Document a single chunk with progress logging.

        Args:
            chunk: Code chunk to document
            current: Current chunk number
            total: Total number of chunks

        Returns:
            Documented code string
        """
        # Remove verbose chunk progress logging

        try:
            documented_code = await self.document_code_async(chunk.content, chunk.name)
            return documented_code
        except Exception as e:
            self.logger.error(f"Failed to document chunk {chunk.name}: {e}")
            # Return original code if documentation fails
            return chunk.content

    def document_code_sync(self, code: str) -> str:
        """Synchronous fallback for single code documentation.

        Args:
            code: Java source code to document

        Returns:
            Documented Java code
        """
        try:
            messages = [
                SystemMessage(content=DOCUMENTATION_PROMPT),
                HumanMessage(
                    content=f"Please add comprehensive documentation to this Java code:\n\n{code}"
                ),
            ]

            response = self.llm.invoke(messages)
            return response.content.strip()

        except Exception as e:
            raise Exception(f"Failed to generate documentation: {e}")


class AsyncLLMClientManager:
    """Manager for async LLM operations with proper lifecycle management."""

    def __init__(
        self,
        model_name: str = DEFAULT_MODEL,
        api_key: Optional[str] = None,
        performance_profile: str = "balanced",
    ):
        """Initialize the async LLM client manager.

        Args:
            model_name: Name of the model to use
            api_key: OpenAI API key
            performance_profile: Performance profile for concurrency settings
        """
        self.model_name = model_name
        self.api_key = api_key
        self.performance_profile = performance_profile
        self._client = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = AsyncLLMClient(
            model_name=self.model_name,
            api_key=self.api_key,
            performance_profile=self.performance_profile,
        )
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        # Cleanup if needed
        self._client = None

    @staticmethod
    def run_async_documentation(
        chunks: List[CodeChunk], performance_profile: str = "balanced", **kwargs
    ) -> List[str]:
        """Convenience method to run async documentation from sync code.

        Args:
            chunks: List of code chunks to document
            performance_profile: Performance profile for concurrency settings
            **kwargs: Additional arguments for AsyncLLMClientManager

        Returns:
            List of documented code strings
        """

        async def _document():
            async with AsyncLLMClientManager(
                performance_profile=performance_profile, **kwargs
            ) as client:
                return await client.document_chunks_async(chunks)

        # Run the async function
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        return loop.run_until_complete(_document())
