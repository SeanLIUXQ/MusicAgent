"""Retired compatibility module.

Audio-to-Sonic-Pi conversion was coupled to an external playback application.
MusicAgent now imports MIDI into editable Composition JSON and renders audio in
the browser.
"""


def call_qwen_audio_to_code(*_args, **_kwargs):
    raise RuntimeError(
        "Audio-to-Sonic-Pi conversion has been retired. Import a MIDI file in the browser workspace."
    )
