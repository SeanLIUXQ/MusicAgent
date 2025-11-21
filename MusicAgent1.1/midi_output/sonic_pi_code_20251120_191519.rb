use_bpm 100

# Instrument definitions
erhu_synth = :hollow
pipa_synth = :pluck
dizi_synth = :fm
yangqin_synth = :piano
guzheng_synth = :pluck
piano_synth = :piano
bass_synth = :tb303
trumpet_synth = :beep
atmosphere_synth = :hollow

# Melodic content with variations
pentatonic_scale = (scale :c4, :major_pentatonic, num_octaves: 2)
blues_notes = (scale :c4, :minor_pentatonic) + [:ds4]

# Melodic variations
erhu_melody_variations = [
  [:c5, :e5, :g5, :e5, :c5, :a4, :g4, :e4],  # Original
  [:c5, :d5, :e5, :g5, :a5, :g5, :e5, :d5],  # Ascending
  [:g5, :e5, :d5, :c5, :a4, :g4, :e4, :c4],  # Descending
  [:c5, :r, :g5, :r, :e5, :a4, :g4, :e4]     # With rests
]

pipa_melody_variations = [
  [:c5, :e5, :g5, :a5, :g5, :e5, :c5, :a4],
  [:e5, :g5, :a5, :c6, :a5, :g5, :e5, :c5],
  [:c5, :r, :g5, :a5, :r, :e5, :c5, :a4],
  [:a4, :c5, :e5, :g5, :a5, :g5, :e5, :c5]
]

dizi_improvisations = [
  [:g5, :a5, :c6, :a5, :g5, :e5, :d5, :c5, :a4, :g4],
  [:c5, :e5, :g5, :a5, :c6, :a5, :g5, :e5, :d5, :c5],
  [:g5, :r, :c6, :a5, :g5, :e5, :r, :c5, :a4, :g4],
  [:a5, :c6, :d6, :c6, :a5, :g5, :e5, :d5, :c5, :a4]
]

# Rhythmic variations
rhythmic_patterns = [
  [0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5],  # Original
  [0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5],  # More active
  [0.75, 0.25, 0.5, 0.5, 0.75, 0.25, 0.5, 0.5],  # Syncopated
  [1, 0.5, 0.25, 0.25, 1, 0.5, 0.25, 0.25]       # Long-short
]

# Harmonic progressions with development
harmonic_development = [
  # Section A - Simple
  [(chord :c4, :maj7), (chord :g4, '7sus4'), (chord :f4, :maj7), (chord :e4, '7#9')],
  
  # Section B - More complex
  [(chord :c4, '9'), (chord :g4, '7sus4'), (chord :a4, :m7), (chord :f4, 'maj9')],
  
  # Section A' - Return with variation
  [(chord :c4, 'maj7#11'), (chord :g4, '13'), (chord :f4, 'maj9'), (chord :e4, '7#9b13')]
]

transition_progression = [
  (chord :a3, :m7),
  (chord :d3, :m7),
  (chord :g3, '7'),
  (chord :c4, :maj7)
]

# Bass lines
walking_bass_pattern = [:c2, :e2, :g2, :b2, :c3, :b2, :g2, :e2]
stride_bass_pattern = [:c2, :g2, :c3, :g2]

# Drum patterns
brush_drum_pattern = [
  [:drum_cymbal_soft, 0.5],
  [:drum_snare_soft, 0.25],
  [:drum_cymbal_soft, 0.5],
  [:drum_snare_soft, 0.25]
]

swing_drum_pattern = [
  [:drum_bass_hard, 1],
  [:drum_snare_soft, 0.5],
  [:drum_cymbal_open, 0.25],
  [:drum_snare_soft, 0.5]
]

# Section marker for proper synchronization
live_loop :section_marker do
  cue :intro
  sleep 8  # Shorter intro for better pacing
  cue :section_a
  sleep 8
  cue :section_b_approaching
  sleep 4
  cue :section_b
  sleep 8
  cue :interlude
  sleep 8
  cue :section_a_prime
  sleep 8
  cue :finale_approaching
  sleep 4
  cue :finale
  sleep 8
  cue :end
