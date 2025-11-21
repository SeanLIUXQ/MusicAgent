use_synth :piano
use_synth_defaults sustain: 1.5, release: 1.5

notes = [60, 62, 64, 65, 67, 69, 71, 72] # C4 to C5

# Play the notes with a slow, deliberate rhythm
notes.each do |note|
  play note, sustain: 1.5, release: 1.5
  sleep 1.5
end

# Repeat the sequence with a descending pattern
notes.reverse_each do |note|
  play note, sustain: 1.5, release: 1.5
  sleep 1.5
end