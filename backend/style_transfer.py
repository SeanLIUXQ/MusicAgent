"""Compatibility wrapper for structured arrangement transforms."""

from music_engine import transform_style


def style_transfer_composition(composition, style_request, client=None, log_callback=None):
    return transform_style(composition, style_request, client, log_callback)


def style_transfer_sonic_pi(*_args, **_kwargs):
    raise RuntimeError(
        "Sonic Pi style transfer has been retired. Use style_transfer_composition()."
    )
