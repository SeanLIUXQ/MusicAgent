# Light Pop with Acoustic Folk elements - IMPROVED VERSION
# Inspired by "Summer" from Kikujiro, with beach holiday vibes

use_bpm 112

# Define musical elements with variations
main_key = :c4

# Enhanced chord progressions with more harmonic interest
chord_progression_a = [
  chord(:c4, :maj9), 
  chord(:g4, :maj9), 
  chord(:a4, :m7),    # Minor variation for color
  chord(:f4, :maj9)
]

chord_progression_b = [
  chord(:f4, :maj9),
  chord(:c4, :maj7),  # Simpler voicing for contrast
  chord(:g4, :maj9),
  chord(:a4, :m9)     # Extended harmony
]

# Whistle melody variations
whistle_variations = [
  [:c5, :d5, :e5, :g5, :a5, :g5, :e5, :d5],  # Original
  [:c5, :e5, :g5, :a5, :c6, :a5, :g5, :e5],  # Higher range
  [:g4, :a4, :c5, :d5, :e5, :d5, :c5, :a4],  # Lower range
  [:c5, :d5, :g5, :a5, :g5, :e5, :d5, :c5]   # Different contour
]

# Enhanced guitar arpeggio patterns with variations
guitar_arpeggios = [
  [:c4, :e4, :g4, :b4, :c5],  # Cmaj9 with extension
  [:g3, :b3, :d4, :f4, :a4],  # Gmaj9 with 9th
  [:a3, :c4, :e4, :g4, :b4],  # Am9 with extension  
  [:f3, :a3, :c4, :e4, :g4]   # Fmaj9 with 9th
]

# Define instrument patterns with rhythmic variations
ukulele_strum_variations = [
  [:c4, :e4, :g4, :b4, :c5, :b4, :g4, :e4],
  [:c4, :g4, :c5, :e5, :g5, :e5, :c5, :g4],
  [:e4, :g4, :b4, :c5, :e5, :c5, :b4, :g4]
]

bass_walking_variations = [
  [:c2, :e2, :g2, :b2, :c3, :b2, :g2, :e2],
  [:c2, :g2, :c3, :e3, :g3, :e3, :c3, :g2],
  [:g1, :b1, :d2, :f2, :g2, :f2, :d2, :b1]
]

marimba_variations = [
  [:c5, :e5, :g5, :b5, :c6, :b5, :g5, :e5],
  [:c5, :g5, :c6, :e6, :g6, :e6, :c6, :g5],
  [:e5, :g5, :b5, :c6, :e6, :c6, :b5, :g5]
]

# Introduction (0:00-0:12)
live_loop :intro_ukulele do
  use_synth :pluck
  with_fx :reverb, mix: 0.3 do
    4.times do |i|
      variation = ukulele_strum_variations[i % ukulele_strum_variations.length]
      # Dynamic shaping - start softer, build up
      current_amp = 0.6 + (i * 0.1)
      play_pattern_timed variation, [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25], amp: current_amp
    end
  end
  stop
end

live_loop :intro_whistle do
  use_synth :beep
  with_fx :echo, decay: 2 do
    sleep 2
    variation = whistle_variations[0]
    play_pattern_timed variation, [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], amp: 0.8
  end
  stop
end

live_loop :intro_percussion do
  sleep 4
  with_fx :level, amp: 0.5 do
    8.times do |i|
      # Vary the snap sound slightly
      sample :perc_snap, rate: [0.7, 0.8, 0.9].choose, amp: 0.4 - (i * 0.05)
      sleep 0.5
    end
  end
  stop
end

# Pre-chorus transition (0:28-0:36)
live_loop :pre_chorus_build do
  sleep 28  # Start 4 beats before chorus
  use_synth :hollow
  with_fx :reverb, mix: 0.6 do
    # Rising arpeggio to build tension
    play_pattern_timed [:c4, :e4, :g4, :b4, :c5, :e5, :g5, :b5], [0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125, 0.125], amp: 0.4
  end
  stop
end

# Verse A Section (0:12-0:36)
live_loop :verse_guitar do
  sleep 12
  use_synth :pluck
  with_fx :reverb, room: 0.7 do
    4.times do |i|
      # Crescendo through the verse
      current_amp = 0.6 + (i * 0.1)
      chord_current = chord_progression_a[i % 4]
      play_chord chord_current, amp: current_amp
      sleep 1.5
      # Guitar melody response with variation
      play_pattern_timed guitar_arpeggios[i % 4], [0.25, 0.25, 0.25, 0.25, 0.25], amp: current_amp * 0.8
      sleep 0.25  # Slightly shorter rest for better flow
    end
  end
  stop
end

live_loop :verse_marimba do
  sleep 12
  use_synth :marimba
  with_fx :lpf, cutoff: 90 do
    4.times do |i|
      variation = marimba_variations[i % marimba_variations.length]
      play_pattern_timed variation, [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25], amp: 0.5 + (i * 0.1)
    end
  end
  stop
end

live_loop :verse_bass do
  sleep 12
  use_synth :fm
  with_fx :distortion, distort: 0.1 do
    8.times do |i|
      variation = bass_walking_variations[i % 2]
      # Walking bass with syncopation and dynamic variation
      if i % 2 == 0
        play variation[i % 8], amp: 0.6 + (i * 0.05), release: 0.8
      else
        play variation[i % 8], amp: 0.4 + (i * 0.03), release: 0.4
      end
      sleep 0.5
    end
  end
  stop
end

# Chorus impact
live_loop :chorus_impact do
  sleep 36
  sample :drum_cymbal_open, amp: 0.3, attack: 0.02, release: 0.5
  stop
end

