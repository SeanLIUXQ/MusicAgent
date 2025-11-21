use_bpm 55
use_synth :piano

# Define musical elements
main_key = :a3
scale_pattern = scale(main_key, :minor)
chord_progression_a = [chord(:a3, :m), chord(:d3, :m), chord(:g3, :maj), chord(:c3, :maj)]
chord_progression_b = [chord(:f3, :maj), chord(:c3, :maj), chord(:g3, :maj), chord(:a3, :m)]
melody_notes = [:a4, :g4, :e4, :d4, :c4, :a3]
bass_drone = :a2

# Ambient textures and effects
with_fx :reverb, mix: 0.8, room: 0.9 do
  with_fx :echo, mix: 0.3, decay: 8 do
    
    # Section transitions controller
    live_loop :section_controller do
      cue :intro
      sleep 32  # Intro section: Only drone and piano
      
      cue :section_a
      sleep 32  # Section A: Add strings
      
      cue :section_b  
      sleep 32  # Section B: Add harp
      
      cue :section_c
      sleep 32  # Section C: Add bells and intensify
      
      cue :outro
      sleep 32  # Outro: Gradual fade
      
      cue :end
    end
    
    # Section tracker (helper loop)
    live_loop :section_tracker do
      sync :intro
      set :current_section, :intro
      sync :section_a
      set :current_section, :section_a
      sync :section_b
      set :current_section, :section_b
      sync :section_c
      set :current_section, :section_c
      sync :outro
      set :current_section, :outro
      sync :end
      set :current_section, :end
    end
    
    # Drone pad - creates atmospheric foundation
    live_loop :ambient_drone, sync: :intro do
      use_synth :hollow
      current_section = get[:current_section]
      
      with_fx :hpf, cutoff: 40 do
        if current_section == :outro
          control amp: 0.3, amp_slide: 32
          play bass_drone, attack: 4, release: 8, sustain: 4
          sleep 16
          control amp: 0.0
        else
          play bass_drone, amp: 0.3, attack: 4, release: 8, sustain: 4
          sleep 16
        end
      end
    end
    
    # Main piano motif - with variation and progression
    live_loop :piano_theme, sync: :intro do
      use_synth :piano
      current_section = get[:current_section]
      
      # Dynamic cutoff based on section
      cutoff_val = case current_section
                  when :section_c then 110
                  when :section_b then 95
                  else 90
                  end
      
      with_fx :lpf, cutoff: cutoff_val do
        # Vary melody based on section
        main_motif = case current_section
                    when :section_b
                      [melody_notes[1], melody_notes[3], melody_notes[5], melody_notes[0]]
                    when :section_c
                      [melody_notes[2], melody_notes[4], melody_notes[1], melody_notes[3]]
                    else
                      [melody_notes[0], melody_notes[2], melody_notes[4], melody_notes[1]]
                    end
        
        main_motif.each do |note|
          if current_section == :outro
            control amp: 0.4, amp_slide: 32
            play note, attack: 0.1, release: 2
            sleep 2
          else
            play note, amp: 0.4, attack: 0.1, release: 2
            sleep 2
          end
        end
      end
    end
    
    # String accompaniment - starts in section_a, stops in outro
    live_loop :strings_layer do
      sync :section_a
      stop if get[:current_section] == :outro
      
      use_synth :dsaw
      current_section = get[:current_section]
      
      with_fx :reverb, mix: 0.7 do
        # Use different chord progression for section B
        chord_seq = current_section == :section_b ? chord_progression_b : chord_progression_a
        chord_sequence = chord_seq.tick
        
        if current_section == :section_c
          play_chord chord_sequence, amp: 0.25, attack: 1.5, release: 3
        else
          play_chord chord_sequence, amp: 0.2, attack: 2, release: 4
        end
        sleep 8
      end
    end
    
    # Harp textures - starts in section_b, stops in outro
    live_loop :harp_textures do
      sync :section_b
      stop if get[:current_section] == :outro
      
      use_synth :pluck
      current_section = get[:current_section]
      
      with_fx :hpf, cutoff: 60 do
        if one_in(current_section == :section_c ? 2 : 3)
          amp_val = current_section == :section_c ? 0.2 : 0.15
          play scale_pattern.choose, amp: amp_val, release: 3
        end
        sleep 4
      end
    end
    
    # Bell-like resonances - starts in section_c, stops in outro
    live_loop :bell_resonances do
      sync :section_c
      stop if get[:current_section] == :outro
      
      use_synth :beep
      if one_in(4)
        play scale_pattern.choose + 12, amp: 0.12, attack: 0.5, release: 6
      end
      sleep 8
    end
    
    # Transition effects - subtle sweeps between sections
    live_loop :transition_effects do
      sync :section_a
      use_synth :noise
      play :c1, amp: 0.05, attack: 1, release: 3, cutoff: 80
      sleep 28
      
      sync :section_b
      use_synth :noise
      play :c1, amp: 0.05, attack: 1, release: 3, cutoff: 90
      sleep 28
      
      sync :section_c
      use_synth :noise
      play :c1, amp: 0.06, attack: 1, release: 4, cutoff: 100
    end
    
  end
end