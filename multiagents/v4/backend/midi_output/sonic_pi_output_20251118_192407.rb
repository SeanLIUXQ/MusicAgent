# Dynamic Evolution - Cinematic Orchestral Piece
# Professional Specification Implementation

use_bpm 70

# Define tonal centers
c_minor_scale_pattern = [:c3, :d3, :ds3, :f3, :g3, :gs3, :as3, :c4, :d4, :ds4, :f4, :g4, :gs4, :as4, :c5]
eb_major_scale_pattern = [:eb3, :f3, :g3, :ab3, :bb3, :c4, :d4, :eb4, :f4, :g4, :ab4, :bb4, :c5, :d5, :eb5]

# Chord progressions
c_minor_progression = [[:c3, :eb3, :g3], [:f3, :ab3, :c4], [:g3, :bb3, :d4], [:eb3, :g3, :bb3]]
eb_major_progression = [[:eb3, :g3, :bb3], [:ab3, :c4, :eb4], [:bb3, :d4, :f4], [:f3, :ab3, :c4]]

# Global parameters
current_tempo = 70
section_duration = 64
transition_duration = 16

# Section timing markers
section_a_start = 0
section_b_start = section_duration
section_c_start = section_b_start + section_duration + transition_duration
section_d_start = section_c_start + section_duration

# Ambient pad with evolving filter
live_loop :ambient_pad, sync: :metronome do
  current_section = get_section(current_tempo)
  
  if current_section == :a
    with_fx :reverb, mix: 0.8, room: 0.9 do
      with_fx :lpf, cutoff: 60 do |lpf_ctrl|
        control lpf_ctrl, cutoff: line(60, 100, steps: 32)
        synth :hollow, note: :c2, sustain: 8, release: 4, volume: 0.3
        sleep 8
      end
    end
  elsif current_section == :b
    with_fx :reverb, mix: 0.7, room: 0.8 do
      synth :hollow, note: :c2, sustain: 4, release: 2, volume: 0.5
      sleep 4
    end
  elsif current_section == :c
    with_fx :reverb, mix: 0.6, room: 0.7 do
      synth :hollow, note: :eb2, sustain: 2, release: 1, volume: 0.7
      sleep 2
    end
  else
    with_fx :reverb, mix: 0.9, room: 1.0 do
      with_fx :lpf, cutoff: line(100, 40, steps: 16) do
        synth :hollow, note: :c2, sustain: 16, release: 8, volume: line(0.6, 0.1, steps: 16)
        sleep 16
      end
    end
  end
end

# Piano arpeggio motif
live_loop :piano_motif, sync: :metronome do
  current_section = get_section(current_tempo)
  current_progression = current_section == :c ? eb_major_progression : c_minor_progression
  
  use_synth :piano
  
  if current_section == :a
    # Sparse, atmospheric piano
    if one_in(4)
      with_fx :reverb, mix: 0.9 do
        play_pattern_timed c_minor_scale_pattern.shuffle.take(3), [0.5, 1, 1.5], volume: 0.2
      end
    end
    sleep 8
  elsif current_section == :b
    # Building arpeggio
    chord_notes = current_progression.tick
    with_fx :reverb, mix: 0.7 do
      play_pattern_timed chord_notes, [0.25, 0.25, 0.5], volume: line(0.3, 0.6, steps: 16)
    end
    sleep 2
  elsif current_section == :c
    # Forceful arpeggio in relative major
    chord_notes = current_progression.tick
    with_fx :reverb, mix: 0.5, room: 0.8 do
      play_chord chord_notes, volume: 0.8, sustain: 1
      play_pattern_timed chord_notes, [0.125, 0.125, 0.25], volume: 0.7
    end
    sleep 1
  else
    # Fading outro
    with_fx :reverb, mix: 0.9, room: 1.0 do
      play :c3, sustain: 8, release: 4, volume: line(0.5, 0.1, steps: 8)
    end
    sleep 16
  end
end

