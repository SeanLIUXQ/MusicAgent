use_bpm 74

# Define pentatonic scale in G major
pentatonic_scale = (scale :g4, :major_pentatonic, num_octaves: 2)

# Melody phrases - structured in 4-bar phrases
melody_phrases = [
  # First phrase (8 bars total)
  [:g4, :a4, :b4, :d5, :b4, :a4, :g4, :r] + [:g4, :a4, :b4, :d5, :e5, :d5, :b4, :r],
  # Second phrase
  [:b4, :d5, :e5, :d5, :b4, :a4, :g4, :r] + [:a4, :g4, :e4, :d4, :e4, :g4, :a4, :r],
  # Third phrase (development)
  [:g4, :b4, :d5, :e5, :g5, :e5, :d5, :b4] + [:a4, :b4, :d5, :e5, :d5, :b4, :a4, :g4],
  # Fourth phrase (climax)
  [:b4, :d5, :e5, :g5, :e5, :d5, :b4, :a4] + [:g4, :a4, :b4, :d5, :b4, :a4, :g4, :r]
]

# Chord progression
chord_progression = [
  [:g3, :b3, :d4], [:c4, :e4, :g4], [:d4, :fs4, :a4, :c5], [:g3, :b3, :d4],  # G-C-D7-G
  [:g3, :b3, :d4], [:e3, :g3, :b3], [:c4, :e4, :g4], [:d4, :fs4, :a4]        # G-Em-C-D
]

# Rhythm patterns
erhu_rhythm = [1, 0.5, 0.5, 2, 1, 0.5, 0.5, 2]
dizi_rhythm = [1.5, 0.5, 1, 1, 0.75, 0.25, 1, 1]
guzheng_arpeggio = [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]

# Section management
sections = [:intro, :verse, :chorus, :bridge, :outro]
current_section = :intro
section_duration = 32  # 32 beats per section

live_loop :section_manager do
  sleep section_duration
  current_section = sections.rotate!.first
  puts "Section changed to: #{current_section}"
end

# Introduction section (first 8 bars)
live_loop :intro_pad do
  sync :section_manager
  if current_section == :intro
    use_synth :dark_ambience
    play :g3, amp: 0.2, attack: 4, release: 4, sustain: 4
    sleep 8
  else
    sleep 8
  end
end

live_loop :dizi_melody do
  sync :section_manager
  case current_section
  when :intro, :verse, :chorus, :bridge
    use_synth :blade
    with_fx :reverb, mix: 0.3 do
      melody_phrases.each_with_index do |phrase, phrase_idx|
        phrase.each_with_index do |note, idx|
          if note != :r
            # Vary amplitude and release based on phrase position and section
            amp_base = case current_section
                      when :intro then 0.6
                      when :verse then 0.7
                      when :chorus then 0.9
                      when :bridge then 0.8
                      else 0.7
                      end
            
            release_variation = dizi_rhythm[idx % 8] * (0.6 + (rand(0.2)))
            
            play note, amp: amp_base, release: release_variation
            sleep dizi_rhythm[idx % 8]
          else
            sleep dizi_rhythm[idx % 8]
          end
        end
      end
    end
  when :outro
    # Simplified melody for outro
    use_synth :blade
    with_fx :reverb, mix: 0.3 do
      melody_phrases[0].each_with_index do |note, idx|
        if note != :r
          play note, amp: 0.5 - (idx * 0.02), release: dizi_rhythm[idx % 8] * 0.6
          sleep dizi_rhythm[idx % 8]
        else
          sleep dizi_rhythm[idx % 8]
        end
      end
    end
  end
end

live_loop :erhu_countermelody do
  sync :section_manager
  case current_section
  when :verse, :chorus, :bridge
    use_synth :hollow
    with_fx :lpf, cutoff: 90 do
      16.times do |i|
        chord_idx = i % chord_progression.length
        current_chord = chord_progression[chord_idx]
        
        # Add passing tones and embellishments
        if i % 4 == 0
          # Play chord tone on strong beats
          play current_chord[1], amp: 0.6, release: erhu_rhythm[i % 8]
        else
          # Add melodic flourishes on weak beats
          embellished_note = pentatonic_scale.choose
          play embellished_note, amp: 0.4, release: erhu_rhythm[i % 8] * 0.7
        end
        
        sleep erhu_rhythm[i % 8]
      end
    end
  when :outro
    # Sparse countermelody in outro
    use_synth :hollow
    with_fx :lpf, cutoff: 90 do
      8.times do |i|
        if i % 2 == 0
          chord_idx = i % chord_progression.length
          current_chord = chord_progression[chord_idx]
          play current_chord[1], amp: 0.3, release: 1.5
        end
        sleep 2
      end
    end
  else
    sleep 8
  end
