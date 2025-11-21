# Generated from audio file: melancholy_piano_render.wav
# Music Description: A slow, melancholic melody played on a synthesized organ with a somber and reflective mood.

use_synth :tb303
use_synth_defaults sustain: 1.5, release: 1.5, attack: 0.1

notes = [60, 62, 64, 65, 67, 69, 71, 72] # C4 to C5

# Play the melody in a slow, deliberate rhythm
notes.each do |note|
  play note, release: 1.5
  sleep 1.5
end

# Repeat the melody with a descending pattern
notes.reverse.each do |note|
  play note, release: 1.5
  sleep 1.5
end