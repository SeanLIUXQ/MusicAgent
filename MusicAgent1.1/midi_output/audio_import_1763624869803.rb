# Generated from audio file: melancholy_piano_render.wav
# Music Description: A slow, melancholic melody played on a synthesized organ-like instrument with a somber and reflective mood.

use_synth :tb303
use_synth_defaults attack: 0.5, release: 2, cutoff: 80, resonance: 0.7

notes = [60, 62, 64, 65, 67, 69, 71, 72] # C4 to C5

# Play the notes with a slow, deliberate rhythm
notes.each do |note|
  play note, sustain: 1.5
  sleep 1.5
end

# Add a descending run for variation
(69..60).step(-1) do |note|
  play note, sustain: 0.5
  sleep 0.5
end

# Final chord for resolution
play [60, 64, 67], sustain: 2
sleep 2