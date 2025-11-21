# Chinese Classical Music: "Er Quan Ying Yue" Style - IMPROVED VERSION
# G Pentatonic Minor with traditional Chinese instrumentation

use_bpm 68  # Adagio tempo for contemplative feel

# Define musical elements with safe variable names
main_scale = (scale :g3, :minor_pentatonic, num_octaves: 2)
secondary_notes = [:gb3, :a3, :eb4]  # Bian tones for emotional color
main_motif = [:d4, :c4, :bb3, :g3]  # Descending "reflected moon" motif
hope_motif = [:g3, :c4, :g3, :bb3, :d4]  # Rising intervals for hope

# Enhanced melodic variations
developed_motifs = {
  main_variation_1: [:d4, :eb4, :d4, :c4, :bb3, :a3, :g3],
  main_variation_2: [:d4, :f4, :d4, :c4, :g3, :f3, :eb3],
  hope_development: [:g3, :c4, :eb4, :g3, :bb3, :d4, :f4],
  chromatic_exploration: [:g3, :a3, :bb3, :c4, :db4, :c4, :bb3]
}

# Expanded harmonic foundation
chord_progression = [
  [:g2, :d3],          # I
  [:c3, :g3, :bb3],    # IV
  [:f2, :c3, :eb3],    # bVII
  [:bb2, :d3, :f3],    # bIII
  [:g2, :d3, :f3]      # I with color
]

# Instrument settings
erhu_settings = {attack: 0.1, release: 1.5, amp: 0.8}
guqin_settings = {attack: 0.05, release: 0.8, amp: 0.4}
pipa_settings = {attack: 0.02, release: 0.3, amp: 0.5}
dizi_settings = {attack: 0.1, release: 1.2, amp: 0.6}
yangqin_settings = {attack: 0.01, release: 0.5, amp: 0.5}  # Increased amp

# Transition and expression functions
define :fade_in do |duration_val = 4|
  with_fx :level, amp: 0 do |ctrl|
    control ctrl, amp: 1, amp_slide: duration_val
  end
end

define :fade_out do |duration_val = 4|
  with_fx :level, amp: 1 do |ctrl|
    control ctrl, amp: 0, amp_slide: duration_val
  end
end

define :expressive_phrase do |notes_arr, timings_arr, base_settings|
  notes_arr.each_with_index do |note_val, idx|
    # Build intensity toward phrase middle
    intensity_val = idx < notes_arr.length / 2 ? idx * 0.1 : (notes_arr.length - idx) * 0.1
    play note_val, base_settings.merge(amp: base_settings[:amp] + intensity_val)
    sleep timings_arr[idx]
  end
end

define :play_chinese_note do |note_val, settings_hash|
  # Slight pitch bends for expressive quality
  use_synth_defaults portamento: 0.1, pitch_bend: 0.05
  play note_val, settings_hash
end

# Enhanced harmonic foundation
live_loop :harmonic_foundation, sync: :section_controller do
  case get[:current_section]
  when :intro
    play_chord [:g2, :d3], guqin_settings.merge(attack: 0.1, release: 6)
    sleep 8
    play_chord [:c3, :g3], guqin_settings.merge(attack: 0.1, release: 6)
    sleep 8
  when :expo_a
    play_chord [:g2, :d3], guqin_settings.merge(attack: 0.1, release: 4, amp: 0.5)
    sleep 6
    play_chord [:c3, :g3, :bb3], guqin_settings.merge(attack: 0.1, release: 4, amp: 0.5)
    sleep 6
  when :expo_b
    play_chord [:f2, :c3, :eb3], guqin_settings.merge(attack: 0.1, release: 3, amp: 0.6)
    sleep 4
    play_chord [:bb2, :d3, :f3], guqin_settings.merge(attack: 0.1, release: 3, amp: 0.6)
    sleep 4
  when :interlude
    play_chord [:g2, :c3, :f3], guqin_settings.merge(attack: 0.1, release: 5, amp: 0.4)
    sleep 6
    play_chord [:bb2, :d3, :g3], guqin_settings.merge(attack: 0.1, release: 5, amp: 0.4)
    sleep 6
  when :recap
    play_chord [:g2, :d3, :f3], guqin_settings.merge(attack: 0.1, release: 4, amp: 0.7)
    sleep 8
  when :coda
    play_chord [:g2, :d3], guqin_settings.merge(attack: 0.1, release: 8, amp: 0.3)
    sleep 8
  end
