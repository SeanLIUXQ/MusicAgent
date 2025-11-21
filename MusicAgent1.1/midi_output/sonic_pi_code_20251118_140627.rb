# 激昂阳光风格 - Energetic Sunshine Style
# Transformed from tranquil repose to energetic, uplifting composition
# Final version with improved rhythm sync and enhanced melodies

use_bpm 130 # Allegro tempo for energetic feel

# Composition settings for better organization
composition_settings = {
  tempo: 130,
  key: :c4,
  scale_type: :major,
  base_amplitude: 0.6,
  chord_durations: [4, 4, 4, 4]
}

# Define musical parameters with safe variable names
current_key = composition_settings[:key]
melodic_scale_notes = scale(current_key, :major) # C Major scale
pentatonic_scale_notes = scale(current_key, :major_pentatonic) # Pentatonic for brightness

# Uplifting harmonic progression (I - V - vi - IV) in C Major
chord_progression = [
  chord(:c3, :M),   # C Major (I)
  chord(:g3, :M),   # G Major (V)
  chord(:a3, :m),   # A Minor (vi)
  chord(:f3, :M)    # F Major (IV)
]

chord_durations = composition_settings[:chord_durations] # Shorter, energetic chords

# Thread-safe volume control
set :master_volume, 0.1

# Pre-calculated arpeggios for performance
precomputed_arpeggios = []
4.times do
  precomputed_arpeggios << pentatonic_scale_notes.shuffle.take(8)
end

# Energetic drum foundation
live_loop :drums do
  with_fx :compressor, threshold: 0.2, ratio: 4.0 do
    sample :drum_bass_hard, amp: 1.2
    sleep 0.5
    sample :drum_snare_hard, amp: 1.0
    sleep 0.5
    sample :drum_bass_hard, amp: 1.1
    sleep 0.5
    sample :drum_snare_hard, amp: 0.9
    sleep 0.5
  end
end

# Driving bass line with improved pattern
live_loop :bass_line do
  use_synth :fm
  with_fx :distortion, distort: 0.1 do
    bass_pattern = [:c2, :e2, :g2, :c2, :a2, :g2, :f2, :e2]
    play_pattern_timed bass_pattern, 
      [0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5],
      amp: get(:master_volume) * 0.9,
      attack: 0.05, release: 0.3
  end
end

# Bright synth pad foundation
live_loop :harmonic_bed do
  use_synth :prophet
  with_fx :reverb, mix: 0.4, room: 0.6, damp: 0.5 do
    with_fx :compressor, threshold: 0.3, ratio: 3.0 do
      chord_progression.each_with_index do |current_chord, index|
        play_chord current_chord, amp: get(:master_volume) * 0.7, attack: 0.2, release: 2
        sleep chord_durations[index]
      end
    end
  end
end

# Bright piano arpeggios
live_loop :piano_textures do
  use_synth :piano
  with_fx :reverb, mix: 0.3, room: 0.5 do
    with_fx :echo, phase: 0.25, decay: 2 do
      precomputed_arpeggios.each do |arpeggio|
        # Safety check for empty patterns
        unless arpeggio.empty?
          arpeggio.each do |note|
            play note, amp: get(:master_volume) * 0.5, 
              pan: rrand(-0.2, 0.2), attack: 0.05, release: 0.8
            sleep 0.25
          end
        end
        sleep 1
      end
    end
  end
end

# Bright guitar patterns
live_loop :guitar_ambience do
  use_synth :pluck
  with_fx :reverb, mix: 0.3, room: 0.4 do
    with_fx :lpf, cutoff: 110 do
      chord_progression.each do |current_chord|
        # Energetic strumming pattern
        play_pattern_timed current_chord, [0.125, 0.25, 0.125],
          amp: get(:master_volume) * 0.4,
          pan: rrand(-0.3, 0.3)
        sleep 2
      end
    end
  end
end

# Prominent lead melody with memorable motif
live_loop :lead_melody do
  use_synth :saw
  with_fx :reverb, mix: 0.3, room: 0.5 do
    with_fx :lpf, cutoff: 100 do
      # Create a recognizable motif instead of random notes
      lead_motif = [:c5, :e5, :g5, :e5, :c5, :g4, :e4, :c4]
      lead_motif.each do |note|
        play note, amp: get(:master_volume) * 0.6,
          attack: 0.1, release: 0.5,
          pan: rrand(-0.2, 0.2)
        sleep 0.5
      end
    end
  end
end

# Bright atmospheric texture
live_loop :atmospheric_pad do
  use_synth :sine
  with_fx :reverb, mix: 0.5, room: 0.7 do
    with_fx :hpf, cutoff: 200 do
      with_fx :lpf, cutoff: 2000 do
        play :c6, amp: get(:master_volume) * 0.2,
          attack: 1, release: 2,
          pan: rrand(-0.3, 0.3)
        sleep 8
      end
    end
  end
end

# Enhanced hi-hats with syncopation for more energy
live_loop :hihats do
  4.times do
    sample :drum_cymbal_closed, amp: 0.4, rate: 1.2
    sleep 0.125
    sample :drum_cymbal_closed, amp: 0.2, rate: 1.1
    sleep 0.125
  end
end

# Add occasional crash cymbal for emphasis
live_loop :accents do
  sleep 16
  sample :drum_cymbal_hard, amp: 0.8, rate: 0.9
  sleep 16
end

# MIDI output capability
live_loop :midi_out do
  use_real_time
  note, velocity = sync "/midi:*/note_on"
  midi note, vel: velocity if note
end

# Quick fade in at start (thread-safe)
live_loop :fade_in do
  current_vol = get(:master_volume)
  if current_vol < 0.8
    set :master_volume, current_vol * 1.2
  else
    set :master_volume, 0.8
    stop
  end
  sleep 0.25
end

# Comment this section to remove automatic fade out
# To fade out manually, reduce master_volume gradually
# live_loop :fade_out do
#   sleep 120 # Wait 2 minutes
#   current_vol = get(:master_volume)
#   set :master_volume, current_vol * 0.95
#   stop if current_vol < 0.01
# end