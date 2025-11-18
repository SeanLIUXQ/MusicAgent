# Ambient Transformation - Atmospheric Soundscape
# Tempo: 72 BPM, Key: C Major, Time Signature: 4/4

use_bpm 72

# Define chord progressions using descriptive variable names
main_chord_seq = [chord(:C3, :maj7), chord(:G3, :maj), chord(:A3, :min), chord(:F3, :maj)]
bridge_chord_seq = [chord(:A3, :min), chord(:F3, :maj), chord(:C3, :maj7), chord(:G3, :maj)]

# Instrument volume settings
piano_vol = 0.6
texture_vol = 0.4
bass_vol = 0.5
pad_vol = 0.7
lead_vol = 0.5
atmo_vol = 0.3

# Global chord progression state
set :current_chord_progression, main_chord_seq

# Main ambient pad chords
live_loop :ambient_pad, sync: :metronome do
  use_synth :dark_ambience
  current_chords = get[:current_chord_progression]
  
  with_fx :reverb, room: 0.95, mix: 0.8, damp: 0.8 do
    with_fx :echo, phase: 1.5, decay: 8, mix: 0.4 do
      with_fx :lpf, cutoff: 60 do |filter|
        control filter, cutoff_slide: 16, cutoff: rrand(50, 80)
        current_chords.each do |current_chord|
          play_chord current_chord, amp: piano_vol, attack: 3, release: 8, sustain: 4
          sleep rrand(7.5, 8.5)
        end
      end
    end
  end
end

# Textural arpeggios (replaces guitar)
live_loop :texture_arpeggios, sync: :metronome do
  use_synth :dsaw
  with_fx :reverb, room: 0.9, mix: 0.7 do
    with_fx :lpf, cutoff: 60 do |filter|
      control filter, cutoff_slide: 4, cutoff: rrand(50, 80)
      chord_pattern = [:C4, :E4, :G4, :B4, :G4, :E4]
      play_pattern_timed chord_pattern, [0.5, 0.5, 0.5, 1.0, 0.5, 1.0], amp: texture_vol, release: 1.5, attack: 0.5
    end
  end
end

# Sub bass drone (replaces bass line)
live_loop :bass_drone, sync: :metronome do
  use_synth :hollow
  with_fx :lpf, cutoff: 50 do
    with_fx :reverb, room: 0.8, mix: 0.6 do
      bass_notes = [:C1, :G1, :A1, :F1]
      bass_notes.each do |bass_note|
        play bass_note, amp: bass_vol, attack: 2, release: 6, sustain: 4
        sleep rrand(7.8, 8.2)
      end
    end
  end
end

# Warm evolving pad
live_loop :evolving_pad, sync: :metronome do
  use_synth :prophet
  pad_chords = [chord(:C4, :maj7), chord(:G4, :maj), chord(:A4, :min), chord(:F4, :maj)]
  with_fx :reverb, room: 0.98, mix: 0.9 do
    with_fx :echo, phase: 2.0, decay: 12, mix: 0.5 do
      with_fx :lpf, cutoff: 70 do |filter|
        control filter, cutoff_slide: 32, cutoff: rrand(60, 90)
        pad_chords.each do |pad_chord|
          play_chord pad_chord, amp: pad_vol, attack: 4, release: 12, sustain: 6
          sleep rrand(15.5, 16.5)
        end
      end
    end
  end
end

# Ethereal lead melody
live_loop :ethereal_lead, sync: :metronome do
  use_synth :sine
  melody_notes = [:C5, :E5, :G5, :B5, :A5, :G5, :E5, :C5]
  rhythm_pattern = [2, 2, 2, 4, 2, 2, 2, 4]
  
  with_fx :reverb, room: 0.9, mix: 0.8 do
    with_fx :echo, phase: 1.25, decay: 6, mix: 0.6 do
      melody_notes.each_with_index do |melody_note, index|
        play melody_note, amp: lead_vol, release: rhythm_pattern[index] * 0.8, attack: 0.5
        sleep rhythm_pattern[index] * 0.9 + rrand(-0.2, 0.2)
      end
    end
  end
end

# Atmospheric percussion (replaces drums)
live_loop :atmospheric_perc, sync: :metronome do
  with_fx :reverb, room: 0.95, mix: 0.9 do
    with_fx :lpf, cutoff: 70 do
      8.times do
        sample :ambi_glass_rub, amp: atmo_vol * 0.4, rate: rrand(0.8, 1.2), pan: rrand(-0.5, 0.5)
        sleep rrand(3.5, 4.5)
      end
    end
  end
end

# Wind-like texture (replaces shaker)
live_loop :wind_texture, sync: :metronome do
  use_synth :noise
  with_fx :reverb, room: 0.98, mix: 0.8 do
    with_fx :lpf, cutoff: 50 do |filter|
      control filter, cutoff_slide: 16, cutoff: rrand(40, 70)
      play :C2, amp: atmo_vol * 0.3, attack: 4, release: 12, sustain: 8
      sleep rrand(15, 17)
    end
  end
end

# Additional atmospheric drones for enhanced ambient texture
live_loop :atmospheric_drones, sync: :metronome do
  use_synth :growl
  with_fx :reverb, room: 0.99, mix: 0.9 do
    with_fx :lpf, cutoff: 50 do |filter|
      control filter, cutoff_slide: 32, cutoff: rrand(40, 70)
      play_chord chord(:C2, :maj7), amp: 0.2, attack: 8, release: 16
      sleep 32
    end
  end
end

# Metronome for synchronization
live_loop :metronome do
  cue :tick
  sleep 8
end

# MIDI output setup
live_loop :midi_output, sync: :metronome do
  use_real_time
  midi_chords = [chord(:C3, :maj7), chord(:G3, :maj), chord(:A3, :min), chord(:F3, :maj)]
  
  midi_chords.each do |midi_chord|
    midi midi_chord, sustain: 3.0
    sleep 2
  end
end

# Section-based structure controller for better timing alignment
live_loop :section_manager do
  cue :intro
  sleep 64  # Allow for random timing variations
  
  cue :main
  control :ambient_pad, amp: piano_vol * 1.1
  control :evolving_pad, amp: pad_vol * 1.2
  sleep 256
  
  cue :bridge
  set :current_chord_progression, bridge_chord_seq
  control :bass_drone, amp: bass_vol * 1.1
  sleep 64
  
  cue :final
  set :current_chord_progression, main_chord_seq
  control :ethereal_lead, amp: lead_vol * 1.3
  sleep 192
  
  cue :outro
  # Gradual fade out over 256 beats (64 bars)
  32.times do |i|
    fade_factor = 1.0 - (i * 0.03125)
    control :ambient_pad, amp: piano_vol * fade_factor
    control :texture_arpeggios, amp: texture_vol * fade_factor
    control :bass_drone, amp: bass_vol * fade_factor
    control :evolving_pad, amp: pad_vol * fade_factor
    control :ethereal_lead, amp: lead_vol * fade_factor
    control :atmospheric_perc, amp: atmo_vol * fade_factor
    control :wind_texture, amp: atmo_vol * 0.3 * fade_factor
    control :atmospheric_drones, amp: 0.2 * fade_factor
    sleep 8
  end
  
  # Stop all loops gracefully
  stop
end