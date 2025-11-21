use_bpm 65

# Define musical elements with improved chord progressions
main_key = :g
chord_progression_a = [
  chord(:g3, :maj7),    # I
  chord(:c3, :dom7),    # IV
  chord(:e3, :min7),    # vi
  chord(:d3, :dom7)     # V
]

chord_progression_b = [
  chord(:e3, :min7),    # i
  chord(:a3, :min7),    # iv
  chord(:c3, :maj7),    # VI
  chord(:b3, :dom7)     # VII
]

melody_notes_a = [:g4, :a4, :b4, :c5, :d5, :e5, :d5, :c5, :b4, :a4]
melody_notes_b = [:e4, :fs4, :g4, :a4, :b4, :c5, :b4, :a4, :g4, :fs4]
harp_arpeggios = [:g4, :b4, :d5, :g5, :b4, :d5, :g5, :b4]

# Define sections for better structure
define :current_section do |current_tick|
  case current_tick
  when 0..31
    :intro
  when 32..95
    :verse_a
  when 96..127
    :transition_ab
  when 128..159
    :verse_b
  when 160..191
    :climax
  when 192..239
    :outro
  else
    :outro
  end
end

# Initialize effects and synths
with_fx :reverb, room: 0.8, damp: 0.5, mix: 0.4 do
  with_fx :lpf, cutoff: 90 do
    # Environmental sounds - wind and birds
    live_loop :nature_sounds do
      current_sec = current_section(tick)
      if [:intro, :transition_ab].include?(current_sec)
        sample :ambi_soft_buzz, amp: 0.1, rate: 0.3, pan: rrand(-0.3, 0.3)
        sleep 8
        if one_in(3)
          sample :ambi_glass_rub, amp: 0.05, rate: 2, pan: rrand(-0.5, 0.5)
        end
      else
        sleep 8
      end
    end

    # Wind chimes / glass celesta
    live_loop :wind_chimes do
      with_fx :lpf, cutoff: 95 do
        sleep 8
        current_sec = current_section(tick)
        if tick % 4 == 0
          amp_level = case current_sec
                     when :climax then 0.15
                     when :outro then 0.05
                     else 0.1
                     end
          play_chord chord(:g5, :maj7), amp: amp_level, attack: 0.5, release: 3, pan: rrand(-0.2, 0.2)
        end
        sleep 8
      end
    end

    # Piano part with improved rhythm and dynamics
    live_loop :piano do
      use_synth :piano
      current_sec = current_section(tick)
      current_chords = current_sec == :verse_b ? chord_progression_b : chord_progression_a
      
      # Intro: sparse arpeggios
      if current_sec == :intro
        play_pattern_timed [:g3, :b3, :d4, :g4, :b3, :d4, :g4], [0.4, 0.4, 0.4, 0.8, 0.4, 0.4, 0.8], amp: 0.6
      else
        # Main accompaniment with rhythmic variation
        4.times do |i|
          current_chord = current_chords[i]
          chord_amp = case current_sec
                     when :climax then 0.6
                     when :outro then 0.2
                     else 0.4
                     end
          
          play_chord current_chord, amp: chord_amp, release: 2
          
          # More varied rhythmic patterns
          case i
          when 0
            sleep 2
          when 1
            sleep 1.5
            play current_chord[0] + 12, amp: chord_amp * 0.5, release: 0.5
            sleep 0.5
          when 2
            play_pattern_timed [current_chord[1], current_chord[2], current_chord[0]], [0.66, 0.66, 0.68], amp: chord_amp * 0.75
            sleep 2
          else
            sleep 2
          end
        end
      end
    end

    # Cello melody with dynamic variation
    live_loop :cello do
      use_synth :hollow
      sleep 8  # Wait for intro
      
      current_sec = current_section(tick)
      current_melody = current_sec == :verse_b ? melody_notes_b : melody_notes_a
      
      with_fx :reverb, room: 0.6, mix: 0.3 do
        current_melody.each_with_index do |note, i|
          # Vary amplitude for expression
          dynamic_amp = 0.3 + (Math.sin(i * 0.5) * 0.1)
          dynamic_amp *= case current_sec
                        when :climax then 1.2
                        when :outro then 0.6
                        else 1.0
                        end
          play note, amp: dynamic_amp, attack: 0.1, release: 1.2, pan: -0.2
          sleep 0.8
        end
      end
    end

    # String section pad with improved dynamics
    live_loop :strings do
      use_synth :dsaw
      sleep 8  # Enter after intro
      
      current_sec = current_section(tick)
      current_chords = current_sec == :verse_b ? chord_progression_b : chord_progression_a
      
      with_fx :lpf, cutoff: 80 do
        4.times do |i|
          current_chord = current_chords[i]
          string_amp = case current_sec
                      when :climax then 0.4
                      when :outro then 0.1
                      else 0.2
                      end
          play_chord current_chord, amp: string_amp, attack: 1, release: 3, pan: 0.1
          sleep 4
        end
      end
    end

    # Harp arpeggios with improved structure
    live_loop :harp do
      use_synth :pluck
      sleep 8  # Enter in transition section
      
      with_fx :lpf, cutoff: 85 do
        current_sec = current_section(tick)
        if [:transition_ab, :verse_b, :climax].include?(current_sec)
          harp_amp = case current_sec
                    when :climax then 0.4
                    when :outro then 0.2
                    else 0.3
                    end
          harp_arpeggios.each do |note|
            play note, amp: harp_amp, release: 1.5, pan: 0.3
            sleep 0.5
          end
        else  # Final section
          sleep 8
          play_pattern_timed [:g4, :b4, :d5, :g5], [0.6, 0.6, 0.6, 1.2], amp: 0.4
        end
      end
    end

    # Bass foundation for better frequency balance
    live_loop :bass do
      use_synth :fm
      sleep 8  # Enter after intro and first melody section
      
      current_sec = current_section(tick)
      current_chords = current_sec == :verse_b ? chord_progression_b : chord_progression_a
      
      with_fx :lpf, cutoff: 70 do
        4.times do |i|
          chord_root = current_chords[i][0] - 12  # Play root note one octave lower
          bass_amp = case current_sec
                    when :climax then 0.4
                    when :outro then 0.15
                    else 0.3
                    end
          play chord_root, amp: bass_amp, release: 3, attack: 0.5
          sleep 4
        end
      end
    end

    # Subtle percussion for rhythmic interest
    live_loop :subtle_percussion do
      sleep 8  # Enter after intro
      current_sec = current_section(tick)
      if [:verse_a, :verse_b, :climax].include?(current_sec) && tick % 8 == 0
        perc_amp = case current_sec
                  when :climax then 0.15
                  else 0.1
                  end
        sample :drum_tom_lo_soft, amp: perc_amp, rate: 0.8
      end
      sleep 1
    end

    # Transition effects for better section changes
    live_loop :transitions do
      transition_points = [32, 96, 160]  # Section changes
      
      if transition_points.include?(tick)
        # Rising sweep effect
        with_fx :lpf, cutoff: 60 do
          with_fx :reverb, room: 0.9 do
            use_synth :sine
            play :g6, amp: 0.1, attack: 1, release: 2, pan: 0
            sleep 2
          end
        end
      end
      sleep 4
    end

    # Melodic embellishments for added interest
    live_loop :melodic_embellishments do
      sleep 8
      current_sec = current_section(tick)
      if [:verse_b, :climax].include?(current_sec) && one_in(4)
        use_synth :blade
        embellish_amp = case current_sec
                       when :climax then 0.3
                       else 0.2
                       end
        play_pattern_timed [:g5, :a5, :b5, :c6], [0.25, 0.25, 0.25, 0.25], amp: embellish_amp, release: 0.3
      end
      sleep 8
    end
  end
end

# Improved gradual fade-out
live_loop :fade_controller do
  sleep 8  # Start fade 16 beats before end
  16.times do |i|
    control all, amp: 1.0 - (i * 0.0625)  # Gradual fade
    sleep 1
  end
  stop
end