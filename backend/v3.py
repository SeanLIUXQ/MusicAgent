"""Compatibility exports for the structured browser-native music engine.

The former Sonic Pi/Ruby generation pipeline has been retired. New code should
import from ``music_engine`` directly.
"""

from music_engine import (  # noqa: F401
    apply_feedback,
    composition_to_midi,
    extract_json_object,
    fallback_composition,
    generate_composition,
    midi_to_composition,
    save_composition,
    transform_style,
    validate_composition,
)


def multi_agent_generate_sonic_pi(*args, **kwargs):
    raise RuntimeError(
        "Sonic Pi output has been removed. Use generate_composition() and the browser audio engine."
    )


def sonic_pi_code_to_midi(*args, **kwargs):
    raise RuntimeError(
        "Sonic Pi compilation has been removed. Use composition_to_midi() with Composition JSON."
    )
