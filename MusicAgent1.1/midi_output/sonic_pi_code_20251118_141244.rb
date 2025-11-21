# 激昂阳光风格 - Energetic Sunshine Style
# Enhanced with brighter timbres, stronger dynamics, and energetic rhythms
# Final version optimized for maximum brightness and energy
# CRITICAL FIX: All variable names updated to avoid Sonic Pi built-in conflicts

use_bpm 140 # Increased tempo for more energetic feel

# Composition settings for better organization
composition_settings = {
  tempo: 140,
  key: :c4,
  scale_type: :major,
  base_amplitude: 0.8,
  chord_durations: [4, 4, 4, 4]
}

# Define musical parameters with safe variable names
current_key = composition_settings[:key]
melodic_scale_pattern = scale(current_key, :major) # C Major scale
pentatonic_scale_pattern = scale(current_key, :major_pentatonic) # Pentatonic for brightness

# Uplifting harmonic progression (I - V - vi - IV) in C Major with major 7th for extra brightness
chord_progression = [
  chord(:c3, :M7),   # C Major 7 (I)
  chord(:g3, :M),    # G Major (V)
  chord(:a3, :m7),   # A Minor 7 (vi)
  chord(:f3, :M7)    # F Major 7 (IV)
]

chord_durations = composition_settings[:chord_durations] # Shorter, energetic chords

# Thread-safe volume control
set :master_volume, 0.1

# Pre-calculated arpeggios for performance
precomputed_arpeggios = []
4.times do
  precomputed_arpeggios << pentatonic_scale_pattern.shuffle.take(8)
end

# Energetic drum foundation with enhanced impact
live_loop :drums do
  with_fx :compressor, threshold: 0.1, ratio: 4.0 do
    sample :drum_bass_hard, amp: 1.4
    sleep 0.5
    sample :drum_snare_hard, amp: 1.2
    sleep 0.5
    sample :drum_bass_hard, amp: 1.3
    sleep 0.5
    sample :drum_snare_hard, amp: 1.1
    sleep 0.5
  end
end

# Driving bass line with enhanced presence
live_loop :bass_line do
  use_synth :fm
  with_fx :distortion, distort: 0.2 do
    bass_pattern = [:c2, :e2, :g2, :c2, :a2, :g2, :f2, :e2]
    play_pattern_timed bass_pattern, 
      [0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5],
      amp: get(:master_volume) * 1.1,
      attack: 0.03, release: 0.2
  end
end

# Bright synth pad foundation with enhanced shimmer
live_loop :harmonic_bed do
  use_synth :prophet
  with_fx :reverb, mix: 0.5, room: 0.5, damp: 0.8 do
    with_fx :compressor, threshold: 0.2, ratio: 3.0 do
      with_fx :chorus, phase: 0.5 do
        chord_progression.each_with_index do |current_chord, index|
          play_chord current_chord, amp: get(:master_volume) * 0.9, attack: 0.1, release: 1.5
          sleep chord_durations[index]
        end
      end
    end
  end
end

# Bright piano arpeggios with faster tempo
live_loop :piano_textures do
  use_synth :pretty_bell
  with_fx :reverb, mix: 0.4, room: 0.4, damp: 0.9 do
    with_fx :echo, phase: 0.125, decay: 4 do
      precomputed_arpeggios.each do |arpeggio|
        # Safety check for empty patterns
        unless arpeggio.empty?
          arpeggio.each do |note|
            play note, amp: get(:master_volume) * 0.7, 
              pan: rrand(-0.3, 0.3), attack: 0.02, release: 0.5
            sleep 0.125
          end
        end
        sleep 0.5
      end
    end
  end
end

# Bright guitar patterns with enhanced presence
live_loop :guitar_ambience do
  use_synth :pluck
  with_fx :reverb, mix: 0.4, room: 0.3 do
    with_fx :lpf, cutoff: 120 do
      chord_progression.each do |current_chord|
        # Energetic strumming pattern
        play_pattern_timed current_chord, [0.125, 0.25, 0.125],
          amp: get(:master_volume) * 0.6,
          pan: rrand(-0.4, 0.4)
        sleep 2
      end
    end
  end
end

# Prominent lead melody with brighter synth
live_loop :lead_melody do
  use_synth :chiplead
  with_fx :reverb, mix: 0.4, room: 0.4, damp: 0.8 do
    with_fx :chorus, phase: 0.25 do
      # Create a recognizable motif instead of random notes
      lead_motif = [:c5, :e5, :g5, :e5, :c5, :g4, :e4, :c4]
      lead_motif.each do |note|
        play note, amp: get(:master_volume) * 0.8,
          attack: 0.05, release: 0.3,
          pan: rrand(-0.3, 0.3)
        sleep 0.5
      end
    end
  end
end

# Bright atmospheric texture with enhanced brightness
live_loop :atmospheric_pad do
  use_synth :sine
  with_fx :reverb, mix: 0.6, room: 0.6 do
    with_fx :hpf, cutoff: 300 do
      with_fx :lpf, cutoff: 2500 do
        play :c6, amp: get(:master_volume) * 0.3,
          attack: 0.5, release: 1.5,
          pan: rrand(-0.4, 0.4)
        sleep 8
      end
    end
  end
end

# Enhanced hi-hats with more energy
live_loop :hihats do
  4.times do
    sample :drum_cymbal_closed, amp: 0.5, rate: 1.3
    sleep 0.125
    sample :drum_cymbal_closed, amp: 0.3, rate: 1.2
    sleep 0.125
  end
end

# Add energetic brass stabs for accents (offset to avoid timing conflicts)
live_loop :brass_accents do
  use_synth :prophet
  with_fx :distortion, distort: 0.2 do
    sleep 4  # Offset by 4 beats to avoid conflict with crash accents
    play_chord chord(:c4, :M), amp: 1.0, attack: 0.01, release: 0.5
    sleep 12
  end
end

# Add occasional crash cymbal for emphasis
live_loop :accents do
  sleep 16
  sample :drum_cymbal_hard, amp: 1.0, rate: 0.9
  sleep 16
end

# Add rising synth sweeps for extra sunshine energy
live_loop :sunrise_sweeps do
  use_synth :saw
  with_fx :lpf, cutoff: 80 do
    play :c3, amp: 0.3, attack: 0.5, release: 3, cutoff: 120
    sleep 16
  end
end

# MIDI output capability
live_loop :midi_out do
  use_real_time
  note, velocity = sync "/midi:*/note_on"
  midi note, vel: velocity if note
end

# Quick fade in at start (thread-safe) with higher maximum and celebratory crash
live_loop :fade_in do
  current_vol = get(:master_volume)
  if current_vol < 1.0
    set :master_volume, current_vol * 1.2  # Faster fade
  else
    set :master_volume, 1.0
    # Add a celebratory crash cymbal at peak volume
    sample :drum_cymbal_hard, amp: 1.2, rate: 0.8
    stop
  end
  sleep 0.15  # Even quicker fade
end

# Comment this section to remove automatic fade out
# To fade out manually, reduce master_volume gradually
# live_loop :fade_out do
#   sleep 120 # Wait 2 minutes
#   current_vol = get(:master_volume)
#   set :master_volume, current_vol * 0.95
#   stop if current_vol < 0.01
# end