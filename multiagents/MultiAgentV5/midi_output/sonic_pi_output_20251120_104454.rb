use_bpm 128

# Global stop signal
$stop = false

# Define musical elements with more variation
chord_progression = [:c2, :g2, :ab2, :eb2].ring
bass_pattern = [0.5, 0.25, 0.25, 1, 0.5, 0.25, 0.25, 1].ring
melody_notes = [:c4, :eb4, :g4, :c5, :eb5, :g4, :c5, :eb4].ring
melody_variation = [:c4, :g4, :bb4, :f5].ring
melody_rhythm = [0.5, 0.25, 0.25, 1].ring

# Drums
live_loop :kick_drum do
  stop if $stop
  sample :bd_haus, amp: 1.2
  sleep 1
end

live_loop :snare do
  stop if $stop
  sleep 1
  sample :sn_dolf, amp: 0.8
  sleep 1
end

live_loop :hihats do
  stop if $stop
  16.times do
    sample :drum_cymbal_closed, amp: 0.3, rate: 1.2
    sleep 0.5
  end
end

live_loop :hat_fills do
  stop if $stop
  sleep 8 # Play a fill every 32 beats
  4.times do
    sample :drum_cymbal_open, amp: 0.2, rate: 1.1
    sleep 0.125
  end
end

# Bass line with chord-based variation
live_loop :bass do
  stop if $stop
  use_synth :tb303
  current_chord = chord_progression.tick
  # Play a pattern using notes from the chord
  bass_notes = [current_chord, chord(current_chord).choose, current_chord, chord(current_chord).choose].ring
  play_pattern_timed bass_notes, bass_pattern, release: 0.3, cutoff: 110, res: 0.6
end

# Main arpeggio melody with variation and automated filter
live_loop :arpeggio do
  stop if $stop
  use_synth :prophet
  tick_val = tick
  with_fx :reverb, room: 0.6 do
    # Automate the cutoff for a less static sound
    current_cutoff = 80 + (Math.sin(tick_val * 0.1) * 20)
    with_fx :lpf, cutoff: current_cutoff do
      # Every 4th cycle, play a different pattern
      if tick_val % 4 == 0
        play_pattern_timed melody_variation, melody_rhythm, amp: 0.7, release: 0.2
      else
        play_pattern_timed melody_notes, 0.25, amp: 0.7, release: 0.1
      end
    end
  end
end

# Pad for atmosphere with richer chords
live_loop :pad do
  stop if $stop
  use_synth :hollow
  current_chord = chord_progression.look
  # Play a minor 7th chord for more color
  play_chord chord(current_chord, :minor7), amp: 0.5, attack: 1, release: 4
  sleep 4
end

# Structure control - centralized with proper transitions
live_loop :structure do
  # Intro (0:00-0:30)
  control :arpeggio, amp: 0
  control :pad, amp: 0
  sleep 8
  
  # Verse A (0:30-1:30)
  control :arpeggio, amp: 0.7, amp_slide: 2
  control :pad, amp: 0.3, amp_slide: 2
  sleep 8
  
  # Pre-chorus (1:30-2:00) with filter build
  with_fx :lpf, cutoff: 60 do
    control cutoff: 120, cutoff_slide: 8
    sleep 8
  end
  sleep 8
  
  # Chorus (2:00-3:00)
  control :arpeggio, amp: 0.9, amp_slide: 2
  control :pad, amp: 0.5, amp_slide: 2
  sleep 8
  
  # Break (3:00-3:30)
  control :arpeggio, amp: 0.3, amp_slide: 2
  control :pad, amp: 0.2, amp_slide: 2
  sleep 8
  
  # Chorus 2 (3:30-4:30)
  control :arpeggio, amp: 0.9, amp_slide: 2
  control :pad, amp: 0.5, amp_slide: 2
  sleep 8
  
  # Outro (4:30-5:00)
  control :arpeggio, amp: 0, amp_slide: 8
  control :pad, amp: 0, amp_slide: 8
  control :bass, amp: 0, amp_slide: 8
  sleep 8
  # Signal all loops to stop
  $stop = true
  stop
end