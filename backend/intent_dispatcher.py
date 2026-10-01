"""Compatibility dispatcher for callers migrating to Composition JSON."""

from typing import Any

from music_engine import generate_composition, transform_style, validate_composition


def dispatch_intent(
    user_input: str,
    client: Any,
    original_composition=None,
    user_feedback=None,
    previous_composition=None,
    style_request=None,
    log_callback=None,
    **_kwargs,
):
    previous = previous_composition or original_composition
    if style_request and previous:
        composition = transform_style(previous, style_request, client, log_callback)
        action = "arrange"
    else:
        composition = generate_composition(
            user_input,
            client,
            feedback=user_feedback,
            previous=validate_composition(previous) if previous else None,
            log_callback=log_callback,
        )
        action = "modify" if user_feedback and previous else "generate"
    return {"action": action, "composition": composition}
