# Classic Progressive House Track - IMPROVED VERSION
use_bpm 124

# Define musical elements with variations
chord_progression = [:cm3, :ab3, :eb3, :gm3]
bass_patterns = [
  [:c2, :r, :r, :c2, :r, :r, :g2, :r, :ab1, :r, :r, :ab1, :r, :r, :eb2, :r], # Rhythmic variation
  [:c2, :c2, :c2, :c2, :ab1, :ab1, :ab1, :ab1, :eb2, :eb2, :eb2, :eb2, :g2, :g2, :g2, :g2]  # Original
]

melody_patterns = [
  [:c4, :eb4, :g4, :ab4, :g4, :eb4, :c4, :r, :ab3, :c4, :eb4, :f4, :eb4, :c4, :ab3, :r], # Verse
  [:c4, :g4, :ab4, :bb4, :c5, :bb4, :ab4, :g4, :eb4, :c4, :eb4, :g4, :f4, :eb4, :c4, :r]  # Chorus
]

pad_chords = [:cm4, :ab4, :eb4, :gm4]

# Drum patterns with variations
kick_patterns = [
  [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0], # Standard 4/4
  [1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0], # Variation for build-up
  [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0]  # Double-time fill
]

clap_patterns = [
  [0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1], # Standard
  [0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0]  # Sparse
]

hat_patterns = [
  [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1], # Straight
  [1, 0, 1, 1, 0, 1, 0, 1, 1, 0, 1, 1, 0, 1, 0, 1]  # Shuffled
]

# Initialize shared variables
set :current_section, :intro
set :current_kick_pattern, kick_patterns[0]
set :current_clap_pattern, clap_patterns[0]
set :current_hat_pattern, hat_patterns[0]
set :current_bass_pattern, bass_patterns[0]
set :current_melody_pattern, melody_patterns[0]
set :chord_cutoff, 80
set :bass_cutoff, 70

# Structure conductor
live_loop :conductor do
  cue :intro
  sleep 8  # 16 bars
  
  cue :buildup_1
  sleep 8  # 8 bars
  
  cue :drop_1
  sleep 8  # 16 bars
  
  cue :breakdown
  sleep 8  # 16 bars
  
  cue :buildup_2
  sleep 8  # 8 bars
  
  cue :drop_2
  sleep 8  # 16 bars
  
  cue :outro
  sleep 8  # 16 bars
  
  cue :stop
end

# Section manager
live_loop :section_manager do
  sync_bpm :conductor
  current_section_value = look(:conductor)
  set :current_section, current_section_value
  
  case current_section_value
  when :intro
    set :current_kick_pattern, kick_patterns[0]
    set :current_clap_pattern, clap_patterns[0]
    set :current_hat_pattern, hat_patterns[0]
    set :current_bass_pattern, bass_patterns[0]
    set :current_melody_pattern, melody_patterns[0]
    set :chord_cutoff, 80
    set :bass_cutoff, 70
    control :lead, amp: 0.5
    control :hihats, amp: 0.2
    control :chords, amp: 0.4
    control :bass, amp: 0.8
    control :pads, amp: 0.2
    
  when :buildup_1
    set :current_hat_pattern, hat_patterns[1]
    set :current_clap_pattern, clap_patterns[1]
    set :chord_cutoff, 100
    control :hihats, amp: 0.8
    control :shaker, amp: 0.4
    
  when :drop_1
    set :current_kick_pattern, kick_patterns[0]
    set :current_clap_pattern, clap_patterns[0]
    set :current_hat_pattern, hat_patterns[0]
    set :current_melody_pattern, melody_patterns[1]
    set :chord_cutoff, 120
    set :bass_cutoff, 90
    control :lead, amp: 0.9
    control :chords, amp: 0.8
    control :bass, amp: 1.2
    control :hihats, amp: 0.3
    
  when :breakdown
    set :current_kick_pattern, kick_patterns[0]
    set :current_melody_pattern, melody_patterns[0]
    set :chord_cutoff, 60
    set :bass_cutoff, 50
    control :kick_drum, amp: 0
    control :bass, amp: 0.3
    control :chords, amp: 0.3
    control :lead, amp: 0.6
    
  when :buildup_2
    set :current_hat_pattern, hat_patterns[1]
    set :current_kick_pattern, kick_patterns[1]
    set :chord_cutoff, 100
    control :hihats, amp: 1.0
    control :shaker, amp: 0.6
    
  when :drop_2
    set :current_kick_pattern, kick_patterns[0]
    set :current_melody_pattern, melody_patterns[1]
    set :chord_cutoff, 130
    set :bass_cutoff, 100
    control :kick_drum, amp: 2
    control :bass, amp: 1.5
    control :lead, amp: 1.0
    control :chords, amp: 0.9
    
  when :outro
    set :current_melody_pattern, melody_patterns[0]
    set :chord_cutoff, 80
    set :bass_cutoff, 60
    control :lead, amp: 0
    control :chords, amp: 0
    control :bass, amp: 0
    control :hihats, amp: 0.1
    control :clap, amp: 0
    control :shaker, amp: 0
    
  when :stop
    stop
  end
