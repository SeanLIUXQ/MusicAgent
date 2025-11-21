use_bpm 120 # Faster tempo for jazz feel

# Define musical scales and motifs with jazz extensions
pentatonic_pattern = (scale :d3, :minor_pentatonic, num_octaves: 2)
blues_pattern = (scale :d3, :minor_pentatonic, num_octaves: 2) + [:eb4] # Add blue note

# Jazz chord progressions
jazz_progression_1 = [chord(:d3, :m9), chord(:g3, :dom9), chord(:c4, :maj9), chord(:f4, :dom7b9)]
jazz_progression_2 = [chord(:a3, :m9), chord(:d4, :dom9), chord(:g3, :maj7), chord(:c4, :dom7)]

# Swing timing parameter
set :swing_factor, 0.1

define :swing_sleep do |duration|
  sleep duration * (1 + get[:swing_factor])
end

# Enhanced swing feel for more authentic jazz rhythm
define :jazz_swing_sleep do |duration|
  if duration == 0.5
    sleep duration * (1 + get[:swing_factor])
  else
    sleep duration
  end
end

# Conductor loop to manage section timing with jazz structure
live_loop :conductor do
  # Head in - Main theme (8 bars)
  cue :section_head_in
  sleep 8
  
  # Solo section 1 (16 bars)
  cue :section_solo_1
  sleep 8
  
  # Solo section 2 (16 bars)
  cue :section_solo_2
  sleep 8
  
  # Head out - Return to theme (8 bars)
  cue :section_head_out
  sleep 8
  
  stop # Stop the entire piece
end

# Section 1: Head In
live_loop :head_piano, sync: :conductor do
  stop
  sync :section_head_in
  use_synth :piano
  with_fx :reverb, room: 0.8 do
    with_fx :flanger, phase: 0.25 do
      # Jazz piano comping with swing
      head_melody = [:d4, :f4, :g4, :bb4, :a4, :c5, :a4, :g4]
      head_melody.each do |note|
        play note, amp: 0.6, attack: 0.05, release: 0.3, pan: 0.2
        jazz_swing_sleep 0.75
      end
    end
  end
  stop
end

live_loop :head_bass, sync: :conductor do
  stop
  sync :section_head_in
  use_synth :sine
  with_fx :lpf, cutoff: 80 do
    with_fx :reverb, room: 0.3 do
      # Walking bass line
      4.times do |i|
        bass_walk = [:d2, :f2, :a2, :c3, :d2, :f2, :g2, :bb2]
        current_amp = 0.4 + (i * 0.05)
        
        bass_walk.each do |note|
          play note, amp: current_amp, release: 0.2, pan: -0.3
          jazz_swing_sleep 0.5
        end
      end
    end
  end
  stop
end

# Section 2: Solo 1
live_loop :solo_trumpet, sync: :conductor do
  stop
  sync :section_solo_1
  use_synth :beep
  with_fx :reverb, room: 0.6 do
    with_fx :chorus, phase: 0.5 do
      4.times do |iteration|
        # Jazz trumpet solo with blues influence and dynamic variation
        case iteration
        when 0, 1
          solo_phrase = [:d4, :f4, :g4, :bb4, :a4, :c5, :eb5, :g5] # Blue note added
        when 2
          solo_phrase = [:d4, :f4, :g4, :bb4, :c5, :a4, :f4, :eb4] # More bluesy
        else
          solo_phrase = [:d4, :f4, :g4, :bb4, :a4, :c5, :eb5, :f5] # Chromatic approach
        end
        
        # Dynamic build with crescendo
        current_amp = 0.5 + (iteration * 0.03)
        
        solo_phrase.each do |note|
          play note, amp: current_amp, attack: 0.1, release: 0.5, pan: 0.1
          jazz_swing_sleep 1
        end
      end
    end
  end
  stop
end

live_loop :solo_piano_comp, sync: :conductor do
  stop
  sync :section_solo_1
  use_synth :piano
  with_fx :reverb, room: 0.4 do
    4.times do |iteration|
      # Piano comping with jazz chords
      jazz_chords = jazz_progression_1
      current_amp = 0.3 + (iteration * 0.02)
      
      jazz_chords.each do |chord_notes|
        play chord_notes, amp: current_amp, attack: 0.1, release: 1.5, pan: rrand(-0.2, 0.2)
        sleep 2
      end
    end
  end
  stop
end

live_loop :jazz_drums, sync: :conductor do
  stop
  sync :section_solo_1
  with_fx :reverb, room: 0.2 do
    4.times do |iteration|
      # Jazz drum kit with ride pattern and brush variation
      16.times do |i|
        if i % 4 == 0
          sample :drum_bass_soft, amp: 0.5 + (iteration * 0.05), pan: -0.1
        elsif i % 4 == 2
          sample :drum_snare_soft, amp: 0.4 + (iteration * 0.03), pan: 0.1
        end
        
        # Ride cymbal pattern with brush variation
        if iteration == 0
          sample :drum_cymbal_pedal, amp: 0.1 + (iteration * 0.01), pan: 0.2
        else
          sample :drum_cymbal_open, amp: 0.08 + (iteration * 0.01), pan: 0.2
        end
        jazz_swing_sleep 0.25
      end
    end
  end
  stop
end

