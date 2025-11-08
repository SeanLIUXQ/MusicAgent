#!/usr/bin/env python3
"""
midi_to_audio.py

Minimal, robust MIDI -> WAV renderer (and optional MP3 export).
- Self-contained MIDI parser (no mido dependency).
- Simple additive synth with ADSR-ish envelope.
- Writes WAV (using scipy) and tries MP3 via pydub/ffmpeg if available.

Usage:
    python midi_to_audio.py path/to/input.mid [--wav OUT.wav] [--mp3 OUT.mp3] [--sr 44100]

Requirements:
    - numpy, scipy  (for synthesis and WAV writing)
    - pydub + ffmpeg (optional, for MP3 export)
If pydub/ffmpeg missing, the script still produces WAV; you can convert locally:
    ffmpeg -i output.wav output.mp3
"""

import sys
import os
import math
import argparse
from pathlib import Path
import traceback

# --- try imports that are required ---
try:
    import numpy as np
    from scipy.io import wavfile
except Exception as e:
    print("ERROR: This script requires numpy and scipy. Install them (e.g., pip install numpy scipy).")
    raise

# -------------------------
# Minimal MIDI parsing helpers
# -------------------------
def read_uint16_be(b, i):
    return int.from_bytes(b[i:i+2], byteorder='big')

def read_uint32_be(b, i):
    return int.from_bytes(b[i:i+4], byteorder='big')

def read_varlen(b, i):
    """
    Read a MIDI variable-length integer starting at b[i].
    Returns (value, new_index).
    """
    value = 0
    while True:
        if i >= len(b):
            raise IndexError("Unexpected end of data while reading varlen")
        byte = b[i]
        i += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, i

# -------------------------
# MIDI file parsing
# -------------------------
def parse_midi_bytes(data_bytes):
    """
    Parse MIDI file bytes into a list of time-ordered events.
    Returns: ticks_per_beat, list_of_events
    where each event is a tuple (abs_ticks, event_tuple)
    and event_tuple is one of:
      ('meta', meta_type, meta_data_bytes)
      ('midi', msg_type, channel, d1, d2)  # for 2-byte messages (note on/off etc)
      ('midi1', msg_type, channel, d1)     # for 1-byte data messages (program change, etc)
    """
    pos = 0
    if len(data_bytes) < 14 or data_bytes[0:4] != b'MThd':
        raise ValueError("Not a valid MIDI file (missing MThd)")
    hdr_len = read_uint32_be(data_bytes, 4)
    if hdr_len < 6:
        raise ValueError("Invalid MIDI header length")
    fmt = read_uint16_be(data_bytes, 8)
    ntrks = read_uint16_be(data_bytes, 10)
    division = read_uint16_be(data_bytes, 12)
    ticks_per_beat = division
    pos = 8 + hdr_len

    tracks = []
    for tr in range(ntrks):
        if pos + 8 > len(data_bytes) or data_bytes[pos:pos+4] != b'MTrk':
            raise ValueError(f"Expected MTrk at pos {pos}")
        tr_len = read_uint32_be(data_bytes, pos+4)
        tr_start = pos + 8
        tr_end = tr_start + tr_len
        if tr_end > len(data_bytes):
            raise ValueError("Track length extends past end of file")
        tr_data = data_bytes[tr_start:tr_end]
        tracks.append(tr_data)
        pos = tr_end

    # Walk tracks and collect events with absolute ticks
    events = []
    for ti, tr in enumerate(tracks):
        i = 0
        abs_ticks = 0
        running_status = None
        while i < len(tr):
            delta, i = read_varlen(tr, i)
            abs_ticks += delta
            if i >= len(tr):
                break
            status = tr[i]
            # running status handling
            if status < 0x80:
                # data byte - use running status
                if running_status is None:
                    raise ValueError("Running status used before being set")
                status_byte = running_status
            else:
                status_byte = status
                i += 1
                running_status = status_byte

            # Meta events
            if status_byte == 0xFF:
                if i >= len(tr):
                    raise ValueError("Malformed meta event")
                meta_type = tr[i]
                i += 1
                length, i = read_varlen(tr, i)
                meta_data = tr[i:i+length]
                i += length
                events.append((abs_ticks, ('meta', meta_type, bytes(meta_data))))
            # SysEx events (skip)
            elif status_byte == 0xF0 or status_byte == 0xF7:
                length, i = read_varlen(tr, i)
                sx = tr[i:i+length]
                i += length
                # We don't process sysex; keep as generic
                events.append((abs_ticks, ('sysex', bytes(sx))))
            else:
                # Channel message
                msg_type = status_byte & 0xF0
                channel = status_byte & 0x0F
                if msg_type in (0x80, 0x90, 0xA0, 0xB0, 0xE0):
                    # two data bytes
                    if i+1 >= len(tr):
                        raise ValueError("Unexpected end of data in 2-byte midi message")
                    d1 = tr[i]; d2 = tr[i+1]; i += 2
                    events.append((abs_ticks, ('midi', msg_type, channel, d1, d2)))
                elif msg_type in (0xC0, 0xD0):
                    # one data byte
                    if i >= len(tr):
                        raise ValueError("Unexpected end of data in 1-byte midi message")
                    d1 = tr[i]; i += 1
                    events.append((abs_ticks, ('midi1', msg_type, channel, d1)))
                else:
                    raise ValueError(f"Unknown MIDI status byte: {hex(status_byte)}")
    # sort by absolute ticks
    events.sort(key=lambda x: x[0])
    return ticks_per_beat, events

