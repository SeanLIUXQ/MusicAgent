use_bpm 70 # Master BPM

# Define musical scales and motifs
pentatonic_scale = (scale :d3, :minor_pentatonic, num_octaves: 2)
western_minor_scale = (scale :d3, :minor, num_octaves: 2)

# Conductor loop to manage section timing
live_loop :conductor do
  # Section 1: Introduction (8 bars)
  cue :section_intro
  sleep 8 # 8 bars * 4 beats/bar
  
  # Section 2: Main Theme A (16 bars)
  cue :section_main
  sleep 8
  
  # Section 3: Section B - Tension (16 bars)
  cue :section_tension
  sleep 8
  
  # Section 4: Development (16 bars)
  cue :section_development
  sleep 8
  
  # Section 5: Climax (8 bars)
  cue :section_climax
  sleep 8
  
  # Section 6: Conclusion (8 bars)
  cue :section_conclusion
  sleep 8
  
  stop # Stop the entire piece
end

# Section 1: Introduction
live_loop :intro_flute, sync: :conductor do
  stop
  sync :section_intro
  use_synth :hollow
  with_fx :reverb, mix: 0.6 do
    # Flute introduction with pentatonic theme
    intro_melody = [:d4, :f4, :g4, :a4, :c5, :a4, :g4, :f4]
    intro_melody.each do |note|
      play note, amp: 0.8, attack: 0.1, release: 0.5, pan: 0.3
      sleep 0.75
    end
  end
  stop
end

live_loop :intro_strings, sync: :conductor do
  stop
  sync :section_intro
  use_synth :saw
  with_fx :lpf, cutoff: 80 do
    with_fx :reverb, room: 0.4 do
      # Strings gradually entering with dynamic build
      4.times do |i|
        play chord(:d3, :m7), amp: 0.2 + (i * 0.1), attack: 2, release: 4, pan: -0.2
        sleep 4
      end
    end
  end
  stop
end

# Section 2: Main Theme A
live_loop :main_theme_strings, sync: :conductor do
  stop
  sync :section_main
  use_synth :prophet
  with_fx :reverb, room: 0.8 do
    with_fx :hpf, cutoff: 100 do
      4.times do |iteration|
        # Melodic variation on different iterations
        case iteration
        when 0, 1
          main_melody = [:d4, :f4, :g4, :bb4, :a4, :g4, :f4, :d4]
        when 2
          main_melody = [:d4, :f4, :g4, :bb4, :c5, :a4, :f4, :d4]
        else
          main_melody = [:d4, :f4, :g4, :bb4, :a4, :c5, :bb4, :g4]
        end
        
        # Dynamic build
        current_amp = 0.6 + (iteration * 0.05)
        
        main_melody.each do |note|
          play note, amp: current_amp, attack: 0.1, release: 0.8, pan: 0.1
          sleep 1
        end
      end
    end
  end
  stop
end

live_loop :erhu_counterpoint, sync: :conductor do
  stop
  sync :section_main
  use_synth :fm
  with_fx :vibrato, depth: 0.3 do
    with_fx :reverb, room: 0.3 do
      4.times do |iteration|
        # Erhu phrase with variation
        erhu_phrase = [:a4, :g4, :f4, :d4, :f4, :g4, :a4, :c5]
        if iteration == 3
          erhu_phrase = [:a4, :g4, :f4, :d4, :f4, :g4, :bb4, :c5]
        end
        
        erhu_phrase.each do |note|
          play note, amp: 0.5 + (iteration * 0.03), attack: 0.2, release: 1.2, pan: -0.3
          sleep 1.5
        end
      end
    end
  end
  stop
end

live_loop :cello_bass, sync: :conductor do
  stop
  sync :section_main
  use_synth :saw
  with_fx :lpf, cutoff: 70 do
    with_fx :eq, low_shelf: -0.5 do
      4.times do |iteration|
        bass_line = [:d2, :a2, :g2, :d2]
        if iteration == 2
          bass_line = [:d2, :a2, :g2, :f2] # Variation
        end
        
        bass_line.each do |note|
          play note, amp: 0.5, attack: 0.1, release: 0.8, pan: -0.2
          sleep 2
        end
      end
    end
  end
  stop
