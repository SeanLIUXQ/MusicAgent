# Jazz Transformation - Professional Music Specification Implementation
# Key: D Major, Tempo: 110 BPM, Time Signature: 4/4
# Style: Jazz with Swing Feel and Extended Harmony

use_bpm 110
use_swing 0.1  # Built-in swing function for authentic jazz feel

# Define musical parameters with safe variable names
current_tempo = 110
key_root = :d4
scale_mode = :major
progression_sequence = [:d3, :g3, :a3, :b3, :f3, :g3, :e3, :a3]
melody_pitches = [:d5, :e5, :fs5, :g5, :a5, :b5, :cs6, :d6, :b5, :a5, :g5, :fs5, :e5, :d5]
rhythm_timing = [0.5, 0.5, 1, 1, 0.75, 0.25, 1, 2]
volume_level = 0.6
reverb_mix = 0.3
delay_time = 0.5

# Jazz chord progression with extensions: Dmaj9 - Gmaj9 - A13 - Bm11

# Jazz organ for harmonic foundation
live_loop :jazz_organ do
  use_synth :hollow
  with_fx :reverb, mix: reverb_mix, room: 0.6 do
    with_fx :flanger, phase: 2 do
      play_chord chord(:d3, :maj9), attack: 0.5, release: 3.5, amp: volume_level * 0.4
      sleep 4
      play_chord chord(:g3, :maj9), attack: 0.5, release: 3.5, amp: volume_level * 0.4
      sleep 4
      play_chord chord(:a3, :dom13), attack: 0.5, release: 3.5, amp: volume_level * 0.4
      sleep 4
      play_chord chord(:b3, :m11), attack: 0.5, release: 3.5, amp: volume_level * 0.4
      sleep 4
    end
  end
end

# Main jazz melody (saxophone-like with swing)
live_loop :main_melody do
  use_synth :prophet  # More authentic jazz tone
  with_fx :reverb, mix: 0.2, room: 0.4 do
    with_fx :vowel, voice: 0.2 do
      # First phrase - swung with jazz articulation
      play :d4, attack: 0.05, release: 0.4, amp: volume_level * 0.8
      sleep 0.5
      play :e4, attack: 0.05, release: 0.4, amp: volume_level * 0.8
      sleep 0.5
      play :fs4, attack: 0.1, release: 0.8, amp: volume_level * 0.9
      sleep 1
      play :g4, attack: 0.1, release: 0.8, amp: volume_level * 0.9
      sleep 1
      
      # Second phrase - syncopated climax
      play :a4, attack: 0.05, release: 0.3, amp: volume_level
      sleep 0.75
      play :b4, attack: 0.02, release: 0.2, amp: volume_level * 1.1
      sleep 0.25
      play :cs5, attack: 0.1, release: 0.6, amp: volume_level * 1.1
      sleep 1
      play :d5, attack: 0.2, release: 1, amp: volume_level * 0.9
      sleep 2
      
      # Third phrase - descending with blue notes
      play :b4, attack: 0.05, release: 0.4, amp: volume_level * 0.8
      sleep 0.5
      play :a4, attack: 0.05, release: 0.4, amp: volume_level * 0.8
      sleep 0.5
      play :g4, attack: 0.1, release: 0.8, amp: volume_level * 0.9
      sleep 1
      play :fs4, attack: 0.1, release: 0.8, amp: volume_level * 0.9
      sleep 1
      
      # Final phrase - jazz resolution
      play :e4, attack: 0.05, release: 0.3, amp: volume_level * 0.7
      sleep 0.75
      play :d4, attack: 0.02, release: 0.2, amp: volume_level * 0.6
      sleep 0.25
      play :cs4, attack: 0.1, release: 0.6, amp: volume_level * 0.5
      sleep 1
      play :d4, attack: 0.3, release: 1.5, amp: volume_level * 0.4
      sleep 3
    end
  end
end

