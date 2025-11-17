# Beethoven's Fate Symphony - Rock Transformation
# Heavy drums and aggressive rock interpretation

use_bpm 120  # Slightly faster for rock energy

# Define core musical elements with safe variable names
fate_motif_rhythm = [0.125, 0.125, 0.25, 0.375, 0.125]  # Faster attack for more drive
fate_motif_pitches = [:g2, :g2, :g2, :eb2, :g2]    # Lower octave for rock power

# Power chord progressions for rock sections
exposition_chord_roots = [:c2, :eb2, :f2, :g2]     # Power chord roots
development_chord_roots = [:ab2, :bb2, :f2, :c2]   # Development power chords
recapitulation_chord_roots = [:c2, :eb2, :f2, :c3] # Triumphant power chords

# Rock intensity levels (FIXED: no 'amp' conflict)
rock_quiet = 0.6
rock_medium = 0.9
rock_heavy = 1.3
rock_crash = 1.8

# Section control flags
@section_active = {
  exposition: true,
  development: false,
  recapitulation: false
}

# Master volume control
master_volume = 1.0

# Rock instrumentation setup
define :guitar_synth do
  use_synth :saw
  use_synth_defaults attack: 0.01, release: 0.2, amp: 0.8
  with_fx :distortion, distort: 0.8 do
    with_fx :lpf, cutoff: 90 do
      use_synth :saw  # Return synth inside FX blocks
    end
  end
end

define :bass_synth do
  use_synth :subpulse
  use_synth_defaults amp: 1.0, cutoff: 60, release: 0.3
end

define :lead_synth do
  use_synth :prophet
  use_synth_defaults attack: 0.05, release: 0.4, amp: 0.7
  with_fx :reverb, room: 0.4 do
    with_fx :echo, phase: 0.25, decay: 2 do
      use_synth :prophet  # Return synth inside FX blocks
    end
  end
end

# Power chord function for authentic rock sound
define :play_power_chord do |root_note, intensity_value|
  guitar_synth
  play_chord [root_note, note(root_note) + 7, note(root_note) + 12], 
             amp: intensity_value * master_volume, 
             attack: 0.05, release: 0.3
end

# Rock fate motif function - aggressive and driving
define :play_rock_motif do |root_note = :c2, intensity_level = rock_heavy, instrument = :guitar|
  # Validate inputs
  unless [:guitar, :bass, :lead].include?(instrument)
    puts "Invalid instrument: #{instrument}"
    return
  end
  
  case instrument
  when :guitar
    guitar_synth
  when :bass
    bass_synth
  when :lead
    lead_synth
  end
  
  # Play the iconic rhythm with rock aggression
  play root_note, amp: intensity_level * master_volume
  sleep fate_motif_rhythm[0]
  play root_note, amp: intensity_level * master_volume
  sleep fate_motif_rhythm[1]
  play root_note, amp: intensity_level * master_volume
  sleep fate_motif_rhythm[2]
  play note(root_note) - 3, amp: intensity_level * master_volume # Minor third down
  sleep fate_motif_rhythm[3]
  play root_note, amp: intensity_level * master_volume # Added rock resolution
  sleep fate_motif_rhythm[4]
end

# Heavy Rock Drums - The requested foundation
live_loop :rock_drums, sync: :conductor do
  stop
  with_fx :compressor, threshold: 0.1, amp: 1.2 do
    # Double kick pattern for more intensity
    sample :bd_haus, amp: 1.4 * master_volume, rate: 0.8
    sleep 0.25
    sample :bd_haus, amp: 1.0 * master_volume, rate: 0.8
    sleep 0.25
    
    # Heavy snare with reverb
    with_fx :reverb, room: 0.3 do
      sample :sn_dolf, amp: 1.2 * master_volume
    end
    sleep 0.5
    
    # Second snare
    with_fx :reverb, room: 0.3 do
      sample :sn_dolf, amp: 1.2 * master_volume
    end
    sleep 0.5
    
    # Constant hi-hat
    4.times do
      sample :drum_cymbal_closed, amp: 0.4 * master_volume
      sleep 0.25
    end
  end
end

# Crash cymbal accents for transitions
live_loop :crash_accents, sync: :conductor do
  stop
  sample :drum_cymbal_open, amp: 1.0 * master_volume, sustain: 1.0
  sleep 4.0  # Every 4 beats