end

# Clock for synchronization
live_loop :clock do
  cue :tick
  sleep 1
end

# Main kick drum
live_loop :kick_drum, sync: :tick do
  current_kick_pattern_val = get(:current_kick_pattern) || kick_patterns[0]
  16.times do |i|
    sample :bd_haus, amp: 2 if current_kick_pattern_val[i] == 1
    sleep 0.25
  end
end

# Clap with variations
live_loop :clap, sync: :tick do
  current_clap_pattern_val = get(:current_clap_pattern) || clap_patterns[0]
  16.times do |i|
    sample :drum_snare_soft, amp: 1.2 if current_clap_pattern_val[i] == 1
    sleep 0.25
  end
end

# Hi-hats with variations and proper mixing
live_loop :hihats, sync: :tick do
  current_hat_pattern_val = get(:current_hat_pattern) || hat_patterns[0]
  16.times do |i|
    sample :drum_cymbal_closed, amp: 0.3, rate: 1.1 if current_hat_pattern_val[i] == 1
    sleep 0.25
  end
end

# Bassline with sidechain effect and filter automation
live_loop :bass, sync: :tick do
  use_synth :saw
  current_bass_pattern_val = get(:current_bass_pattern) || bass_patterns[0]
  current_bass_cutoff = get(:bass_cutoff) || 70
  
  with_fx :lpf, cutoff: current_bass_cutoff do
    with_fx :compressor, threshold: 0.1, clamp_time: 0.01, relax_time: 0.1 do
      16.times do |i|
        play current_bass_pattern_val[i], amp: 1.2, release: 0.2, sustain: 0.1 unless current_bass_pattern_val[i] == :r
        sleep 0.25
      end
    end
  end
end

# Main chord progression with filter automation
live_loop :chords, sync: :tick do
  use_synth :prophet
  current_chord_cutoff = get(:chord_cutoff) || 80
  
  with_fx :lpf, cutoff: current_chord_cutoff do
    with_fx :compressor, threshold: 0.2, ratio: 4 do
      4.times do |i|
        play_chord chord_progression[i], amp: 0.6, release: 1.5
        sleep 4
      end
    end
  end
end

# Lead melody with variations
live_loop :lead, sync: :tick do
  use_synth :pluck
  current_melody_pattern_val = get(:current_melody_pattern) || melody_patterns[0]
  
  16.times do |i|
    play current_melody_pattern_val[i], amp: 0.5, release: 0.3 unless current_melody_pattern_val[i] == :r
    sleep 0.5
  end
end

# Atmospheric pads
live_loop :pads, sync: :tick do
  use_synth :hollow
  with_fx :reverb, room: 0.8 do
    4.times do |i|
      play_chord pad_chords[i], amp: 0.3, attack: 2, release: 6
      sleep 4
    end
  end
end

# Percussion elements
live_loop :shaker, sync: :tick do
  16.times do
    sample :perc_snap2, amp: 0.2, rate: 1.5
    sleep 0.5
  end
end

# Enhanced FX and transitions
live_loop :fx_transitions, sync: :tick do
  sync_bpm :conductor
  current_section_val = look(:conductor)
  
  case current_section_val
  when :buildup_1, :buildup_2
    # Riser effect
    with_fx :lpf, cutoff: 60 do
      with_fx :reverb, room: 0.9 do
        sample :ambi_glass_rub, rate: 0.5, amp: 0.6, attack: 4, release: 4
      end
    end
    sleep 8
    
    # White noise sweep
    with_fx :hpf, cutoff: 40 do
      sample :noise, rate: 0.3, amp: 0.4, attack: 2, release: 2, cutoff: 120
    end
    
  when :drop_1, :drop_2
    # Impact effect
    sample :drum_roll, rate: 0.8, amp: 0.5, release: 0.5
    sleep 0.5
    
  when :breakdown, :outro
    # Reverse cymbal
    sample :drum_cymbal_open, rate: -1, amp: 0.4, release: 2
  end
end

# Drum fills before transitions
live_loop :drum_fills, sync: :tick do
  sync_bpm :conductor
  current_section_fill = look(:conductor)
  
  if [:buildup_1, :buildup_2].include?(current_section_fill)
    sleep 8  # Wait until last 2 bars of build-up
    # Drum roll fill
    4.times do
      sample :drum_tom_hi_hard, amp: 0.3, rate: 1.2
      sleep 0.125
    end
  end
end