end

# Transition to tension section
live_loop :transition_riser, sync: :conductor do
  stop
  sync_bpm :section_main
  sleep 8 # Start 2 bars before section end
  
  # Rising effect to build tension
  with_fx :lpf, cutoff: 60 do
    with_fx :reverb, room: 0.8 do
      16.times do |i|
        use_synth :sine
        play :c6, amp: 0.1 + (i * 0.02), release: 0.1, pan: rrand(-0.5, 0.5)
        sleep 0.125
      end
    end
  end
  stop
end

# Section 3: Tension Building
live_loop :tension_section, sync: :conductor do
  stop
  sync :section_tension
  use_synth :saw
  with_fx :distortion, mix: 0.2 do
    with_fx :lpf, cutoff: 90 do
      4.times do |iteration|
        # Improved chord progression for better tension
        tension_chords = [chord(:a3, :m7), chord(:d4, :m7), chord(:g3, :dim), chord(:c4, :7)]
        
        tension_chords.each_with_index do |chord_notes, idx|
          current_amp = 0.7 + (iteration * 0.05)
          play chord_notes, amp: current_amp, attack: 0.05, release: 0.5, pan: rrand(-0.1, 0.1)
          sleep 1.5
        end
      end
    end
  end
  stop
end

live_loop :pipa_rhythm, sync: :conductor do
  stop
  sync :section_tension
  use_synth :pluck
  with_fx :ping_pong, mix: 0.3 do
    with_fx :reverb, room: 0.2 do
      4.times do |iteration|
        # Pipa rhythmic patterns with variation
        rhythm_pattern = [:g4, :r, :a4, :r, :bb4, :g4, :r, :a4]
        if iteration == 2
          rhythm_pattern = [:g4, :r, :a4, :bb4, :r, :g4, :a4, :r]
        end
        
        rhythm_pattern.each do |note|
          if note == :r
            sleep 0.25
          else
            play note, amp: 0.4, release: 0.1, pan: 0.4
            sleep 0.25
          end
        end
      end
    end
  end
  stop
end

live_loop :chinese_drums, sync: :conductor do
  stop
  sync :section_tension
  with_fx :reverb, room: 0.3 do
    4.times do |iteration|
      # Chinese drum patterns with increasing complexity
      drum_hits = [1, 0, 1, 0, 1, 1, 0, 1]
      if iteration == 3
        drum_hits = [1, 0, 1, 1, 0, 1, 1, 1] # More intense for transition
      end
      
      drum_hits.each do |hit|
        if hit == 1
          sample :drum_tom_hi_hard, amp: 0.6 + (iteration * 0.1), rate: 0.8, pan: rrand(-0.2, 0.2)
        end
        sleep 0.5
      end
    end
  end
  stop
end

# Section 4: Development
live_loop :development_synth, sync: :conductor do
  stop
  sync :section_development
  use_synth :hollow
  with_fx :wobble, phase: 2 do
    with_fx :reverb, room: 0.5 do
      4.times do |iteration|
        dev_melody = [:f4, :g4, :bb4, :c5, :d5, :c5, :bb4, :g4]
        if iteration == 3
          dev_melody = [:f4, :g4, :bb4, :c5, :d5, :eb5, :d5, :c5] # Higher climax
        end
        
        current_amp = 0.5 + (iteration * 0.03)
        dev_melody.each do |note|
          play note, amp: current_amp, attack: 0.3, release: 1.0, pan: rrand(-0.1, 0.1)
          sleep 1
        end
      end
    end
  end
  stop
end

