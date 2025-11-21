# Rock Style Transformation
use_bpm 120  # Faster tempo for rock feel

# Rock-appropriate synth with aggressive settings
use_synth :prophet
use_synth_defaults attack: 0.05, release: 0.3, cutoff: 110, resonance: 0.5

# Original melody notes
melody_notes = [60, 62, 64, 65, 67, 69, 71, 72] # C4 to C5

# Enhanced rock drum pattern with more dynamics
live_loop :rock_drums do
  sample :drum_bass_hard, amp: 1.0
  sleep 0.5
  sample :drum_snare_hard, amp: 0.9
  sleep 0.5
  sample :drum_bass_hard, amp: 0.8
  sleep 0.25
  sample :drum_bass_hard, amp: 0.9
  sleep 0.25
  sample :drum_snare_hard, amp: 1.0
  sleep 0.5
end

# Add bass line for rock foundation
live_loop :bass_line do
  use_synth :fm
  with_fx :lpf, cutoff: 80 do
    play 36, release: 0.4, amp: 0.8
    sleep 1
    play 38, release: 0.4, amp: 0.8
    sleep 1
  end
end

# Main melody with rock distortion and punchier rhythm
with_fx :distortion, distort: 0.4, amp: 0.9 do
  with_fx :reverb, room: 0.3 do
    # Fixed timing - melody aligned with 0.5 beat grid
    melody_notes.each do |current_note|
      play current_note, sustain: 0.2, amp: 0.9
      sleep 0.5
      # Add power chord emphasis on strong beats
      play current_note + 7, sustain: 0.15, amp: 0.7 if [60, 64, 67].include?(current_note)
      sleep 1.0  # Total 1.5 beats per iteration
    end

    # Descending run with rock energy and guitar-like slides
    (69..60).step(-1) do |current_note|
      play current_note, sustain: 0.15, amp: 0.8, slide: 0.1
      sleep 0.25
    end

    # Final power chord with enhanced distortion for rock resolution
    with_fx :distortion, distort: 0.6 do
      play [60, 67], sustain: 1.5, amp: 1.3  # Root + fifth power chord
      sleep 2
    end
  end
end

# Additional hi-hat for rock drive
live_loop :hi_hat do
  sample :drum_cymbal_closed, amp: 0.4, rate: 1.5
  sleep 0.25
end