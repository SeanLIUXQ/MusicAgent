# Universal Uplift - Ambient Pop Composition
# Tempo: 108 BPM, Key: C Major, Time Signature: 4/4

use_bpm 108

# Define chord progressions using descriptive variable names
main_chord_progression = [chord(:C3, :maj7), chord(:G3, :maj), chord(:A3, :min), chord(:F3, :maj)]
bridge_chord_progression = [chord(:A3, :min), chord(:F3, :maj), chord(:C3, :maj7), chord(:G3, :maj)]

# Instrument volume settings
piano_volume = 0.8
guitar_volume = 0.6
bass_volume = 0.7
pad_volume = 0.5
lead_volume = 0.8
drum_volume = 0.6

# Main piano chords and melody
live_loop :piano_main, sync: :metronome do
  use_synth :piano
  current_chords = main_chord_progression
  
  # Intro section (bars 1-8) - soft and sparse
  if tick < 32
    with_fx :reverb, room: 0.8, mix: 0.3 do
      4.times do
        current_chords.each do |current_chord|
          play_chord current_chord, amp: piano_volume * 0.6, release: 2
          sleep 2
        end
      end
    end
  # Verse section (bars 9-24) - building energy
  elsif tick < 96
    with_fx :reverb, room: 0.7, mix: 0.4 do
      3.times do
        current_chords.each do |current_chord|
          play_chord current_chord, amp: piano_volume * 0.8, release: 1.5
          sleep 2
        end
      end
    end
  # Chorus and beyond - full expression
  else
    with_fx :reverb, room: 0.9, mix: 0.5 do
      current_chords.each do |current_chord|
        play_chord current_chord, amp: piano_volume, release: 2
        sleep 2
      end
    end
  end
end

# Acoustic guitar arpeggios
live_loop :guitar_arpeggios, sync: :metronome do
  use_synth :pluck
  with_fx :reverb, room: 0.6, mix: 0.3 do
    with_fx :lpf, cutoff: 90 do
      # Only enter after intro
      if tick >= 32
        chord_pattern = [:C4, :E4, :G4, :B4, :G4, :E4]
        play_pattern_timed chord_pattern, [0.25, 0.25, 0.25, 0.5, 0.25, 0.5], amp: guitar_volume, release: 0.3
      else
        sleep 8
      end
    end
  end
end

# Electric bass foundation
live_loop :bass_line, sync: :metronome do
  use_synth :fm
  # Only enter after intro
  if tick >= 32
    bass_pattern = [:C2, :C2, :G2, :G2, :A2, :A2, :F2, :F2]
    with_fx :lpf, cutoff: 70 do
      bass_pattern.each do |bass_note|
        play bass_note, amp: bass_volume, release: 1.5, attack: 0.1
        sleep 1
      end
    end
  else
    sleep 8
  end
end

# Warm pad atmosphere
live_loop :warm_pad, sync: :metronome do
  use_synth :hollow
  # Enter during verse section
  if tick >= 64
    pad_chords = [chord(:C4, :maj7), chord(:G4, :maj), chord(:A4, :min), chord(:F4, :maj)]
    with_fx :reverb, room: 0.9, mix: 0.7 do
      with_fx :lpf, cutoff: 80 do
        pad_chords.each do |pad_chord|
          play_chord pad_chord, amp: pad_volume, attack: 2, release: 6, sustain: 2
          sleep 8
        end
      end
    end
  else
    sleep 32
  end
end

# Lead melody (enters in chorus)
live_loop :lead_melody, sync: :metronome do
  use_synth :saw
  # Enter during chorus section
  if tick >= 96
    melody_notes = [:C5, :E5, :G5, :B5, :A5, :G5, :E5, :C5]
    rhythm_pattern = [1, 1, 1, 2, 1, 1, 1, 2]
    
    with_fx :reverb, room: 0.8, mix: 0.4 do
      with_fx :echo, phase: 0.75, decay: 4 do
        melody_notes.each_with_index do |melody_note, index|
          play melody_note, amp: lead_volume, release: rhythm_pattern[index], cutoff: 90
          sleep rhythm_pattern[index]
        end
      end
    end
  else
    sleep 32
  end
end

# Minimal drum kit
live_loop :drums, sync: :metronome do
  # Enter during verse section
  if tick >= 32
    4.times do |i|
      sample :bd_haus, amp: drum_volume * 0.8, rate: 0.9 if i.even?
      sample :sn_dolf, amp: drum_volume * 0.6, rate: 1.1 if i.odd?
      sleep 1
    end
  else
    sleep 8
  end
end

# Shaker for high-end texture
live_loop :shaker, sync: :metronome do
  # Enter during chorus section
  if tick >= 96
    16.times do
      sample :perc_snap2, amp: drum_volume * 0.3, rate: 2, pan: rrand(-0.3, 0.3)
      sleep 0.25
    end
  else
    sleep 16
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
    midi midi_chord, sustain: 1.5
    sleep 2
  end
end

# Structure controller
live_loop :structure do
  # Intro: 32 beats (8 bars)
  sleep 32
  
  # Verse: 64 beats (16 bars)
  sleep 64
  
  # Chorus: 64 beats (16 bars)
  sleep 64
  
  # Bridge: 32 beats (8 bars) - use bridge progression
  control :piano_main, current_chords: bridge_chord_progression
  sleep 32
  
  # Final Chorus: 64 beats (16 bars) - back to main progression
  control :piano_main, current_chords: main_chord_progression
  control :lead_melody, amp: lead_volume * 1.2
  control :drums, amp: drum_volume * 1.1
  sleep 64
  
  # Outro: fade out over 64 beats
  8.times do |i|
    fade_factor = 1.0 - (i * 0.125)
    control :piano_main, amp: piano_volume * fade_factor
    control :guitar_arpeggios, amp: guitar_volume * fade_factor
    control :bass_line, amp: bass_volume * fade_factor
    control :warm_pad, amp: pad_volume * fade_factor
    control :lead_melody, amp: lead_volume * fade_factor
    control :drums, amp: drum_volume * fade_factor
    control :shaker, amp: drum_volume * 0.3 * fade_factor
    sleep 8
  end
  
  # Stop all loops gracefully
  stop
end