live_loop :development_strings, sync: :conductor do
  stop
  sync :section_development
  use_synth :saw
  with_fx :reverb, mix: 0.7 do
    with_fx :hpf, cutoff: 80 do
      4.times do |iteration|
        string_pads = [chord(:d3, :m9), chord(:g3, :m9), chord(:c4, :m9), chord(:f3, :m9)]
        current_amp = 0.3 + (iteration * 0.03)
        
        string_pads.each do |chord_notes|
          play chord_notes, amp: current_amp, attack: 1, release: 3, pan: rrand(-0.3, 0.3)
          sleep 4
        end
      end
    end
  end
  stop
end

# Climax transition with drum fill
live_loop :climax_transition, sync: :conductor do
  stop
  sync_bpm :section_development
  sleep 8 # Start fill 2 bars before climax
  
  with_fx :reverb, room: 0.5 do
    16.times do |i|
      sample :drum_tom_hi_hard, amp: 0.4 + (i * 0.05), rate: 1.0 + (i * 0.05), pan: rrand(-0.5, 0.5)
      sleep 0.125
    end
  end
  stop
end

# Section 5: Climax
live_loop :climax_full, sync: :conductor do
  stop
  sync :section_climax
  use_synth :saw
  with_fx :reverb, room: 1.0 do
    with_fx :hpf, cutoff: 200 do
      2.times do |iteration|
        climax_melody = [:d4, :f4, :g4, :bb4, :a4, :c5, :d5, :f5]
        if iteration == 1
          climax_melody = [:d4, :f4, :g4, :bb4, :a4, :c5, :eb5, :g5] # Higher variation
        end
        
        current_amp = 0.9 + (iteration * 0.1)
        climax_melody.each do |note|
          play note, amp: current_amp, attack: 0.05, release: 0.3, pan: rrand(-0.2, 0.2)
          sleep 0.25
        end
      end
    end
  end
  stop
end

live_loop :climax_drums, sync: :conductor do
  stop
  sync :section_climax
  with_fx :reverb, room: 0.4 do
    4.times do |iteration|
      # Intense drumming with variation
      8.times do |i|
        amp_val = 1.0 + (iteration * 0.1)
        sample :drum_bass_hard, amp: amp_val, pan: rrand(-0.1, 0.1)
        sleep 0.125
      end
    end
  end
  stop
end

live_loop :gong_impact, sync: :conductor do
  stop
  sync :section_climax
  # Gong sound for dramatic emphasis at climax peak
  sleep 8 # Wait for the right moment
  with_fx :reverb, room: 1.0 do
    sample :misc_cineboom, amp: 1.5, rate: 0.7, pan: 0
  end
  sleep 2
  stop
end

# Section 6: Conclusion
live_loop :conclusion_flute, sync: :conductor do
  stop
  sync :section_conclusion
  use_synth :hollow
  with_fx :reverb, mix: 0.8 do
    # Return to flute theme, fading out with variation
    conclusion_melody = [:d4, :f4, :g4, :a4, :g4, :f4, :d4, :r]
    
    conclusion_melody.each do |note|
      if note == :r
        sleep 1
      else
        play note, amp: 0.8, attack: 0.2, release: 1.5, pan: 0.3
        sleep 1
      end
    end
  end
  stop
end

live_loop :fadeout_strings, sync: :conductor do
  stop
  sync :section_conclusion
  use_synth :saw
  with_fx :lpf, cutoff: 60 do
    with_fx :reverb, room: 0.5 do
      # Strings fading out gradually with harmonic variation
      4.times do |i|
        fade_chord = chord(:d3, :m7)
        if i == 2
          fade_chord = chord(:d3, :m9) # Richer harmony
        end
        
        play fade_chord, amp: 0.5 - (i * 0.1), attack: 1, release: 4, pan: -0.2
        sleep 4
      end
    end
  end
  stop
end

# Final wind chime effect
live_loop :ending_chimes, sync: :conductor do
  stop
  sync :section_conclusion
  sleep 8 # Start in the last 2 bars
  
  with_fx :reverb, room: 0.8 do
    4.times do |i|
      use_synth :pretty_bell
      play [:d5, :f5, :a5].choose, amp: 0.3 - (i * 0.07), release: 2, pan: rrand(-0.5, 0.5)
      sleep 2
    end
  end
  stop
end