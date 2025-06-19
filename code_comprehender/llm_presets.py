"""LLM model presets with optimized configurations for different OpenAI models."""

from dataclasses import dataclass
from typing import Dict


@dataclass
class LLMPreset:
    """Configuration preset for an LLM model."""

    name: str
    model_name: str
    context_window: int
    max_chunk_size: int
    temperature: float


# Define all available LLM presets
LLM_PRESETS: Dict[str, LLMPreset] = {
    "gpt-3.5-turbo": LLMPreset(
        name="gpt-3.5-turbo",
        model_name="gpt-3.5-turbo",
        context_window=16385,
        max_chunk_size=15000,
        temperature=0.1,
    ),
    "gpt-4o-mini": LLMPreset(
        name="gpt-4o-mini",
        model_name="gpt-4o-mini",
        context_window=128000,
        max_chunk_size=120000,
        temperature=0.1,
    ),
    "gpt-4o": LLMPreset(
        name="gpt-4o",
        model_name="gpt-4o",
        context_window=128000,
        max_chunk_size=120000,
        temperature=0.1,
    ),
}


def get_preset(preset_name: str) -> LLMPreset:
    """Get an LLM preset by name.

    Args:
        preset_name: Name of the preset to retrieve

    Returns:
        LLMPreset object

    Raises:
        ValueError: If preset name is not found
    """
    if preset_name not in LLM_PRESETS:
        available = ", ".join(LLM_PRESETS.keys())
        raise ValueError(
            f"Unknown preset '{preset_name}'. Available presets: {available}"
        )

    return LLM_PRESETS[preset_name]


def get_default_preset() -> LLMPreset:
    """Get the default LLM preset.

    Returns:
        Default LLMPreset (gpt-4o-mini)
    """
    return LLM_PRESETS["gpt-4o-mini"]
