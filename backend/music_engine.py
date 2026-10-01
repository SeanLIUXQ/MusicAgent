"""Structured music generation, validation, transformation, and MIDI export."""

from __future__ import annotations

import copy
import json
import math
import os
import random
import re
import uuid
from pathlib import Path
from typing import Any, Callable, Iterable

import mido


LogCallback = Callable[[str], None] | None
ALLOWED_WAVEFORMS = {"sine", "square", "sawtooth", "triangle"}
MAX_TRACKS = 16
MAX_NOTES = 4096
MAX_BEATS = 512.0


def _log(callback: LogCallback, message: str) -> None:
    if callback:
        callback(message)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def _number(value: Any, default: float) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _integer(value: Any, default: int) -> int:
    return int(round(_number(value, default)))


def _safe_id(value: Any, prefix: str) -> str:
    candidate = re.sub(r"[^a-zA-Z0-9_-]", "-", str(value or "")).strip("-")
    return candidate[:64] or f"{prefix}-{uuid.uuid4().hex[:8]}"


def validate_composition(raw: Any) -> dict[str, Any]:
    """Return a bounded, browser-safe composition from untrusted model/user data."""
    if not isinstance(raw, dict):
        raise ValueError("composition must be a JSON object")

    tempo = _integer(raw.get("tempo"), 112)
    tempo = int(_clamp(tempo, 30, 240))
    time_signature = raw.get("time_signature", [4, 4])
    if not isinstance(time_signature, list) or len(time_signature) != 2:
        time_signature = [4, 4]
    numerator = int(_clamp(_integer(time_signature[0], 4), 1, 12))
    denominator = _integer(time_signature[1], 4)
    if denominator not in {1, 2, 4, 8, 16}:
        denominator = 4

    tracks_raw = raw.get("tracks", [])
    if not isinstance(tracks_raw, list):
        raise ValueError("tracks must be an array")

    tracks: list[dict[str, Any]] = []
    note_count = 0
    max_end = 0.0
    for track_index, track_raw in enumerate(tracks_raw[:MAX_TRACKS]):
        if not isinstance(track_raw, dict):
            continue
        notes_raw = track_raw.get("notes", [])
        if not isinstance(notes_raw, list):
            notes_raw = []
        notes: list[dict[str, Any]] = []
        for note_raw in notes_raw:
            if note_count >= MAX_NOTES or not isinstance(note_raw, dict):
                break
            start = _clamp(_number(note_raw.get("start"), 0), 0, MAX_BEATS)
            duration = _clamp(_number(note_raw.get("duration"), 0.5), 0.03125, 32)
            if start + duration > MAX_BEATS:
                duration = max(0.03125, MAX_BEATS - start)
            note = {
                "id": _safe_id(note_raw.get("id"), "note"),
                "pitch": int(_clamp(_integer(note_raw.get("pitch"), 60), 0, 127)),
                "start": round(start, 5),
                "duration": round(duration, 5),
                "velocity": int(_clamp(_integer(note_raw.get("velocity"), 88), 1, 127)),
            }
            notes.append(note)
            note_count += 1
            max_end = max(max_end, note["start"] + note["duration"])

        waveform = str(track_raw.get("waveform", "sine")).lower()
        if waveform not in ALLOWED_WAVEFORMS:
            waveform = "sine"
        tracks.append(
            {
                "id": _safe_id(track_raw.get("id"), f"track-{track_index + 1}"),
                "name": str(track_raw.get("name") or f"Track {track_index + 1}")[:80],
                "instrument": str(track_raw.get("instrument") or "Synth")[:80],
                "waveform": waveform,
                "gain": round(_clamp(_number(track_raw.get("gain"), 0.72), 0, 1), 3),
                "pan": round(_clamp(_number(track_raw.get("pan"), 0), -1, 1), 3),
                "muted": bool(track_raw.get("muted", False)),
                "notes": sorted(notes, key=lambda item: (item["start"], item["pitch"])),
            }
        )

    if not tracks:
        raise ValueError("composition must contain at least one track")

    requested_duration = _number(raw.get("duration_beats"), max_end)
    duration_beats = round(_clamp(max(requested_duration, max_end, numerator * 2), 1, MAX_BEATS), 5)
    return {
        "id": _safe_id(raw.get("id"), "composition"),
        "title": str(raw.get("title") or "Untitled idea")[:120],
        "tempo": tempo,
        "time_signature": [numerator, denominator],
        "duration_beats": duration_beats,
        "tracks": tracks,
    }


