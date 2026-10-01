import tempfile
import unittest
from pathlib import Path

import mido

from music_engine import (
    apply_feedback,
    composition_to_midi,
    fallback_composition,
    validate_composition,
)


class MusicEngineTests(unittest.TestCase):
    def test_fallback_is_deterministic_and_playable(self):
        first = fallback_composition("bright electronic song")
        second = fallback_composition("bright electronic song")
        self.assertEqual(first, second)
        self.assertGreaterEqual(len(first["tracks"]), 2)
        self.assertTrue(all(track["notes"] for track in first["tracks"]))

    def test_validation_clamps_untrusted_values(self):
        result = validate_composition(
            {
                "tempo": 999,
                "time_signature": [99, 3],
                "tracks": [
                    {
                        "name": "Lead",
                        "waveform": "invalid",
                        "gain": 4,
                        "pan": -8,
                        "notes": [{"pitch": 500, "start": -4, "duration": 0, "velocity": 0}],
                    }
                ],
            }
        )
        self.assertEqual(result["tempo"], 240)
        self.assertEqual(result["time_signature"], [12, 4])
        track = result["tracks"][0]
        self.assertEqual(track["waveform"], "sine")
        self.assertEqual(track["gain"], 1)
        self.assertEqual(track["pan"], -1)
        self.assertEqual(track["notes"][0]["pitch"], 127)
        self.assertEqual(track["notes"][0]["start"], 0)
        self.assertGreater(track["notes"][0]["duration"], 0)

    def test_feedback_modifies_previous_composition(self):
        previous = fallback_composition("calm piano")
        revised = apply_feedback(previous, "faster and transpose higher")
        self.assertEqual(revised["tempo"], previous["tempo"] + 12)
        self.assertEqual(
            revised["tracks"][0]["notes"][0]["pitch"],
            previous["tracks"][0]["notes"][0]["pitch"] + 2,
        )
        self.assertEqual(previous, fallback_composition("calm piano"), "input must not be mutated")

    def test_polyphonic_midi_events_remain_simultaneous(self):
        composition = validate_composition(
            {
                "title": "Chord",
                "tempo": 120,
                "duration_beats": 4,
                "tracks": [
                    {
                        "name": "Chord",
                        "notes": [
                            {"pitch": 60, "start": 0, "duration": 2, "velocity": 90},
                            {"pitch": 64, "start": 0, "duration": 2, "velocity": 90},
                            {"pitch": 67, "start": 1, "duration": 1, "velocity": 90},
                        ],
                    }
                ],
            }
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "chord.mid"
            composition_to_midi(composition, path)
            midi = mido.MidiFile(path)
            tick = 0
            note_on_ticks = []
            for message in midi.tracks[0]:
                tick += message.time
                if message.type == "note_on" and message.velocity:
                    note_on_ticks.append((message.note, tick))
            self.assertEqual(note_on_ticks, [(60, 0), (64, 0), (67, 480)])


if __name__ == "__main__":
    unittest.main()
