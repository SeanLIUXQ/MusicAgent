# Rock Style Transformation
use_bpm 140

# Aggressive lead synth with distortion
use_synth :saw
use_synth_defaults attack: 0.05, release: 0.2, amp: 0.9

melody_notes = [60, 62, 64, 65, 67, 69, 71, 72]

with_fx :distortion, distort: 0.4 do
  with_fx :reverb, room: 0.2, damp: 0.6 do
    live_loop :rock_melody do
      melody_notes.each do |note_value|
        # Strong, consistent rock dynamics
        dynamic_level = 0.7 + (rand * 0.2)
        # Shorter, punchier notes for rock style
        sustain_duration = [0.1, 0.15, 0.2].choose
        # Add occasional slide for rock expression
        control note: note_value, slide: (rand < 0.2 ? 0.1 : 0) if rand < 0.3
        play note_value, sustain: sustain_duration, amp: dynamic_level
        sleep 0.3
      end
    end
  end
end

# Power chord rhythm section
live_loop :rhythm_guitar do
  use_synth :prophet
  chord_sequence = [chord(:C, :maj), chord(:G, :maj), chord(:A, :min), chord(:F, :maj)]
  with_fx :distortion, distort: 0.3 do
    chord_sequence.each do |chord_notes|
      # Play power chords (root + fifth) for rock sound
      power_chord = [chord_notes[0], chord_notes[2]]
      play_chord power_chord, attack: 0.05, release: 0.4, amp: 0.8
      sleep 2
    end
  end
end

# Add palm-muted power chords between main chords
live_loop :rhythm_fills do
  sync :rhythm_guitar
  use_synth :prophet
  with_fx :distortion, distort: 0.2 do
    4.times do
      play chord(:C, :maj)[0], release: 0.1, amp: 0.4
      sleep 0.25
    end
  end
end

# Aggressive bass line with rhythmic pattern
live_loop :bass_groove do
  use_synth :fm
  bass_pattern = [36, 36, 38, 38, 41, 41, 43, 43] # Lower octave for punch
  with_fx :lpf, cutoff: 80 do
    bass_pattern.each do |bass_note|
      play bass_note, release: 0.3, amp: 0.9
      sleep 0.5
      # Add ghost notes for groove
      play bass_note + 2, release: 0.1, amp: 0.3 if rand < 0.3
      sleep 0.5
    end
  end
end

# Driving rock drums
live_loop :drum_beat do
  sample :drum_bass_hard, amp: 1.0
  sleep 0.5
  sample :drum_snare_hard, amp: 0.9
  sleep 0.5
  sample :drum_bass_hard, amp: 1.0
  sleep 0.5
  sample :drum_snare_hard, amp: 0.9
  sleep 0.5
end

# Additional rhythm element with hi-hat
live_loop :hi_hat do
  sample :drum_cymbal_closed, amp: 0.4
  sleep 0.25
end

# Add occasional crash cymbals for emphasis
live_loop :cymbals do
  sync :drum_beat
  sample :drum_cymbal_open, amp: 0.6 if tick % 8 == 0
end