# String section
live_loop :strings, sync: :metronome do
  current_section = get_section(current_tempo)
  
  use_synth :saw
  
  if current_section == :b
    # Building tension with high strings
    with_fx :reverb, mix: 0.6 do
      play_chord [:c5, :eb5, :g5], sustain: 4, volume: line(0.3, 0.6, steps: 8)
      sleep 4
      play_chord [:d5, :f5, :ab5], sustain: 4, volume: line(0.4, 0.7, steps: 8)
      sleep 4
    end
  elsif current_section == :c
    # Full string melody in climax
    with_fx :reverb, mix: 0.4 do
      melody_notes = [:eb4, :f4, :g4, :ab4, :bb4, :c5, :bb4, :ab4]
      play_pattern_timed melody_notes, [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.25, 0.25], volume: 0.8
    end
  else
    sleep 8
  end
end

# Percussion section
live_loop :percussion, sync: :metronome do
  current_section = get_section(current_tempo)
  
  if current_section == :b
    # Building taiko drums
    sample :perc_snap2, rate: 0.8, volume: line(0.3, 0.7, steps: 16) if spread(3, 8).tick
    sleep 0.5
  elsif current_section == :c
    # Driving orchestral percussion
    sample :bd_haus, volume: 0.9 if factor?(0, 4)
    sample :drum_cymbal_closed, volume: 0.6 if factor?(2, 4)
    sample :drum_snare_hard, volume: 0.7 if factor?(1, 2)
    sleep 0.5
  else
    sleep 1
  end
end

# Brass hits in climax
live_loop :brass, sync: :metronome do
  current_section = get_section(current_tempo)
  
  if current_section == :c
    use_synth :hollow
    with_fx :reverb, mix: 0.3 do
      play_chord [:eb3, :g3, :bb3], sustain: 0.5, volume: 0.8 if factor?(0, 8)
      play_chord [:f3, :ab3, :c4], sustain: 0.25, volume: 0.6 if factor?(4, 8)
    end
  end
  sleep 1
end

# Transition effects and sweeps
live_loop :transitions, sync: :metronome do
  current_section = get_section(current_tempo)
  
  if current_section == :b && factor?(15, 16)
    # Rising sweep into climax
    with_fx :lpf, cutoff: line(60, 130, steps: 8) do
      synth :sine, note: :c2, sustain: 2, volume: 0.5
    end
  elsif current_section == :c && factor?(0, 32)
    # Impact on section start
    sample :bd_boom, rate: 0.7, volume: 1.0
  elsif current_section == :d && factor?(0, 16)
    # Final cymbal tail
    sample :drum_cymbal_open, sustain: 4, volume: 0.8
  end
  
  sleep 1
end

# Master tempo control and section management
live_loop :metronome do
  current_time = beat / 4.0  # Convert to bars
  
  if current_time >= section_d_start
    current_tempo = line(115, 60, steps: 32).tick if current_time < section_d_start + 32
    use_bpm current_tempo
    sleep 0.25
  elsif current_time >= section_c_start
    current_tempo = 115
    use_bpm current_tempo
    sleep 0.25
  elsif current_time >= section_b_start
    current_tempo = line(70, 115, steps: transition_duration).tick
    use_bpm current_tempo
    sleep 0.25
  else
    current_tempo = 70
    use_bpm current_tempo
    sleep 0.25
  end
end

# Helper function to determine current section
define :get_section do |tempo_param|
  current_time_value = beat / 4.0
  
  if current_time_value >= section_d_start
    :d
  elsif current_time_value >= section_c_start
    :c
  elsif current_time_value >= section_b_start
    :b
  else
    :a
  end
end

# MIDI output setup for external instruments
live_loop :midi_out, sync: :metronome do
  current_section = get_section(current_tempo)
  
  if current_section == :c
    # Send MIDI notes for the climax melody
    begin
      midi eb_major_scale_pattern[0..3], port: "iac_driver_bus_1" if factor?(0, 8)
    rescue
      # Handle MIDI error gracefully
    end
  end
  
  sleep 2
end

# Print section changes for monitoring
live_loop :section_monitor, sync: :metronome do
  current_section = get_section(current_tempo)
  puts "Section: #{current_section}, BPM: #{current_tempo.round(1)}"
  sleep 4
end