end

live_loop :guzheng_accompaniment do
  sync :section_manager
  case current_section
  when :intro
    # Sparse in intro
    use_synth :pluck
    8.times do |i|
      if i % 4 == 0
        chord_idx = i % chord_progression.length
        current_chord = chord_progression[chord_idx]
        play current_chord[0] - 12, amp: 0.3, release: 0.4
      end
      sleep 2
    end
  when :verse, :chorus, :bridge
    # Full activity in main sections
    use_synth :pluck
    32.times do |i|
      chord_idx = (i / 4) % chord_progression.length
      current_chord = chord_progression[chord_idx]
      current_chord.each do |note|
        play note - 12, amp: 0.4, release: 0.3
        sleep 0.25
      end
    end
  when :outro
    # Gradual simplification
    use_synth :pluck
    16.times do |i|
      if i % 2 == 0
        chord_idx = (i / 2) % chord_progression.length
        current_chord = chord_progression[chord_idx]
        play current_chord[0] - 12, amp: 0.3 - (i * 0.01), release: 0.5
      end
      sleep 1
    end
  end
end

live_loop :bass_support do
  sync :section_manager
  case current_section
  when :intro, :verse, :chorus, :bridge
    use_synth :fm
    16.times do |i|
      chord_idx = i % chord_progression.length
      root_note = chord_progression[chord_idx][0] - 24
      
      # Shorter release to prevent muddiness
      play root_note, amp: 0.3, release: 0.8, cutoff: 70
      
      # Vary rhythm occasionally
      if i % 8 == 0
        sleep 1.5
        play root_note + 7, amp: 0.2, release: 0.5  # Add fifth for movement
        sleep 0.5
      else
        sleep 2
      end
    end
  when :outro
    # Fading bass in outro
    use_synth :fm
    8.times do |i|
      chord_idx = i % chord_progression.length
      root_note = chord_progression[chord_idx][0] - 24
      play root_note, amp: 0.2 - (i * 0.02), release: 0.6, cutoff: 60
      sleep 2
    end
  end
end

live_loop :percussion do
  sync :section_manager
  case current_section
  when :intro
    # Light percussion in intro
    16.times do
      sample :drum_tom_hi_soft, amp: 0.1, rate: 1.2 if (tick % 8) == 0
      sleep 0.5
    end
  when :verse
    # Moderate percussion in verse
    32.times do
      case tick % 16
      when 0, 8
        sample :drum_tom_lo_soft, amp: 0.2, rate: 0.9
      when 4, 12
        sample :drum_tom_mid_soft, amp: 0.15, rate: 1.1
      end
      
      # Add shaker/texture on off-beats
      if (tick % 2) == 1
        sample :perc_snap2, amp: 0.08, rate: 2
      end
      
      sleep 0.5
    end
  when :chorus, :bridge
    # Full percussion in chorus/bridge
    32.times do
      case tick % 16
      when 0, 8
        sample :drum_tom_lo_soft, amp: 0.25, rate: 0.9
      when 4, 12
        sample :drum_tom_mid_soft, amp: 0.2, rate: 1.1
      when 2, 6, 10, 14
        sample :drum_tom_hi_soft, amp: 0.15, rate: 1.2
      end
      
      # Add shaker/texture on off-beats
      if (tick % 2) == 1
        sample :perc_snap2, amp: 0.1, rate: 2
      end
      
      sleep 0.5
    end
  when :outro
    # Fading percussion in outro
    16.times do |i|
      if (tick % 8) == 0
        sample :drum_tom_hi_soft, amp: 0.1 - (i * 0.005), rate: 1.1
      end
      sleep 0.5
    end
  end
end

# Transitional effects
live_loop :transitions do
  sync :section_manager
  case current_section
  when :chorus
    # Build-up to chorus
    with_fx :lpf, cutoff: 60 do
      with_fx :reverb, room: 0.8 do
        play_chord chord(:g4, :major), amp: 0.3, release: 2, attack: 1
      end
    end
  when :outro
    # Fade out all instruments gradually
    8.times do |i|
      control :dizi_melody, amp: 0.7 - (i * 0.0875) if get[:dizi_melody]
      control :erhu_countermelody, amp: 0.5 - (i * 0.0625) if get[:erhu_countermelody]
      control :guzheng_accompaniment, amp: 0.4 - (i * 0.05) if get[:guzheng_accompaniment]
      control :bass_support, amp: 0.3 - (i * 0.0375) if get[:bass_support]
      sleep 2
    end
  end
end