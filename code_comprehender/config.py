"""Configuration settings for the Code Comprehender."""

import os

from dotenv import load_dotenv

load_dotenv()

# Import preset system
from code_comprehender.llm_presets import get_default_preset

# LLM Configuration (using preset system)
_default_preset = get_default_preset()
DEFAULT_MODEL = _default_preset.model_name
MAX_CHUNK_SIZE = _default_preset.max_chunk_size

# Performance optimization settings for different repository sizes and use cases
PERFORMANCE_PROFILES = {
    "conservative": {
        "description": "Safe settings for small repos or API rate limit concerns",
        "best_for": "Small repositories (≤20 files), limited API quotas, or unstable connections",
        "max_concurrent_files": 3,
        "max_concurrent_llm_requests": 5,
        "max_concurrent_viz_requests": 3,
        "rate_limit_delay": 0.5,
        "expected_speedup": "2-3x faster than sequential",
    },
    "balanced": {
        "description": "Good balance of speed and stability for most repositories",
        "best_for": "Medium repositories (20-50 files), general use, default choice",
        "max_concurrent_files": 8,
        "max_concurrent_llm_requests": 10,
        "max_concurrent_viz_requests": 6,
        "rate_limit_delay": 0.2,
        "expected_speedup": "4-6x faster than sequential",
    },
    "aggressive": {
        "description": "Maximum performance for large repositories with high API limits",
        "best_for": "Large repositories (50+ files), high API quotas, fast connections",
        "max_concurrent_files": 15,
        "max_concurrent_llm_requests": 20,
        "max_concurrent_viz_requests": 12,
        "rate_limit_delay": 0.1,
        "expected_speedup": "8-12x faster than sequential",
    },
}


def get_performance_profile(profile_name: str = "balanced") -> dict:
    """Get performance profile settings.

    Args:
        profile_name: Profile name (conservative, balanced, aggressive)

    Returns:
        Dictionary with performance settings
    """
    return PERFORMANCE_PROFILES.get(profile_name, PERFORMANCE_PROFILES["balanced"])


# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# GitHub Configuration
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# Output directory
OUTPUT_DIR = "output"
