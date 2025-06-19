"""Token counting utilities for Java code."""

import tiktoken

from code_comprehender.config import DEFAULT_MODEL


class TokenCounter:
    """Handles token counting for text using tiktoken."""

    def __init__(self, model_name: str = DEFAULT_MODEL):
        """Initialize the token counter with a specific model.

        Args:
            model_name: The name of the model to use for token counting
        """
        try:
            self.encoding = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to cl100k_base encoding if model not found
            self.encoding = tiktoken.get_encoding("cl100k_base")

    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in the given text.

        Args:
            text: The text to count tokens for

        Returns:
            The number of tokens in the text
        """
        return len(self.encoding.encode(text))
