# Chinese Folk Song - Traditional Style
# BPM: 76 (moderate slow pace)
use_bpm 76
set :sync, true

# Define pentatonic scale in C major (C D E G A)
pentatonic_scale = (scale :c, :major_pentatonic)

# Melody patterns - folk song inspired phrases
melody_phrases = [
  [:c4, :e4, :g4, :e4, :c4],           # Opening phrase
  [:d4, :g4, :a4, :g4, :e4],           # Ascending phrase
  [:c4, :a3, :g3, :a3, :c4],           # Descending phrase
  [:e4, :g4, :a4, :c5, :a4, :g4],      # Climax phrase
  [:g4, :e4, :d4, :c4]                 # Closing phrase
]

# Expanded chord progressions for harmonic variety
chord_progression = [
  [:c3, :g3, :c4],    # I chord (C)
  [:g3, :d4, :g4],    # V chord (G)
  [:a3, :e4, :a4],    # vi chord (relative minor)
  [:f3, :c4, :f4]     # IV chord (borrowed from major)
]

# Section progressions
verse_progression = [0, 1, 2, 3]      # I-V-vi-IV
chorus_progression = [0, 3, 1, 0]     # I-IV-V-I

# Rhythmic patterns for variety
rhythm_patterns = [
  [0.25, 0.25, 0.5, 1],      # Standard
  [0.125, 0.125, 0.25, 0.5], # Double-time
  [0.75, 0.25, 0.5, 0.5]     # Syncopated
]

# Metronome for synchronization
live_loop :metronome do
  cue :tick
  sleep 1
end

# Transition function for smooth section changes
define :transition_fill do |duration|
  with_fx :reverb, room: 0.8, amp: 0.7 do
    play_pattern_timed [:g4, :a4, :c5], [duration/3, duration/3, duration/3]
  end
end

# Bamboo flute (main melody)
live_loop :bamboo_flute, sync: :tick do
  use_synth :blade
  use_octave -1
  
  # 30-second sections for better timing
  current_section = (beat / 30).to_i % 6
  section_beat = beat % 30
  
  # Add transition 2 seconds before section end
  if section_beat == 28
    transition_fill(2)
  end
  
  case current_section
  when 0  # Intro (8 seconds)
    with_fx :level, amp: 0.8 do
      play_pattern_timed [:c4, :e4, :g4], [1, 1, 2]
    end
    sleep 4  # Total 8 seconds
    
  when 1  # Verse A (30 seconds)
    # First phrase with dynamic shaping
    with_fx :level, amp: 0.9 do
      play_pattern_timed melody_phrases[0], [0.5, 0.25, 0.5, 0.25, 0.5]
    end
    # Second phrase with crescendo
    with_fx :level, amp: 1.0 do
      play_pattern_timed melody_phrases[1], [0.25, 0.5, 0.25, 0.5, 0.5]
    end
    remaining_time = 30 - 6.5
    sleep remaining_time
    
  when 2  # Chorus B (30 seconds)
    with_fx :vowel, voice: 0.3 do
      # Descending phrase
      play_pattern_timed melody_phrases[2], [0.25, 0.25, 0.5, 0.25, 0.75]
      # Climax phrase with crescendo
      with_fx :level, amp: 1.2 do
        4.times do |i|
          with_swing 0.1, pulse: i do
            play melody_phrases[3][i], amp: 0.8 + (i * 0.1)
            sleep 0.25
          end
        end
        play melody_phrases[3][4], amp: 1.2
        sleep 0.25
        play melody_phrases[3][5], amp: 1.1
        sleep 0.5
      end
    end
    sleep 8 - 8.5
    
  when 3  # Interlude (20 seconds)
    with_fx :echo, phase: 0.75, decay: 4 do
      play_pattern_timed pentatonic_scale.shuffle.take(6), [0.5, 0.25, 0.25, 0.5, 0.5, 1]
    end
    sleep 8  # Total 20 seconds
    
  when 4  # Verse A' (30 seconds)
    # Variation with ornamentation and dynamics
    with_fx :level, amp: 1.1 do
      play_pattern_timed [:c4, :e4, :g4, :a4, :g4, :e4, :c4], [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5]
    end
    with_fx :level, amp: 1.0 do
      play_pattern_timed [:d4, :g4, :a4, :c5, :a4, :g4, :e4], [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.5]
    end
    sleep 8 - 5.5
    
  when 5  # Outro (20 seconds)
    with_fx :level, amp: 1.0 do
      play :c4, release: 4
    end
    sleep 6
    with_fx :level, amp: 0.8 do
      play :g3, release: 4
    end
    sleep 6
    with_fx :level, amp: 0.5 do
      play :c4, release: 4
    end
    sleep 8
  end
end

