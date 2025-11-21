# Tranquil Repose - Rest Music Composition
# Based on professional music specification for relaxation and calm
# Improved version with thread-safe volume control and enhanced organization

use_bpm 60 # Larghetto tempo for resting heart rate

# Composition settings for better organization
composition_settings = {
  tempo: 60,
  key: :c4,
  scale_type: :major,
  base_amplitude: 0.3,
  chord_durations: [8, 8, 8, 8]
}

# Define musical parameters with safe variable names
current_key = composition_settings[:key]
melodic_scale = scale(current_key, :major) # C Major scale
pentatonic_scale = scale(current_key, :major_pentatonic) # Pentatonic for simplicity

# Gentle harmonic progression (I - IV - vi - V) in C Major
harmonic_progression = [
  chord(:c3, :M),   # C Major (I)
  chord(:f3, :M),   # F Major (IV)
  chord(:a3, :m),   # A Minor (vi)
  chord(:g3, :M)    # G Major (V)
]

chord_durations = composition_settings[:chord_durations] # Long, sustained chords

# Thread-safe volume control
set :master_volume, 0.01

# Pre-calculated arpeggios for performance
precomputed_arpeggios = []
4.times do
  precomputed_arpeggios << pentatonic_scale.shuffle.take(4)
end

# Warm ambient pad foundation
live_loop :harmonic_bed do
  use_synth :hollow
  with_fx :reverb, mix: 0.8, room: 0.9, damp: 0.7 do
    with_fx :eq, low_shelf: -1, high_shelf: -2 do
      harmonic_progression.each_with_index do |current_chord, index|
        play_chord current_chord, amp: get(:master_volume) * 0.4, attack: 2, release: 6
        sleep chord_durations[index]
      end
    end
  end
end

# Delicate piano arpeggios
live_loop :piano_textures do
  use_synth :piano
  with_fx :reverb, mix: 0.7, room: 0.8 do
    with_fx :echo, phase: 0.75, decay: 4 do
      precomputed_arpeggios.each do |arpeggio|
        # Safety check for empty patterns
        unless arpeggio.empty?
          arpeggio.each do |note|
            play note, amp: get(:master_volume) * 0.3, 
              pan: rrand(-0.3, 0.3), attack: 0.1, release: 1.5
            sleep 0.5
          end
        end
        sleep 2
      end
    end
  end
end

# Nylon string guitar patterns
live_loop :guitar_ambience do
  use_synth :pluck
  with_fx :reverb, mix: 0.6, room: 0.7 do
    with_fx :lpf, cutoff: 90 do
      harmonic_progression.each do |current_chord|
        # Gentle fingerpicking pattern
        play_pattern_timed current_chord, [0.25, 0.5, 0.25],
          amp: get(:master_volume) * 0.2,
          pan: rrand(-0.2, 0.2)
        sleep 4
      end
    end
  end
end

# Subtle string melody (appears occasionally)
live_loop :string_melody do
  use_synth :saw
  with_fx :reverb, mix: 0.8, room: 0.9 do
    with_fx :lpf, cutoff: 80 do
      if one_in(4) # Only play 25% of the time
        # Simple pentatonic melody fragment
        melody_notes = pentatonic_scale.shuffle.take(3)
        # Safety check for empty melody
        unless melody_notes.empty?
          melody_notes.each do |note|
            play note + 12, # One octave up
              amp: get(:master_volume) * 0.15,
              attack: 0.5, release: 2,
              pan: rrand(-0.1, 0.1)
            sleep 1.5
          end
        end
      end
      sleep 8
    end
  end
end

# Atmospheric texture (high-frequency shimmer)
live_loop :atmospheric_pad do
  use_synth :cnoise
  with_fx :reverb, mix: 0.9, room: 1 do
    with_fx :hpf, cutoff: 80 do
      with_fx :lpf, cutoff: 120 do
        play :c6, amp: get(:master_volume) * 0.05,
          attack: 3, release: 5,
          pan: rrand(-0.5, 0.5)
        sleep 12
      end
    end
  end
end

# Optional: Nature sounds (uncomment if desired)
# live_loop :nature_sounds do
#   sample :ambi_soft_buzz, amp: get(:master_volume) * 0.1, rate: 0.3
#   sleep 16
# end

# MIDI output capability
live_loop :midi_out do
  use_real_time
  note, velocity = sync "/midi:*/note_on"
  midi note, vel: velocity if note
end

# Gentle fade in at start (thread-safe)
live_loop :fade_in do
  current_vol = get(:master_volume)
  if current_vol < 0.3
    set :master_volume, current_vol * 1.1
  else
    set :master_volume, 0.3
    stop
  end
  sleep 0.5
end

# Comment this section to remove automatic fade out
# To fade out manually, reduce master_volume gradually
# live_loop :fade_out do
#   sleep 120 # Wait 2 minutes
#   current_vol = get(:master_volume)
#   set :master_volume, current_vol * 0.95
#   stop if current_vol < 0.01
# end