# -------------------------
# Convert events -> scheduled notes (in seconds)
# -------------------------
def events_to_notes(ticks_per_beat, events):
    """
    Convert sorted events (abs_ticks, evdata) into scheduled notes in seconds.
    Returns list of (start_sec, end_sec, midi_note, velocity)
    """
    default_tempo = 500000  # microseconds per beat (120 bpm)
    current_tempo = default_tempo
    last_tick = 0
    time_seconds = 0.0

    active_notes = {}  # midi_note -> list of (start_time_sec, velocity)
    scheduled_notes = []

    for ev in events:
        abs_tick, evdata = ev
        delta_ticks = abs_tick - last_tick
        last_tick = abs_tick
        # convert ticks to seconds under current tempo
        delta_seconds = (delta_ticks * current_tempo) / (ticks_per_beat * 1_000_000.0)
        time_seconds += delta_seconds

        if evdata[0] == 'meta':
            meta_type = evdata[1]
            meta_bytes = evdata[2]
            if meta_type == 0x51 and len(meta_bytes) == 3:
                tempo = int.from_bytes(meta_bytes, byteorder='big')
                current_tempo = tempo
        elif evdata[0] == 'midi':
            msg_type = evdata[1]
            # msg_type is high nibble
            if msg_type == 0x90:  # note on
                note = evdata[3]
                vel = evdata[4]
                if vel > 0:
                    active_notes.setdefault(note, []).append((time_seconds, vel))
                else:
                    lst = active_notes.get(note)
                    if lst and len(lst) > 0:
                        start, start_vel = lst.pop(0)
                        scheduled_notes.append((start, time_seconds, note, start_vel))
            elif msg_type == 0x80:  # note off
                note = evdata[3]
                lst = active_notes.get(note)
                if lst and len(lst) > 0:
                    start, start_vel = lst.pop(0)
                    scheduled_notes.append((start, time_seconds, note, start_vel))
            else:
                # ignore other channel messages
                pass
        elif evdata[0] == 'midi1':
            # program change or channel pressure - ignored for synthesis
            pass
        else:
            # meta, sysex already handled; ignore others
            pass

    final_time = time_seconds
    # Close any notes left active
    for note, lst in active_notes.items():
        for (start, vel) in lst:
            scheduled_notes.append((start, final_time + 1.0, note, vel))

    return scheduled_notes, final_time

# -------------------------
# Simple additive synth
# -------------------------
def midi_to_freq(m):
    return 440.0 * (2.0 ** ((m - 69) / 12.0))