end

# Exposition Section - Heavy Guitar Riff
live_loop :exposition_guitar, sync: :conductor do
  stop
  with_fx :distortion, distort: 0.7 do
    guitar_synth
    
    # Fate motif as heavy guitar riff
    2.times do
      play_rock_motif(:g2, rock_heavy, :guitar)
    end
    
    # Power chord answering phrase
    play_power_chord(:eb2, rock_medium)
    sleep 1.0
    play_power_chord(:f2, rock_medium)
    sleep 1.0
    play_power_chord(:g2, rock_crash)
    sleep 0.5
  end
end

live_loop :exposition_bass, sync: :conductor do
  stop
  with_fx :lpf, cutoff: 80 do
    bass_synth
    
    # Heavy bass foundation following power chords
    exposition_chord_roots.each do |chord_root|
      play chord_root, amp: rock_medium * master_volume, release: 1.5
      sleep 2.0
    end
  end
end

# Development Section - Increased rock tension
live_loop :development_lead, sync: :conductor do
  stop
  lead_synth
  
  # Modulating through different keys with rock intensity
  development_chord_roots.each do |dev_key|
    play_rock_motif(note(dev_key) + 7, rock_medium, :lead) # Play motif in new key
    sleep 1.0
  end
end

# Recapitulation - Heavy rock climax
live_loop :recapitulation_full, sync: :conductor do
  stop
  # Build up to rock climax
  with_fx :reverb, room: 0.6 do
    with_fx :distortion, distort: 0.9 do
      # Guitar plays fate motif with increasing rock intensity
      4.times do |i|
        current_intensity = [rock_medium, rock_heavy, rock_crash, rock_crash + 0.2][i]
        play_rock_motif(:g2, current_intensity, :guitar)
      end
      
      # Power chord triumphant ending
      sleep 1.0
      play_power_chord(:c3, rock_crash + 0.3)
      sleep 3.0
    end
  end
end

# Additional Heavy Drum Elements
live_loop :heavy_toms, sync: :conductor do
  stop
  # Tom fills for transitions
  sample :drum_tom_hi_hard, amp: 0.7 * master_volume
  sleep 0.25
  sample :drum_tom_mid_hard, amp: 0.8 * master_volume
  sleep 0.25
  sample :drum_tom_lo_hard, amp: 0.9 * master_volume
  sleep 0.5
end

# Conductor loop to manage rock sections
live_loop :conductor do
  # Verse - 16 beats (heavy riff section)
  puts "VERSE - Heavy Guitar Riff"
  @section_active = {exposition: true, development: false, recapitulation: false}
  sync_bpm :conductor
  sleep 16
  
  # Bridge - 16 beats with increased intensity
  puts "BRIDGE - Building Rock Tension"
  @section_active = {exposition: false, development: true, recapitulation: false}
  use_bpm 125  # Slight accelerando for intensity
  sleep 16
  
  # Chorus - 16 beats full rock power
  puts "CHORUS - Full Rock Power"
  @section_active = {exposition: false, development: false, recapitulation: true}
  use_bpm 120 # Return to main tempo
  sleep 16
  
  # Outro - Heavy rock ending
  puts "OUTRO - Heavy Rock Resolution"
  sleep 8
end

# MIDI output setup for external rock instruments
live_loop :midi_output, sync: :conductor do
  stop
  use_real_time
  
  # Send rock fate motif via MIDI
  fate_motif_pitches.each_with_index do |pitch, index|
    midi pitch, sustain: fate_motif_rhythm[index], velocity: 100
    sleep fate_motif_rhythm[index]
  end
end

# Uncomment sections to hear different rock parts:
# sync :conductor
# live_loop :rock_drums do; ...; end
# live_loop :exposition_guitar do; ...; end
# live_loop :exposition_bass do; ...; end
# live_loop :development_lead do; ...; end
# live_loop :recapitulation_full do; ...; end
# live_loop :heavy_toms do; ...; end

puts "Beethoven's Fate Symphony transformed to Rock Style with heavy drums!"
puts "Rock Fate Motif: G-G-G-Eb-G (Aggressive Short-Short-Short-Medium-Short rhythm)"
puts "Heavy drum foundation established with kick, snare, and cymbals"