end

# Intro Section (0:00-0:40)
live_loop :intro_erhu, sync: :start do
  fade_in(8)
  use_synth :blade
  with_fx :reverb, mix: 0.4 do
    # Main motif with expressive articulation
    expressive_phrase(main_motif, [0.8, 0.7, 0.9, 1.2],
      erhu_settings.merge(portamento: 0.3, vibrato_rate: 6, vibrato_depth: 0.1))
    sleep 2
    # Ornamented variation
    play_pattern_timed [:d4, :eb4, :d4, :c4, :bb3], [0.4, 0.3, 0.5, 0.8, 1.0],
      erhu_settings.merge(portamento: 0.2)
  end
  sleep 8
end

# Exposition A Section (0:40-2:20)
live_loop :expo_a_erhu, sync: :intro_erhu do
  use_synth :blade
  with_fx :reverb, mix: 0.3 do
    # Developed primary theme with variation
    if tick % 2 == 0
      notes_seq = [:g3, :bb3, :c4, :d4, :f4, :d4, :c4, :bb3]
      timing_seq = [0.6, 0.5, 0.7, 0.8, 1.0, 0.4, 0.6, 0.9]
    else
      notes_seq = developed_motifs[:main_variation_1]
      timing_seq = [0.6, 0.3, 0.5, 0.7, 0.4, 0.6, 1.2]
    end
    play_pattern_timed notes_seq, timing_seq,
      erhu_settings.merge(portamento: 0.2, vibrato_rate: 5, amp: 0.9)
  end
  sleep 4
end

live_loop :expo_a_pipa, sync: :intro_erhu do
  use_synth :pluck
  # Ornamental flourishes with variation
  sleep 6
  if tick % 3 == 0
    play_pattern_timed [:g4, :bb4, :c5, :g4], [0.2, 0.3, 0.4, 0.3], pipa_settings
  else
    play_pattern_timed [:f4, :g4, :bb4, :c5], [0.15, 0.25, 0.35, 0.25], pipa_settings.merge(amp: 0.4)
  end
  sleep 8
end

live_loop :expo_a_dizi, sync: :intro_erhu do
  use_synth :sine
  # Call-and-response phrases with erhu
  sleep 2
  if tick % 2 == 0
    play_pattern_timed [:f4, :g4, :bb4], [0.8, 0.6, 1.2],
      dizi_settings.merge(portamento: 0.1, amp: 0.7)
  else
    play_pattern_timed [:c4, :eb4, :g4], [0.7, 0.8, 1.0],
      dizi_settings.merge(portamento: 0.15, amp: 0.6)
  end
  sleep 8
end

# Exposition B Section (2:20-3:50)
live_loop :expo_b_yangqin, sync: :expo_a_erhu do
  use_synth :pulse
  # Rhythmic pulse with dynamic variation
  with_fx :lpf, cutoff: 90 do
    4.times do |i|
      amp_val = yangqin_settings[:amp] + (i * 0.1)
      play_pattern_timed [:g3, :c4, :g3, :d4], [0.5, 0.5, 0.5, 1.5],
        yangqin_settings.merge(amp: amp_val)
    end
  end
  sleep 8
end

live_loop :expo_b_erhu, sync: :expo_a_erhu do
  use_synth :blade
  # Emotional peaks with hope motif development
  with_fx :reverb, mix: 0.4 do
    if tick % 2 == 0
      expressive_phrase(hope_motif, [0.7, 0.6, 0.5, 0.8, 1.4],
        erhu_settings.merge(portamento: 0.3, amp: 1.0))
    else
      expressive_phrase(developed_motifs[:hope_development], [0.6, 0.5, 0.7, 0.4, 0.6, 0.8, 1.2],
        erhu_settings.merge(portamento: 0.25, amp: 1.1))
    end
    sleep 1
    # Chromatic exploration with variation
    play_pattern_timed developed_motifs[:chromatic_exploration], [0.6, 0.4, 0.7, 0.5, 0.3, 0.4, 1.0],
      erhu_settings.merge(vibrato_depth: 0.12)
  end
  sleep 4
