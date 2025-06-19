"""LLM client for code comprehender."""

from typing import List, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from code_comprehender.config import DEFAULT_MODEL, OPENAI_API_KEY
from code_comprehender.java_parser import CodeChunk
from code_comprehender.logger import get_logger, log_progress, log_warning
from code_comprehender.prompts import DOCUMENTATION_PROMPT


class LLMClient:
    """Handles communication with LLM."""

    def __init__(self, model_name: str = DEFAULT_MODEL, api_key: Optional[str] = None):
        """Initialize the LLM client.

        Args:
            model_name: Name of the model to use
            api_key: OpenAI API key (uses environment variable if not provided)

        Raises:
            ValueError: If API key is not provided or found in environment
        """
        self.logger = get_logger(self.__class__.__name__)

        if not api_key and not OPENAI_API_KEY:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or provide api_key parameter."
            )

        self.llm = ChatOpenAI(
            model=model_name,
            api_key=api_key or OPENAI_API_KEY,
            temperature=0.1,  # Low temperature for consistent documentation
            max_tokens=None,  # Let the model decide based on context
        )

    def document_code(self, code: str) -> str:
        """Generate comprehensive documentation for Java code.

        Args:
            code: Java source code to document

        Returns:
            Documented Java code with comprehensive comments

        Raises:
            Exception: If LLM request fails
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

    def document_chunks(self, chunks: List[CodeChunk]) -> List[str]:
        """Document multiple code chunks.

        Args:
            chunks: List of code chunks to document

        Returns:
            List of documented code strings

        Raises:
            Exception: If any LLM request fails
        """
        documented_chunks = []

        for i, chunk in enumerate(chunks):
            log_progress(
                f"Processing chunk: {chunk.name} ({chunk.token_count:,} tokens)",
                i + 1,
                len(chunks),
            )

            try:
                documented_code = self.document_code(chunk.content)
                documented_chunks.append(documented_code)

            except Exception as e:
                log_warning(f"Failed to document chunk {chunk.name}: {e}")
                # Include original code if documentation fails
                documented_chunks.append(chunk.content)

        return documented_chunks

    def test_connection(self) -> bool:
        """Test the connection to the LLM.

        Returns:
            True if connection is successful, False otherwise
        """
        try:
            test_message = SystemMessage(
                content="Respond with 'OK' if you can see this message."
            )
            response = self.llm.invoke([test_message])
            return "OK" in response.content.upper()
        except Exception:
            return False
