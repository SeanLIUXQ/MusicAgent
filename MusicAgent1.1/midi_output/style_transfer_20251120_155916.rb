# Classical Style Transformation
use_bpm 75  # Slower tempo for classical feel

# Classical-appropriate synth with expressive settings
use_synth :piano
use_synth_defaults attack: 0.2, release: 1.0, amp: 0.7

# Original melody notes
melody_pattern = [60, 62, 64, 65, 67, 69, 71, 72] # C4 to C5

# Classical texture with gentle dynamics
live_loop :classical_texture do
  sample :ambi_glass_rub, amp: 0.2, rate: 0.3
  sleep 8
end

# Add cello bass line for classical foundation
live_loop :cello_bass do
  use_synth :hollow
  play 36, release: 2.0, amp: 0.6
  sleep 4
  play 38, release: 2.0, amp: 0.6
  sleep 4
end

# Add string accompaniment
live_loop :string_section do
  use_synth :hollow
  play_chord [48, 52, 55], amp: 0.4, release: 3.0
  sleep 4
end

# Main melody with classical expression and lyrical rhythm
with_fx :reverb, room: 0.8, mix: 0.3 do
  with_fx :echo, decay: 2.0 do
    # Expressive timing - melody with lyrical phrasing
    melody_pattern.each do |current_pitch|
      play current_pitch, sustain: 1.0, amp: (rrand(0.5, 0.8)), pan: rrand(-0.2, 0.2)
      sleep 1.0
      # Add harmonic support on strong beats
      play current_pitch + 4, sustain: 0.8, amp: 0.5 if [60, 64, 67].include?(current_pitch)
      sleep 2.0  # Total 3 beats per iteration for lyrical feel
    end

    # Gentle descending run with expressive timing
    (69..60).step(-1) do |current_pitch|
      play current_pitch, sustain: 0.5, amp: 0.6, pan: rrand(-0.3, 0.3)
      sleep 0.5
    end

    # Final chord with rich classical harmony
    play_chord [60, 64, 67], sustain: 3.0, amp: 0.8  # Major triad
    sleep 4
  end
end

# Additional gentle arpeggio for classical texture
live_loop :arpeggio_texture do
  use_synth :sine
  play_pattern_timed [60, 64, 67, 72], [0.5, 0.5, 0.5, 1.5], amp: 0.3, release: 0.8
  sleep 2
end

# Optional: Add slight tempo variations for expression
live_loop :tempo_variation do
  use_bpm 70 + rrand(-5, 5) if spread(3, 8).tick
  sleep 1
end