def extract_json_object(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else text.strip()
    try:
        value = json.loads(candidate)
    except json.JSONDecodeError:
        start, end = candidate.find("{"), candidate.rfind("}")
        if start < 0 or end <= start:
            raise ValueError("model did not return a JSON object")
        value = json.loads(candidate[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("model response must be a JSON object")
    return value


def _seeded_rng(prompt: str) -> random.Random:
    seed = sum((index + 1) * ord(char) for index, char in enumerate(prompt))
    return random.Random(seed)


def fallback_composition(prompt: str) -> dict[str, Any]:
    """Create a deterministic, playable composition when no model key is configured."""
    lower = prompt.lower()
    rng = _seeded_rng(prompt)
    stable_id = f"local-{sum((index + 1) * ord(char) for index, char in enumerate(prompt)):x}"
    tempo = 112
    if any(word in lower for word in ("slow", "calm", "ambient", "安静", "舒缓", "慢")):
        tempo = 78
    elif any(word in lower for word in ("fast", "dance", "energetic", "快", "活力", "电子")):
        tempo = 132

    root = 60
    if "minor" in lower or "小调" in prompt or "忧伤" in prompt:
        scale = [0, 2, 3, 5, 7, 8, 10]
    else:
        scale = [0, 2, 4, 5, 7, 9, 11]
    progression = [0, 5, 3, 4]
    melody: list[dict[str, Any]] = []
    chords: list[dict[str, Any]] = []
    bass: list[dict[str, Any]] = []

    for bar in range(8):
        chord_degree = progression[bar % len(progression)]
        chord_root = root + scale[chord_degree]
        for offset in (0, 2, 4):
            pitch = root + scale[(chord_degree + offset) % 7]
            if chord_degree + offset >= 7:
                pitch += 12
            chords.append({"pitch": pitch, "start": bar * 4, "duration": 3.75, "velocity": 68})
        bass.extend(
            {"pitch": chord_root - 24, "start": bar * 4 + beat, "duration": 0.8, "velocity": 78}
            for beat in range(4)
        )
        for step in range(8):
            degree = (chord_degree + rng.choice([0, 1, 2, 4, 6])) % 7
            octave = 12 if rng.random() > 0.72 else 0
            melody.append(
                {
                    "id": f"melody-{bar}-{step}",
                    "pitch": root + scale[degree] + octave,
                    "start": bar * 4 + step * 0.5,
                    "duration": rng.choice([0.3, 0.45, 0.8]),
                    "velocity": rng.randint(72, 104),
                }
            )

    title_words = [word for word in re.split(r"\s+", prompt.strip()) if word]
    title = " ".join(title_words[:6]) if title_words else "New idea"
    for index, note in enumerate(chords):
        note["id"] = f"chord-{index}"
    for index, note in enumerate(bass):
        note["id"] = f"bass-{index}"
    return validate_composition(
        {
            "id": stable_id,
            "title": title,
            "tempo": tempo,
            "time_signature": [4, 4],
            "duration_beats": 32,
            "tracks": [
                {"id": "lead", "name": "Lead", "instrument": "Bright lead", "waveform": "triangle", "gain": 0.64, "pan": 0.08, "notes": melody},
                {"id": "harmony", "name": "Harmony", "instrument": "Warm pad", "waveform": "sine", "gain": 0.42, "pan": -0.18, "notes": chords},
                {"id": "bass", "name": "Bass", "instrument": "Mono bass", "waveform": "square", "gain": 0.36, "pan": 0, "notes": bass},
            ],
        }
    )


def _schema_prompt() -> str:
    return """Return only one JSON object with this exact shape:
{
  "title": "short title",
  "tempo": 120,
  "time_signature": [4, 4],
  "duration_beats": 32,
  "tracks": [{
    "id": "lead",
    "name": "Lead",
    "instrument": "Bright lead",
    "waveform": "sine|square|sawtooth|triangle",
    "gain": 0.7,
    "pan": 0,
    "muted": false,
    "notes": [{"id":"n1","pitch":60,"start":0,"duration":0.5,"velocity":90}]
  }]
}
All note positions and durations are in beats. MIDI pitches are integers 0-127. Use 2-8 coherent tracks, no more than 256 notes, and 16-64 beats. Make the result immediately playable and musically complete."""


def generate_composition(
    prompt: str,
    client: Any = None,
    feedback: str | None = None,
    previous: dict[str, Any] | None = None,
    log_callback: LogCallback = None,
) -> dict[str, Any]:
    prompt = str(prompt or "").strip()
    feedback = str(feedback or "").strip()
    if not prompt and not feedback:
        raise ValueError("a music description or feedback is required")

    if client is None:
        _log(log_callback, "Using the built-in composition engine (no DeepSeek key configured).")
        composition = fallback_composition(prompt or feedback)
        return apply_feedback(composition if previous is None else previous, feedback, prompt)

    _log(log_callback, "Generating structured arrangement with DeepSeek...")
    messages: list[dict[str, str]] = [
        {
            "role": "system",
            "content": "You are a music arranger. Create structured note data for a browser synthesizer. " + _schema_prompt(),
        }
    ]
    if previous:
        messages.append(
            {
                "role": "user",
                "content": "Revise this composition while preserving its identity:\n"
                + json.dumps(validate_composition(previous), ensure_ascii=False)
                + f"\nOriginal brief: {prompt}\nFeedback: {feedback}",
            }
        )
    else:
        messages.append({"role": "user", "content": f"Compose music for this brief:\n{prompt}"})

    response = client.chat.completions.create(
        model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
        messages=messages,
        temperature=0.65,
    )
    content = response.choices[0].message.content or ""
    composition = validate_composition(extract_json_object(content))
    _log(log_callback, f"Generated {len(composition['tracks'])} tracks for “{composition['title']}”.")
    return composition


def apply_feedback(composition: dict[str, Any], feedback: str, original_prompt: str = "") -> dict[str, Any]:
    result = copy.deepcopy(validate_composition(composition))
    text = f"{original_prompt} {feedback}".lower()
    if any(word in text for word in ("faster", "quicker", "speed up", "更快", "加速")):
        result["tempo"] = int(_clamp(result["tempo"] + 12, 30, 240))
    if any(word in text for word in ("slower", "slow down", "更慢", "减速")):
        result["tempo"] = int(_clamp(result["tempo"] - 12, 30, 240))
    transpose = 0
    if any(word in text for word in ("higher", "transpose up", "更高", "升调")):
        transpose = 2
    elif any(word in text for word in ("lower", "transpose down", "更低", "降调")):
        transpose = -2
    if transpose:
        for track in result["tracks"]:
            for note in track["notes"]:
                note["pitch"] = int(_clamp(note["pitch"] + transpose, 0, 127))
    if any(word in text for word in ("softer", "quieter", "轻柔", "安静")):
        for track in result["tracks"]:
            track["gain"] = round(track["gain"] * 0.78, 3)
            track["waveform"] = "sine" if track["waveform"] == "square" else track["waveform"]
    return validate_composition(result)


def transform_style(
    composition: dict[str, Any],
    style_request: str,
    client: Any = None,
    log_callback: LogCallback = None,
) -> dict[str, Any]:
    current = validate_composition(composition)
    if client is not None:
        _log(log_callback, "Re-arranging tracks for the requested style...")
        response = client.chat.completions.create(
            model=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
            messages=[
                {
                    "role": "system",
                    "content": "You are a music arranger. Transform the supplied composition into the requested style. " + _schema_prompt(),
                },
                {
                    "role": "user",
                    "content": f"Style request: {style_request}\nComposition:\n{json.dumps(current, ensure_ascii=False)}",
                },
            ],
            temperature=0.55,
        )
        return validate_composition(extract_json_object(response.choices[0].message.content or ""))

    result = copy.deepcopy(current)
    style = style_request.lower()
    if "rock" in style or "摇滚" in style_request:
        result["tempo"] = max(result["tempo"], 124)
        waves = ["sawtooth", "square", "triangle"]
    elif "electronic" in style or "电子" in style_request:
        result["tempo"] = max(result["tempo"], 128)
        waves = ["sawtooth", "square", "sine"]
    elif "ambient" in style or "氛围" in style_request:
        result["tempo"] = min(result["tempo"], 84)
        waves = ["sine", "triangle", "sine"]
        for track in result["tracks"]:
            for note in track["notes"]:
                note["duration"] = round(min(note["duration"] * 1.5, 8), 5)
    elif "jazz" in style or "爵士" in style_request:
        result["tempo"] = int(_clamp(result["tempo"], 92, 132))
        waves = ["triangle", "sine", "square"]
    else:
        waves = ["triangle", "sine", "sawtooth"]
    for index, track in enumerate(result["tracks"]):
        track["waveform"] = waves[index % len(waves)]
    result["title"] = f"{result['title']} · {style_request[:32]}"
    return validate_composition(result)


def iter_midi_events(composition: dict[str, Any]) -> Iterable[tuple[float, int, str, int, int]]:
    """Yield beat, order, type, pitch, velocity; note-offs sort before note-ons."""
    validated = validate_composition(composition)
    for track_index, track in enumerate(validated["tracks"]):
        channel = track_index % 16
        for note in track["notes"]:
            yield note["start"], 1, "note_on", note["pitch"], note["velocity"] | (channel << 8)
            yield note["start"] + note["duration"], 0, "note_off", note["pitch"], channel << 8


def composition_to_midi(composition: dict[str, Any], output_path: str | Path) -> str:
    """Export polyphonic absolute beat events without serializing overlapping notes."""
    validated = validate_composition(composition)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    mid = mido.MidiFile(ticks_per_beat=480)
    track = mido.MidiTrack()
    mid.tracks.append(track)
    track.append(mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(validated["tempo"]), time=0))
    numerator, denominator = validated["time_signature"]
    track.append(mido.MetaMessage("time_signature", numerator=numerator, denominator=denominator, time=0))

    last_tick = 0
    for beat, order, event_type, pitch, packed_velocity in sorted(iter_midi_events(validated)):
        absolute_tick = round(beat * mid.ticks_per_beat)
        delta = max(0, absolute_tick - last_tick)
        channel = (packed_velocity >> 8) & 0x0F
        velocity = packed_velocity & 0xFF
        track.append(mido.Message(event_type, note=pitch, velocity=velocity, channel=channel, time=delta))
        last_tick = absolute_tick

    track.append(mido.MetaMessage("end_of_track", time=0))
    mid.save(output)
    return str(output)


def midi_to_composition(input_path: str | Path) -> dict[str, Any]:
    path = Path(input_path)
    mid = mido.MidiFile(path)
    tempo = 500_000
    active: dict[tuple[int, int, int], list[tuple[float, int]]] = {}
    tracks: list[dict[str, Any]] = []
    max_beat = 0.0
    for track_index, midi_track in enumerate(mid.tracks[:MAX_TRACKS]):
        beat = 0.0
        notes: list[dict[str, Any]] = []
        for message in midi_track:
            beat += message.time / mid.ticks_per_beat
            if message.type == "set_tempo":
                tempo = message.tempo
            if message.type == "note_on" and message.velocity > 0:
                active.setdefault((track_index, message.channel, message.note), []).append((beat, message.velocity))
            elif message.type == "note_off" or (message.type == "note_on" and message.velocity == 0):
                key = (track_index, message.channel, message.note)
                starts = active.get(key)
                if starts:
                    start, velocity = starts.pop(0)
                    notes.append({"pitch": message.note, "start": start, "duration": max(0.03125, beat - start), "velocity": velocity})
                    max_beat = max(max_beat, beat)
        if notes:
            tracks.append({"name": f"MIDI Track {track_index + 1}", "instrument": "Imported MIDI", "waveform": ["triangle", "sine", "square", "sawtooth"][track_index % 4], "notes": notes})
    if not tracks:
        raise ValueError("MIDI file does not contain completed note events")
    return validate_composition({"title": path.stem, "tempo": round(mido.tempo2bpm(tempo)), "duration_beats": max_beat, "tracks": tracks})


def save_composition(composition: dict[str, Any], output_path: str | Path) -> str:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(validate_composition(composition), ensure_ascii=False, indent=2), encoding="utf-8")
    return str(output)