end

# Interlude Section (3:50-4:30)
live_loop :interlude_dizi, sync: :expo_b_erhu do
  fade_in(4)
  use_synth :sine
  # Ethereal duet phrases with microtonal expression
  with_fx :reverb, mix: 0.5 do
    play_chinese_note :c5, dizi_settings.merge(release: 1.5)
    sleep 1.0
    play_chinese_note :bb4, dizi_settings.merge(release: 1.3)
    sleep 0.8
    play_chinese_note :g4, dizi_settings.merge(release: 1.8)
    sleep 1.2
    play_chinese_note :f4, dizi_settings.merge(release: 2.0)
    sleep 1.5
  end
  fade_out(4)
  sleep 8
end

# Recapitulation A' Section (4:30-5:55)
live_loop :recap_erhu, sync: :interlude_dizi do
  use_synth :blade
  # Return to main theme with heightened expression and variation
  with_fx :reverb, mix: 0.3 do
    expressive_phrase(main_motif, [0.9, 0.8, 1.0, 1.5],
      erhu_settings.merge(portamento: 0.4, vibrato_depth: 0.15, amp: 1.1))
    sleep 0.5
    # Expanded variation with dynamic contrast
    if tick % 2 == 0
      expanded_pattern = [:d4, :f4, :d4, :c4, :bb3, :g3, :f3]
      timing_pattern = [0.5, 0.4, 0.6, 0.5, 0.8, 0.7, 1.2]
    else
      expanded_pattern = developed_motifs[:main_variation_2]
      timing_pattern = [0.6, 0.4, 0.5, 0.7, 0.8, 0.9, 1.4]
    end
    play_pattern_timed expanded_pattern, timing_pattern,
      erhu_settings.merge(amp: 1.0, vibrato_rate: 7)
  end
  sleep 6
end

# Coda Section (5:55-6:35)
live_loop :coda_erhu, sync: :recap_erhu do
  fade_out(20)
  use_synth :blade
  # Final statement of main motif with gradual decay
  with_fx :reverb, mix: 0.6 do
    play_pattern_timed main_motif, [1.2, 1.1, 1.3, 2.0],
      erhu_settings.merge(amp: 0.6, release: 2.0, portamento: 0.5)
  end
  sleep 8
end

# Traditional percussion for rhythmic interest
live_loop :qing, sync: :section_controller do
  current_sect = get[:current_section]
  if current_sect == :expo_b || current_sect == :recap
    sample :perc_bell, rate: 0.8, amp: 0.2, pan: -0.3
    sleep 2
  else
    sleep 1
  end
end

# Enhanced Section Controller with transitions
live_loop :section_controller do
  # Intro with fade in (40 seconds)
  cue :intro_erhu
  set :current_section, :intro
  sleep 8
  cue :transition_to_expo_a
  sleep 4
  
  # Exposition A with build (100 seconds)
  cue :expo_a_erhu
  set :current_section, :expo_a
  sleep 8
  cue :transition_to_expo_b
  sleep 4
  
  # Exposition B - emotional peak (90 seconds)
  cue :expo_b_erhu
  set :current_section, :expo_b
  sleep 8
  cue :transition_to_interlude
  sleep 4
  
  # Interlude - calm before recap (40 seconds)
  cue :interlude_dizi
  set :current_section, :interlude
  sleep 8
  cue :transition_to_recap
  sleep 4
  
  # Recapitulation with heightened intensity (85 seconds)
  cue :recap_erhu
  set :current_section, :recap
  sleep 8
  cue :transition_to_coda
  sleep 4
  
  # Coda with fade out (40 seconds)
  cue :coda_erhu
  set :current_section, :coda
  sleep 8
  cue :end
  sleep 4
end