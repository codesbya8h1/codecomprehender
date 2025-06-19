"""Token counting utilities for Java code."""

import tiktoken
from typing import List
from code_comprehender.config import DEFAULT_MODEL, MAX_CHUNK_SIZE


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
    
    def is_within_limit(self, text: str, max_tokens: int = MAX_CHUNK_SIZE) -> bool:
        """Check if the text is within the token limit.
        
        Args:
            text: The text to check
            max_tokens: The maximum number of tokens allowed
            
        Returns:
            True if the text is within the limit, False otherwise
        """
        return self.count_tokens(text) <= max_tokens
    
    def estimate_tokens_from_chars(self, char_count: int) -> int:
        """Estimate token count from character count.
        
        Args:
            char_count: Number of characters
            
        Returns:
            Estimated number of tokens
        """
        # This is a rough estimate, actual counting is more accurate
        return int(char_count * 0.25) 