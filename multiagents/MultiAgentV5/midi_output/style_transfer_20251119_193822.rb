use_synth :piano
use_synth_defaults attack: 0.15, release: 0.8, amp: 0.6

melody_pattern = [60, 62, 64, 65, 67, 69, 71, 72]

with_fx :reverb, room: 0.7, damp: 0.4 do
  live_loop :classical_melody do
    melody_pattern.each do |note_value|
      # More expressive dynamic shaping with crescendo/diminuendo effect
      dynamic_level = 0.4 + (rand * 0.4)
      # Add legato/sustain variations for classical phrasing
      sustain_time = [0.3, 0.4, 0.5].choose
      play note_value, sustain: sustain_time, amp: dynamic_level
      sleep 0.3
    end
  end
end

live_loop :harmony do
  use_synth :piano
  chord_progression = [chord(:C, :maj), chord(:G, :maj), chord(:A, :min), chord(:F, :maj)]
  chord_progression.each do |chord_notes|
    play_chord chord_notes, attack: 0.2, release: 1.2, amp: 0.3
    sleep 2
  end
end

# Add counter-melody for classical texture
live_loop :counter_melody do
  use_synth :piano
  counter_pattern = [48, 50, 52, 53, 55, 57, 59, 60]
  with_fx :reverb, room: 0.5, damp: 0.3 do
    counter_pattern.each do |counter_note|
      counter_dynamic = 0.2 + (rand * 0.2)
      play counter_note, sustain: 0.25, amp: counter_dynamic
      sleep 0.6
    end
  end
end