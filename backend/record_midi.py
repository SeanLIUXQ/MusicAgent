"""MIDI import compatibility helpers.

Live Sonic Pi recording has been removed. Browser playback and MIDI file import
now operate on the same structured Composition representation.
"""

from music_engine import midi_to_composition


def import_midi_file(filename):
    return midi_to_composition(filename)


def record_sonic_pi_midi_once(*_args, **_kwargs):
    raise RuntimeError(
        "Sonic Pi recording has been retired. Import a .mid file through the browser workspace."
    )