def synth_notes(scheduled_notes, sr=44100):
    """
    scheduled_notes: list of (start_sec, end_sec, note, vel)
    returns numpy int16 array and sample rate
    """
    if scheduled_notes:
        duration = max(end for (_, end, _, _) in scheduled_notes) + 0.1
    else:
        duration = 0.1
    n_samples = int(math.ceil(duration * sr))
    audio = np.zeros(n_samples, dtype=np.float32)

    for (start, end, note, vel) in scheduled_notes:
        # bound checks
        start_i = int(round(max(0.0, start) * sr))
        end_i = int(round(min(end, duration) * sr))
        if start_i >= n_samples:
            continue
        if end_i <= start_i:
            end_i = min(start_i + 1, n_samples)
        tt = (np.arange(start_i, end_i) / sr) - start
        f = midi_to_freq(note)
        # additive partials -> approximated piano-ish tone
        wave = np.sin(2*np.pi*f*tt)
        wave += 0.6 * np.sin(2*np.pi*(2*f)*tt)
        wave += 0.3 * np.sin(2*np.pi*(3*f)*tt)

        # envelope: small attack, sustain, release based on note length
        note_len = max(0.001, end - start)
        attack = min(0.01, note_len * 0.1)
        release = min(0.25, note_len * 0.2)
        sustain_len = max(0.0, note_len - attack - release)

        a_s = int(attack * sr)
        s_s = int(sustain_len * sr)
        r_s = int(release * sr)
        env = np.ones_like(wave)
        pos = 0
        if a_s > 0 and pos < len(env):
            endpos = min(pos + a_s, len(env))
            env[pos:endpos] = np.linspace(0.0, 1.0, endpos-pos, endpoint=False)
            pos = endpos
        if s_s > 0 and pos < len(env):
            endpos = min(pos + s_s, len(env))
            env[pos:endpos] = 1.0
            pos = endpos
        if r_s > 0 and pos < len(env):
            endpos = min(pos + r_s, len(env))
            env[pos:endpos] = np.linspace(1.0, 0.0, endpos-pos, endpoint=False)
            pos = endpos
        if pos < len(env):
            env[pos:] = 0.0

        amp = (vel / 127.0) * 0.25  # global per-note scale to avoid clipping
        audio[start_i:start_i+len(wave)] += wave * env * amp

    # normalize to int16
    mx = np.max(np.abs(audio)) if audio.size > 0 else 0.0
    if mx < 1e-9:
        audio_int16 = np.zeros(n_samples, dtype=np.int16)
    else:
        audio = audio / mx
        audio_int16 = (audio * 32767.0).astype(np.int16)
    return audio_int16, sr

# -------------------------
# Main CLI / Orchestration
# -------------------------
def main():
    parser = argparse.ArgumentParser(description="Render a MIDI file to WAV/MP3 (simple synth).")
    parser.add_argument("midi", type=Path, help="Input MIDI file path")
    parser.add_argument("--wav", type=Path, default=None, help="Output WAV path (default: input_render.wav)")
    parser.add_argument("--mp3", type=Path, default=None, help="Output MP3 path (tries pydub/ffmpeg; optional)")
    parser.add_argument("--sr", type=int, default=44100, help="Sample rate (default 44100)")
    args = parser.parse_args()

    midi_path = args.midi
    if not midi_path.exists():
        print("ERROR: MIDI file not found:", midi_path)
        sys.exit(2)

    out_wav = args.wav if args.wav is not None else midi_path.with_name(midi_path.stem + "_render.wav")
    out_mp3 = args.mp3 if args.mp3 is not None else midi_path.with_name(midi_path.stem + "_render.mp3")

    print("Reading MIDI:", midi_path)
    data = midi_path.read_bytes()

    try:
        ticks_per_beat, events = parse_midi_bytes(data)
    except Exception as e:
        print("Failed to parse MIDI:", e)
        traceback.print_exc()
        sys.exit(1)

    print(f"Parsed MIDI: ticks_per_beat={ticks_per_beat}, events={len(events)}")

    scheduled_notes, final_time = events_to_notes(ticks_per_beat, events)
    print(f"Collected {len(scheduled_notes)} scheduled notes. Approx duration: {final_time:.2f} s")

    # synth
    try:
        audio_int16, sr = synth_notes(scheduled_notes, sr=args.sr)
    except Exception as e:
        print("Synthesis failed:", e)
        traceback.print_exc()
        sys.exit(1)

    # write WAV
    try:
        wavfile.write(str(out_wav), sr, audio_int16)
        print("WAV written to:", out_wav)
    except Exception as e:
        print("Failed to write WAV:", e)
        traceback.print_exc()
        sys.exit(1)

    # try write MP3 via pydub if available
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_wav(str(out_wav))
        seg.export(str(out_mp3), format="mp3", bitrate="192k")
        print("MP3 written to:", out_mp3)
    except Exception as e:
        print("MP3 export skipped/failed (pydub/ffmpeg may be missing). Error:")
        print(e)
        print("You can convert the WAV to MP3 locally with ffmpeg, e.g.:")
        print(f"  ffmpeg -i \"{out_wav}\" \"{out_mp3}\"")

if __name__ == "__main__":
    main()