# Section 3: Solo 2
live_loop :solo_sax, sync: :conductor do
  stop
  sync :section_solo_2
  use_synth :prophet
  with_fx :reverb, room: 0.7 do
    with_fx :flanger, phase: 0.75 do
      4.times do |iteration|
        # Saxophone solo with more complex phrasing and dynamic variation
        sax_phrases = [
          [:d4, :f4, :g4, :bb4, :a4, :c5, :eb5, :g5],
          [:d4, :eb4, :f4, :g4, :bb4, :a4, :c5, :d5],
          [:d4, :f4, :g4, :a4, :bb4, :c5, :eb5, :f5],
          [:d4, :f4, :g4, :bb4, :a4, :ab4, :g4, :f4] # Chromatic descent
        ]
        
        # Dynamic variation with decrescendo on final phrase
        current_amp = iteration == 3 ? 0.7 - (iteration * 0.1) : 0.6 + (iteration * 0.04)
        phrase = sax_phrases[iteration]
        
        phrase.each do |note|
          play note, amp: current_amp, attack: 0.15, release: 0.8, pan: -0.2
          jazz_swing_sleep 1
        end
      end
    end
  end
  stop
end

live_loop :walking_bass_solo, sync: :conductor do
  stop
  sync :section_solo_2
  use_synth :sine
  with_fx :lpf, cutoff: 90 do
    with_fx :reverb, room: 0.2 do
      4.times do |iteration|
        # More active walking bass during solo section with chromatic passing tones
        bass_patterns = [
          [:d2, :f2, :a2, :c3, :eb2, :f2, :g2, :bb2],
          [:d2, :e2, :f2, :g2, :a2, :bb2, :c3, :d3],
          [:d2, :f2, :ab2, :bb2, :c3, :eb3, :f3, :g3],
          [:d2, :f2, :a2, :c3, :d2, :f2, :g2, :bb2]
        ]
        
        current_amp = 0.5 + (iteration * 0.03)
        pattern = bass_patterns[iteration]
        
        pattern.each do |note|
          play note, amp: current_amp, release: 0.15, pan: -0.3
          jazz_swing_sleep 0.5
        end
      end
    end
  end
  stop
end

# Rhythm section stabs for added jazz texture
live_loop :rhythm_stabs, sync: :conductor do
  stop
  sync :section_solo_2
  use_synth :piano
  with_fx :reverb, room: 0.3 do
    2.times do |i|
      # Occasional rhythm hits
      sleep 6
      play chord(:d4, :dom7), amp: 0.4, attack: 0.01, release: 0.2, pan: rrand(-0.3, 0.3)
      sleep 2
    end
  end
  stop
end

# Drum fill transition
live_loop :drum_fill, sync: :conductor do
  stop
  sync_bpm :section_solo_2
  sleep 8 # Start fill before section end
  
  with_fx :reverb, room: 0.3 do
    # Jazz drum fill
    8.times do |i|
      sample :drum_tom_hi_soft, amp: 0.3 + (i * 0.05), rate: 1.0, pan: rrand(-0.3, 0.3)
      jazz_swing_sleep 0.125
    end
  end
  stop
end

# Section 4: Head Out
live_loop :head_out_piano, sync: :conductor do
  stop
  sync :section_head_out
  use_synth :piano
  with_fx :reverb, room: 0.8 do
    with_fx :chorus, phase: 0.5 do
      # Return to head melody with variation
      outro_melody = [:d4, :f4, :g4, :bb4, :a4, :c5, :a4, :g4, :f4, :d4, :r, :r]
      
      outro_melody.each do |note|
        if note == :r
          jazz_swing_sleep 1
        else
          play note, amp: 0.7, attack: 0.1, release: 0.8, pan: 0.2
          jazz_swing_sleep 0.75
        end
      end
    end
  end
  stop
end

live_loop :fadeout_bass, sync: :conductor do
  stop
  sync :section_head_out
  use_synth :sine
  with_fx :lpf, cutoff: 70 do
    with_fx :reverb, room: 0.4 do
      # Bass fading out gradually
      4.times do |i|
        bass_notes = [:d2, :f2, :a2, :c3]
        current_amp = 0.5 - (i * 0.1)
        
        bass_notes.each do |note|
          play note, amp: current_amp, release: 0.3, pan: -0.3
          sleep 1
        end
      end
    end
  end
  stop
end

# Final jazz ending with authentic progression
live_loop :ending_comp, sync: :conductor do
  stop
  sync :section_head_out
  sleep 6 # Start in the last bars
  
  use_synth :piano
  with_fx :reverb, room: 0.6 do
    # Authentic jazz ending progression
    ending_chords = [chord(:d3, :maj9), chord(:g3, :dom9), chord(:c4, :maj7), chord(:f4, :maj7), chord(:bb3, :dom7), chord(:eb3, :maj7), chord(:d3, :maj7)]
    
    ending_chords.each do |chord_notes|
      play chord_notes, amp: 0.4, attack: 0.2, release: 2.0, pan: rrand(-0.2, 0.2)
      sleep 1
    end
  end
  stop
end

# Trading fours section for authentic jazz interaction
live_loop :trading_fours, sync: :conductor do
  stop
  sync :section_solo_2
  sleep 8 # Start in the middle of solo section
  
  use_synth :beep
  with_fx :reverb, room: 0.5 do
    # Short four-bar trumpet phrase
    trade_phrase = [:d4, :f4, :g4, :bb4, :a4, :c5, :eb5, :d5]
    trade_phrase.each do |note|
      play note, amp: 0.5, attack: 0.05, release: 0.3, pan: 0.1
      jazz_swing_sleep 0.5
    end
  end
  stop
end

# Allow MIDI output
use_midi_defaults port: "iac_driver_bus_1" if defined?(use_midi_defaults)