# Guzheng (Chinese zither - harmony and rhythm)
live_loop :guzheng, sync: :tick do
  use_synth :hollow
  use_octave -2
  
  current_section = (beat / 30).to_i % 6
  section_beat = beat % 30
  
  case current_section
  when 0  # Intro - solo introduction
    with_fx :level, amp: 0.8 do
      play_pattern_timed [:c3, :e3, :g3, :c4], [1, 1, 1, 2]
      play_pattern_timed [:g3, :b3, :d4, :g4], [1, 1, 1, 2]
    end
    
  when 1, 4  # Verses A and A'
    # Arpeggio patterns with verse progression
    4.times do |i|
      chord_idx = verse_progression[i % 4]
      with_fx :level, amp: 0.7 + (i * 0.05) do
        play_chord chord_progression[chord_idx], release: 0.5
      end
      sleep 1.5
      chord_idx = verse_progression[(i + 1) % 4]
      with_fx :level, amp: 0.7 + (i * 0.05) do
        play_chord chord_progression[chord_idx], release: 0.5
      end
      sleep 1.5
    end
    
  when 2  # Chorus B
    # More active accompaniment with chorus progression
    with_fx :reverb, room: 0.3 do
      4.times do |i|
        chord_idx = chorus_progression[i % 4]
        with_fx :level, amp: 0.8 + (i * 0.1) do
          play_pattern_timed chord_progression[chord_idx], [0.25, 0.25, 0.25]
        end
        sleep 0.25
      end
    end
    
  when 3  # Interlude
    # Improvisational section with dynamics
    with_fx :level, amp: 0.9 do
      play_pattern_timed pentatonic_scale.shuffle.take(8), [0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 0.5]
    end
    
  when 5  # Outro
    # Fading arpeggios with gradual diminuendo
    4.times do |i|
      with_fx :level, amp: 1.0 - (i * 0.2) do
        play_chord [:c3, :e3, :g3, :c4], release: 2
        sleep 2
      end
    end
  end
end

# Pipa (plucked string - rhythmic emphasis)
live_loop :pipa, sync: :tick do
  use_synth :pluck
  use_octave -1
  
  current_section = (beat / 30).to_i % 6
  
  # Only play in main sections, not intro/outro
  if [1, 2, 4].include?(current_section)
    # Use different rhythm patterns for variety
    current_rhythm = rhythm_patterns[current_section % 3]
    
    if current_section == 1 || current_section == 4  # Verses
      progression = verse_progression
    else  # Chorus
      progression = chorus_progression
    end
    
    # Plucked chord patterns with rhythmic variation
    2.times do |i|
      chord_idx = progression[i % progression.length]
      chord_notes = chord_progression[chord_idx]
      
      play chord_notes[0], amp: 0.8
      sleep current_rhythm[0]
      play chord_notes[1], amp: 0.6
      sleep current_rhythm[1]
      play chord_notes[2], amp: 0.7
      sleep current_rhythm[2]
    end
  else
    sleep 8
  end
end

# Erhu (secondary melody - emotional counterpoint)
live_loop :erhu, sync: :tick do
  use_synth :saw
  use_octave -1
  
  current_section = (beat / 30).to_i % 6
  
  # Only prominent in chorus and interlude
  case current_section
  when 2  # Chorus B
    with_fx :vibrato, depth: 0.1 do
      with_fx :level, amp: 0.9 do
        play_pattern_timed [:a3, :c4, :e4, :g4], [0.75, 0.75, 0.75, 0.75]
      end
      with_fx :level, amp: 0.8 do
        play_pattern_timed [:g4, :e4, :c4, :a3], [0.5, 0.5, 0.5, 0.5]
      end
    end
  when 3  # Interlude
    with_fx :level, amp: 0.7 do
      play_pattern_timed [:g3, :a3, :c4, :d4, :e4], [0.5, 0.25, 0.5, 0.25, 1]
    end
  else
    sleep 8
  end
end

# Percussion - wood block and bell accents
live_loop :percussion, sync: :tick do
  current_section = (beat / 30).to_i % 6
  
  if current_section != 0 && current_section != 5  # No percussion in intro/outro
    # Wood block on strong beats with dynamic variation
    if beat % 4 == 0
      amp_val = 0.3 + (Math.sin(beat * 0.1) * 0.1).abs
      sample :perc_bell, rate: 0.8, amp: amp_val
    end
    
    # Bell accents at phrase endings with variety
    if [3, 7, 11, 15].include?(beat % 16)
      sample :glitch_bass_g, rate: 2 + (current_section * 0.2), amp: 0.2, release: 0.1
    end
  end
  
  sleep 0.25
end

# Ambient sounds for intro and outro
live_loop :ambience, sync: :tick do
  current_section = (beat / 30).to_i % 6
  
  if current_section == 0 || current_section == 5
    # Gentle water-like sound with dynamic fade
    fade_amp = current_section == 0 ? 0.1 : 0.1 - ((beat % 30) * 0.003)
    with_fx :lpf, cutoff: 70 do
      sample :ambi_soft_buzz, rate: 0.3, amp: fade_amp, attack: 1, release: 1
    end
    sleep 4
  else
    sleep 8
  end
end