# Chorus Section (0:36-1:00)
live_loop :chorus_whistle do
  sleep 36
  use_synth :beep
  with_fx :echo, phase: 0.75 do
    3.times do |i|
      variation = whistle_variations[i % whistle_variations.length]
      # Build intensity through chorus
      current_amp = 1.0 + (i * 0.1)
      play_pattern_timed variation, [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25], amp: current_amp
    end
  end
  stop
end

live_loop :chorus_strings do
  sleep 36
  use_synth :hollow
  with_fx :reverb, mix: 0.4 do
    6.times do |i|
      if i % 2 == 0
        play chord_progression_b[i % 4], amp: 0.3 + (i * 0.05), release: 0.3 + (i * 0.1)
      end
      sleep 1
    end
  end
  stop
end

live_loop :chorus_bells do
  sleep 36
  use_synth :pretty_bell
  6.times do |i|
    play chord_progression_b[i % 4], amp: 0.2 + (i * 0.03), release: 0.5 + (i * 0.1)
    sleep 1
  end
  stop
end

live_loop :chorus_waves do
  sleep 36
  with_fx :level, amp: 0.2 do
    sample :ambi_soft_buzz, rate: 0.3, attack: 1, release: 8
  end
  stop
end

# Interlude (1:00-1:12)
live_loop :interlude_marimba do
  sleep 60
  use_synth :marimba
  # Transition to G major with dynamic shaping
  play_chord chord(:g4, :maj9), amp: 0.8
  sleep 1
  play_pattern_timed [:g4, :b4, :d5, :f5, :g5, :f5, :d5, :b4], [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25], amp: 0.6
  sleep 1
  stop
end

live_loop :interlude_shaker do
  sleep 60
  with_fx :level, amp: 0.4 do
    12.times do |i|
      # Vary the shaker sound
      sample :perc_swash, rate: [1.3, 1.5, 1.7].choose, amp: 0.3 + (i * 0.02)
      sleep 0.25
    end
  end
  stop
end

live_loop :transition_windchime do
  sleep 60
  sample :elec_twang, rate: 0.5, amp: 0.3
  stop
end

# Verse B Section (1:12-1:36)
live_loop :verse_b_piano do
  sleep 72
  use_synth :piano
  with_fx :reverb, room: 0.5 do
    4.times do |i|
      play_chord chord_progression_a[i % 4], amp: 0.5 + (i * 0.1), release: 1.5
      sleep 2
    end
  end
  stop
end

live_loop :verse_b_guitar_harmonics do
  sleep 72
  use_synth :pluck
  with_fx :echo, decay: 1 do
    8.times do |i|
      # More varied harmonic selection
      harmonic_note = guitar_arpeggios[i % 4][[1, 2, 3].choose]
      play harmonic_note, amp: 0.3 + (i * 0.02), release: 2
      sleep 1
    end
  end
  stop
end

# Bridge Section (1:36-1:48) - NEW
live_loop :bridge_pads do
  sleep 96
  use_synth :dark_ambience
  with_fx :reverb, room: 0.8 do
    # Bridge chords for contrast
    bridge_chords = [chord(:d4, :m9), chord(:g4, :maj7), chord(:e4, :m7), chord(:a4, :m9)]
    3.times do |i|
      play_chord bridge_chords[i % 4], amp: 0.4, release: 3
      sleep 3
    end
  end
  stop
end

live_loop :bridge_melody do
  sleep 96
  use_synth :sine
  with_fx :echo, decay: 2 do
    # Simple bridge melody
    play_pattern_timed [:d5, :f5, :a5, :g5, :e5, :c5, :d5], [0.75, 0.75, 1.0, 0.5, 0.75, 0.75, 1.5], amp: 0.6
  end
  stop
end

# Outro (1:48-2:00) - IMPROVED
live_loop :outro_fade do
  sleep 108
  use_synth :beep
  
  # More gradual, musical outro
  with_fx :level, amp: 1.0 do
    play_pattern_timed whistle_variations[0][0..3], [0.5, 0.5, 0.5, 0.5]
  end
  
  with_fx :level, amp: 0.7 do
    play_pattern_timed whistle_variations[0][2..5], [0.5, 0.5, 0.5, 0.5]
  end
  
  with_fx :level, amp: 0.4 do
    play_pattern_timed whistle_variations[0][4..7], [0.5, 0.5, 0.5, 0.5]
  end
  
  with_fx :level, amp: 0.2 do
    play whistle_variations[0][0], release: 4
  end
  
  stop
end

# Improved main percussion with variation
live_loop :main_percussion do
  # Add slight timing variations for human feel
  timing_variation = [0.95, 1.0, 1.05, 1.0].choose * 0.25
  
  sample :drum_tom_hi_soft, amp: 0.3, rate: [0.9, 1.0, 1.1].choose
  sleep timing_variation * 4
  
  sample :perc_snap, amp: 0.2
  sleep timing_variation * 4
  
  sample :drum_tom_hi_soft, amp: 0.3, rate: [0.9, 1.0, 1.1].choose
  sleep timing_variation * 4
  
  sample :perc_snap, amp: 0.2
  sleep timing_variation * 4
end

# Enhanced conga pattern with variation
live_loop :conga_rhythm do
  sample :drum_tom_lo_soft, amp: 0.4, rate: [0.95, 1.0, 1.05].choose
  sleep 0.5
  sample :drum_snare_soft, amp: 0.3, rate: [0.9, 1.0, 1.1].choose
  sleep 0.5
  sample :drum_tom_lo_soft, amp: 0.4, rate: [0.95, 1.0, 1.05].choose
  sleep 1
  sample :drum_snare_soft, amp: 0.3, rate: [0.9, 1.0, 1.1].choose
  sleep 0.5
  sample :drum_tom_lo_soft, amp: 0.4, rate: [0.95, 1.0, 1.05].choose
  sleep 0.5
end