end

# Tempo transition for smooth change
live_loop :tempo_transition do
  sync :section_b_approaching
  current_bpm_val = 100
  target_bpm_val = 130
  steps_val = 8
  
  steps_val.times do
    current_bpm_val += (target_bpm_val - 100) / steps_val.to_f
    use_bpm current_bpm_val
    sleep 0.5
  end
end

# Introduction (0:00-0:08) - Shorter for better pacing
live_loop :intro_vinyl do
  sync :intro
  sample :vinyl_hiss, amp: 0.3, rate: 0.8
  sleep 8
end

live_loop :intro_pipa do
  sync :intro
  use_synth pipa_synth
  with_fx :reverb, room: 0.3 do
    with_fx :lpf, cutoff: 1200 do  # Frequency management
      play_pattern_timed pipa_melody_variations[0], rhythmic_patterns[0]
    end
  end
  sleep 8
end

live_loop :intro_piano do
  sync :intro
  use_synth piano_synth
  with_fx :lpf, cutoff: 90 do
    play_chord harmonic_development[0][0], amp: 0.4, release: 2
    sleep 4
    play_chord harmonic_development[0][1], amp: 0.4, release: 2
    sleep 4
  end
end

# Section A (0:08-0:48)
live_loop :section_a_erhu do
  sync :section_a
  use_synth erhu_synth
  with_fx :reverb, room: 0.5, mix: 0.3 do
    with_fx :lpf, cutoff: 1200 do  # High frequency range
      with_fx :slicer, phase: 0.25 do
        melody_var = erhu_melody_variations.tick
        rhythm_var = rhythmic_patterns.choose
        play_pattern_timed melody_var, rhythm_var
      end
    end
  end
  sleep 8
end

live_loop :evolving_bass do
  sync :section_a
  use_synth bass_synth
  with_fx :lpf, cutoff: 90 do
    with_fx :distortion, distort: 0.1 do
      harmonic_development[0].each do |current_chord|
        root_note = current_chord[0] - 12  # Play bass note one octave lower
        play root_note, amp: 0.6, release: 1.5
        sleep 1.5
        # Add passing tones for interest
        play root_note + 2, amp: 0.4, release: 0.5 if one_in(2)
        sleep 0.5
        play root_note + 4, amp: 0.4, release: 0.5
        sleep 0.5
        play root_note + 7, amp: 0.4, release: 0.5
        sleep 0.5
      end
    end
  end
end

live_loop :section_a_trumpet do
  sync :section_a
  sleep 8  # Staggered entry
  
  use_synth trumpet_synth
  with_fx :reverb, room: 0.4 do
    with_fx :lpf, cutoff: 1000 do  # Mid frequency range
      with_fx :distortion, distort: 0.1 do
        play_pattern_timed erhu_melody_variations[1], rhythmic_patterns[1]
      end
    end
  end
  sleep 8
end

live_loop :texture_pad do
  sync :section_a
  sleep 8  # Wait before entering for textural development
  
  use_synth :hollow
  with_fx :reverb, room: 0.8 do
    with_fx :lpf, cutoff: 80 do
      play_chord (chord :c3, :maj7), amp: 0.2, attack: 4, release: 8
      sleep 8
    end
  end
end

# Section B (0:52-1:32) - Swing section
live_loop :section_b_dizi do
  sync :section_b
  use_synth dizi_synth
  with_fx :reverb, room: 0.6 do
    with_fx :lpf, cutoff: 1500 do  # High frequency range
      with_fx :vibrato, depth: 0.3, rate: 6 do
        improv_var = dizi_improvisations.tick
        play_pattern_timed improv_var, rhythmic_patterns.choose
      end
    end
  end
  sleep 4
end

live_loop :section_b_drums do
  sync :section_b
  with_fx :level, amp: 0.6 do
    8.times do
      sample swing_drum_pattern[0][0], amp: swing_drum_pattern[0][1]
      sleep 1
      sample swing_drum_pattern[1][0], amp: swing_drum_pattern[1][1]
      sleep 0.5
      sample swing_drum_pattern[2][0], amp: swing_drum_pattern[2][1]
      sleep 0.25
      sample swing_drum_pattern[3][0], amp: swing_drum_pattern[3][1]
      sleep 0.5
    end
  end
