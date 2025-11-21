# Beethoven's Fate Symphony - Sonic Pi Interpretation
# Based on Symphony No. 5 in C minor, Op. 67

use_bpm 110

# Define core musical elements with safe variable names
fate_motif_rhythm = [0.25, 0.25, 0.25, 0.75] # Short-Short-Short-Long
fate_motif_pitches = [:g4, :g4, :g4, :eb4] # G-G-G-Eb

# Key centers and modulations
primary_key = :c # C minor
relative_major = :eb3 # Eb major for contrast
parallel_major = :c4 # C major for triumph

# Chord progressions for different sections (FIXED: no 'chord' conflict)
exposition_chord_roots = [:c3, :eb3, :f3, :g3] # Cm, Eb, Fm, G
development_chord_roots = [:ab3, :bb3, :f3, :c3] # Ab, Bb, Fm, Cm
recapitulation_chord_roots = [:c3, :eb3, :f3, :c4] # Cm, Eb, Fm, C major

# Dynamic levels (FIXED: no 'amp' conflict)
dynamic_pp = 0.3
dynamic_p = 0.5
dynamic_mf = 0.7
dynamic_f = 0.9
dynamic_ff = 1.2
dynamic_sfz = 1.5

# Section control flags
@section_active = {
  exposition: true,
  development: false,
  recapitulation: false
}

# Master volume control
master_volume = 1.0

# Instrumentation setup
define :string_synth do
  use_synth :hollow
  use_synth_defaults attack: 0.1, release: 0.3, amp: 0.8
end

define :brass_synth do
  use_synth :fm
  use_synth_defaults attack: 0.05, release: 0.2, amp: 0.7
end

define :woodwind_synth do
  use_synth :beep
  use_synth_defaults attack: 0.08, release: 0.4, amp: 0.6
end

define :timpani_synth do
  use_synth :sine
  use_synth_defaults attack: 0.01, release: 1.0, amp: 0.9
end

# Fate motif function - the core musical idea
define :play_fate_motif do |root_note = :c4, dynamic_level = dynamic_f, instrument = :string|
  # Validate inputs
  unless [:string, :brass, :woodwind].include?(instrument)
    puts "Invalid instrument: #{instrument}"
    return
  end
  
  case instrument
  when :string
    string_synth
  when :brass
    brass_synth
  when :woodwind
    woodwind_synth
  end
  
  # Play the iconic rhythm with appropriate pitches
  play root_note, amp: dynamic_level * master_volume
  sleep fate_motif_rhythm[0]
  play root_note, amp: dynamic_level * master_volume
  sleep fate_motif_rhythm[1]
  play root_note, amp: dynamic_level * master_volume
  sleep fate_motif_rhythm[2]
  play note(root_note) - 3, amp: dynamic_level * master_volume # Minor third down
  sleep fate_motif_rhythm[3]
end

# Exposition Section - First Movement (Allegro con brio)
live_loop :exposition_strings, sync: :conductor do
  stop
  with_fx :reverb, room: 0.3 do
    string_synth
    
    # Fate motif in C minor
    2.times do
      play_fate_motif(:g4, dynamic_f, :string)
    end
    
    # Answering phrase
    play :eb4, amp: dynamic_p * master_volume, release: 1.0
    sleep 1.0
    play :f4, amp: dynamic_mf * master_volume, release: 1.0
    sleep 1.0
    play :g4, amp: dynamic_sfz * master_volume, release: 0.5
    sleep 0.5
  end
end

live_loop :exposition_brass, sync: :conductor do
  stop
  with_fx :lpf, cutoff: 80 do
    brass_synth
    
    # Harmonic foundation (FIXED: using chord_roots instead of chords)
    exposition_chord_roots.each do |chord_root|
      play_chord chord(chord_root, :minor), amp: dynamic_p * master_volume, release: 2.0
      sleep 2.0
    end
  end
end

# Development Section - Increased tension
live_loop :development_woodwinds, sync: :conductor do
  stop
  woodwind_synth
  
  # Modulating through different keys
  development_keys = [:ab3, :bb3, :f3, :c3]
  development_keys.each do |dev_key|
    play_fate_motif(note(dev_key) + 7, dynamic_mf, :woodwind) # Play motif in new key
    sleep 1.0
  end
end

# Recapitulation - Return and triumph
live_loop :recapitulation_full, sync: :conductor do
  stop
  # Build up to climax
  with_fx :reverb, room: 0.8 do
    # Strings play fate motif with increasing intensity (FIXED: dynamic variables)
    4.times do |i|
      current_dynamic = [dynamic_mf, dynamic_f, dynamic_ff, dynamic_sfz][i]
      play_fate_motif(:g4, current_dynamic, :string)
    end
    
    # Transition to C major for triumphant ending
    sleep 2.0
    play_chord chord(:c4, :major), amp: dynamic_ff * master_volume, release: 4.0
    sleep 4.0
  end
end

# Timpani for rhythmic drive
live_loop :timpani_rhythm, sync: :conductor do
  stop
  timpani_synth
  
  # Timpani tuned to C and G
  play :c2, amp: 0.6 * master_volume
  sleep 1.0
  play :g2, amp: 0.4 * master_volume
  sleep 1.0
  play :c2, amp: 0.7 * master_volume
  sleep 0.5
  play :g2, amp: 0.5 * master_volume
  sleep 0.5
end

# Conductor loop to manage sections
live_loop :conductor do
  # Exposition - 16 beats
  puts "EXPOSITION - C minor"
  @section_active = {exposition: true, development: false, recapitulation: false}
  sync_bpm :conductor
  sleep 16
  
  # Development - 16 beats with ritardando (FIXED: use_bpm instead of current_bpm)
  puts "DEVELOPMENT - Building tension"
  @section_active = {exposition: false, development: true, recapitulation: false}
  use_bpm 90  # ritardando effect
  sleep 16
  
  # Recapitulation - 16 beats a tempo
  puts "RECAPITULATION - Return and triumph"
  @section_active = {exposition: false, development: false, recapitulation: true}
  use_bpm 110 # a tempo
  sleep 16
  
  # Coda - Final statement
  puts "CODA - Final resolution"
  sleep 8
end

# MIDI output setup for external instruments
live_loop :midi_output, sync: :conductor do
  stop
  use_real_time
  
  # Send fate motif via MIDI
  fate_motif_pitches.each_with_index do |pitch, index|
    midi pitch, sustain: fate_motif_rhythm[index]
    sleep fate_motif_rhythm[index]
  end
end

# Uncomment sections to hear different parts:
# sync :conductor
# live_loop :exposition_strings do; ...; end
# live_loop :exposition_brass do; ...; end
# live_loop :development_woodwinds do; ...; end
# live_loop :recapitulation_full do; ...; end
# live_loop :timpani_rhythm do; ...; end

puts "Beethoven's Fate Symphony loaded. Uncomment live_loops to hear different sections."
puts "Core Fate Motif: G-G-G-Eb (Short-Short-Short-Long rhythm)"