# Enhanced walking bass line for jazz foundation
live_loop :walking_bass do
  use_synth :tb303  # More authentic bass tone
  with_fx :reverb, mix: 0.1 do
    # D Major walking pattern with chromatic approaches
    play :d2, amp: volume_level * 0.7, release: 0.4
    sleep 0.5
    play :e2, amp: volume_level * 0.5, release: 0.3  # Chromatic approach
    sleep 0.5
    play :fs2, amp: volume_level * 0.6, release: 0.4
    sleep 0.5
    play :a2, amp: volume_level * 0.7, release: 0.4
    sleep 0.5
    
    # G Major walking pattern
    play :g2, amp: volume_level * 0.7, release: 0.4
    sleep 0.5
    play :a2, amp: volume_level * 0.5, release: 0.3  # Passing tone
    sleep 0.5
    play :b2, amp: volume_level * 0.6, release: 0.4
    sleep 0.5
    play :d3, amp: volume_level * 0.7, release: 0.4
    sleep 0.5
    
    # A7 walking pattern
    play :a2, amp: volume_level * 0.7, release: 0.4
    sleep 0.5
    play :b2, amp: volume_level * 0.5, release: 0.3  # Approach tone
    sleep 0.5
    play :cs3, amp: volume_level * 0.6, release: 0.4
    sleep 0.5
    play :e3, amp: volume_level * 0.7, release: 0.4
    sleep 0.5
    
    # B minor walking pattern
    play :b2, amp: volume_level * 0.7, release: 0.4
    sleep 0.5
    play :cs3, amp: volume_level * 0.5, release: 0.3  # Chromatic
    sleep 0.5
    play :d3, amp: volume_level * 0.6, release: 0.4
    sleep 0.5
    play :fs3, amp: volume_level * 0.7, release: 0.4
    sleep 0.5
  end
end

# Jazz piano comping with syncopation - FIXED SYNTAX
live_loop :jazz_piano do
  use_synth :piano
  with_fx :reverb, mix: 0.1 do
    with_fx :chorus, phase: 0.25 do
      # Syncopated chord stabs
      sleep 0.25
      play_chord [:d3, :fs3, :a3, :cs4, :e4], amp: volume_level * 0.5, sustain: 0.3
      sleep 1.75
      play_chord [:g3, :b3, :d4, :fs4, :a4], amp: volume_level * 0.5, sustain: 0.3
      sleep 2
      play_chord [:a3, :cs4, :e4, :g4, :b4], amp: volume_level * 0.5, sustain: 0.3
      sleep 2
      play_chord [:b3, :d4, :fs4, :a4, :c5], amp: volume_level * 0.5, sustain: 0.3
      sleep 2
    end
  end
end

# Enhanced jazz drum kit
live_loop :jazz_hihat do
  sample :drum_cymbal_pedal, amp: volume_level * 0.2, rate: 1.2
  sleep 0.25
  sample :drum_cymbal_pedal, amp: volume_level * 0.1, rate: 1.2
  sleep 0.25
end

live_loop :jazz_comping do
  sleep 2
  sample :drum_snare_soft, amp: volume_level * 0.4
  sleep 1
  sample :drum_snare_soft, amp: volume_level * 0.3
  sleep 1
end

# Jazz brush snare for authenticity
live_loop :brush_snare do
  sleep 8
  sample :drum_snare_soft, amp: volume_level * 0.2, rate: 0.8
  sleep 8
end

# MIDI output for external instruments
live_loop :midi_melody, sync: :main_melody do
  use_real_time
  midi melody_pitches.tick, sustain: 0.6, vel_f: 0.8
  sleep rhythm_timing.look
end

# Subtle atmospheric texture
live_loop :atmosphere do
  use_synth :dark_ambience
  with_fx :reverb, mix: 0.4, room: 0.6 do
    with_fx :flanger, phase: 4 do
      play :d2, attack: 2, release: 6, amp: volume_level * 0.15, cutoff: 70
      sleep 8
      play :a2, attack: 2, release: 6, amp: volume_level * 0.15, cutoff: 70
      sleep 8
    end
  end
end

# Jazz fill every 16 bars for authenticity
live_loop :jazz_fills do
  sleep 64  # Wait 16 bars (64 beats at 4/4)
  use_synth :prophet
  with_fx :reverb, mix: 0.3 do
    play_pattern_timed [:d5, :e5, :fs5, :g5, :a5], [0.2, 0.2, 0.2, 0.2, 0.4], amp: volume_level * 0.8
  end
end