end

live_loop :section_b_bass do
  sync :section_b
  use_synth bass_synth
  with_fx :lpf, cutoff: 100 do
    harmonic_development[1].each do |current_chord|
      root_note = current_chord[0] - 12
      play root_note, amp: 0.5, release: 1, cutoff: 80
      sleep 2
      # Walking bass variation
      play root_note + 7, amp: 0.3, release: 0.5, cutoff: 90
      sleep 1
      play root_note + 12, amp: 0.3, release: 0.5, cutoff: 90
      sleep 1
    end
  end
end

# Interlude (1:32-1:48)
live_loop :interlude_yangqin do
  sync :interlude
  use_synth yangqin_synth
  with_fx :reverb, room: 0.4 do
    with_fx :lpf, cutoff: 800 do  # Mid frequency range
      play_pattern_timed pentatonic_scale.shuffle.take(8), [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25]
    end
  end
  sleep 4
end

live_loop :interlude_piano do
  sync :interlude
  use_synth piano_synth
  with_fx :lpf, cutoff: 80 do
    play_chord transition_progression[0], amp: 0.5, release: 1
    sleep 2
    play_chord transition_progression[1], amp: 0.5, release: 1
    sleep 2
    play_chord transition_progression[2], amp: 0.5, release: 1
    sleep 2
    play_chord transition_progression[3], amp: 0.5, release: 1
    sleep 2
  end
end

# Section A' (1:48-2:28)
live_loop :section_a_prime_erhu do
  sync :section_a_prime
  use_bpm 100  # Return to original tempo
  
  use_synth erhu_synth
  with_fx :reverb, room: 0.5, mix: 0.3 do
    with_fx :lpf, cutoff: 1200 do
      with_fx :slicer, phase: 0.25 do
        melody_var = erhu_melody_variations.choose
        rhythm_var = rhythmic_patterns.choose
        play_pattern_timed melody_var, rhythm_var
      end
    end
  end
  sleep 8
end

live_loop :section_a_prime_atmosphere do
  sync :section_a_prime
  use_synth atmosphere_synth
  with_fx :lpf, cutoff: 60 do
    with_fx :echo, phase: 0.75, decay: 4 do
      play_chord harmonic_development[2][0], amp: 0.2, attack: 2, release: 6
      sleep 8
      play_chord harmonic_development[2][1], amp: 0.2, attack: 2, release: 6
      sleep 8
    end
  end
end

# Finale (2:32-2:52)
live_loop :finale_pipa do
  sync :finale
  use_synth pipa_synth
  with_fx :reverb, room: 0.8 do
    with_fx :lpf, cutoff: 1000 do
      # Single pipa notes fading out with dynamic variation
      play :c5, amp: 0.6, release: 2
      sleep 2
      play :g4, amp: 0.4, release: 2
      sleep 2
      play :e4, amp: 0.2, release: 2
      sleep 2
    end
  end
end

live_loop :finale_piano do
  sync :finale
  use_synth piano_synth
  with_fx :reverb, room: 0.9, damp: 1 do
    # Piano harmonics fading out
    play_chord (chord :c6, :maj7), amp: 0.3, attack: 0.5, release: 4
    sleep 4
    play_chord (chord :g5, '7sus4'), amp: 0.2, attack: 0.5, release: 3
    sleep 3
    play :c5, amp: 0.1, attack: 0.5, release: 2
    sleep 2
  end
end

live_loop :finale_ship_horn do
  sync :finale
  sleep 8  # Wait for most of finale
  
  # Ship horn sample (simulated with synth)
  use_synth :hollow
  with_fx :pitch_shift, pitch: -4 do
    play :c3, amp: 0.5, attack: 0.1, release: 2, cutoff: 60
    sleep 2
  end
end

# Fade out everything gracefully
live_loop :master_fade do
  sync :finale_approaching
  control_amp = 1.0
  16.times do
    control_amp -= 0.0625
    set_mixer_amp! control_amp
    sleep 0.25
  end
end