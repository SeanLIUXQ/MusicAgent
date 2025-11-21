use_bpm 76

# Define musical elements
main_key = :eb3
chord_progression_a = [:eb3, :c3, :ab3, :bb3]
chord_progression_b = [:g3, :c4]

# Define synth and sample choices
epiano_synth = :epiano
bass_synth = :fm
pad_synth = :hollow
lead_synth = :saw
guitar_synth = :pluck

# Define effects
main_reverb = 0.6
delay_time = 0.75

# Global section state
set :current_section, :intro

# Improved section controller with proper timing
live_loop :section_controller do
  set :current_section, :intro
  cue :intro
  sleep 8
  
  set :current_section, :verse_a
  cue :verse_a
  sleep 8
  
  set :current_section, :pre_chorus
  cue :pre_chorus
  sleep 8
  
  set :current_section, :chorus
  cue :chorus
  sleep 8
  
  set :current_section, :interlude
  cue :interlude
  sleep 8
  
  set :current_section, :verse_b
  cue :verse_b
  sleep 8
  
  set :current_section, :bridge
  cue :bridge
  sleep 8
  
  set :current_section, :outro
  cue :outro
  sleep 8
end

# Introduction section - only plays during intro
live_loop :intro_epiano do
  sync :intro
  use_synth epiano_synth
  with_fx :reverb, mix: main_reverb do
    with_fx :lpf, cutoff: 90 do
      play_chord chord(main_key, :M9), amp: 0.3, release: 4
      sleep 4
    end
  end
  stop if get[:current_section] != :intro
end

live_loop :intro_atmosphere do
  sync :intro
  sample :ambi_soft_buzz, rate: 0.3, amp: 0.1
  sleep 8
  stop if get[:current_section] != :intro
end

live_loop :intro_bass do
  sync :intro
  use_synth bass_synth
  with_fx :reverb, mix: 0.3 do
    play main_key, amp: 0.2, release: 8, note_slide: 0.5
    sleep 8
  end
  stop if get[:current_section] != :intro
end

# Main drum pattern with section variations
live_loop :drums_main do
  sync_bpm :tick
  current_sect = get[:current_section]
  
  with_fx :level, amp: case current_sect
    when :intro then 0.6
    when :verse_a, :verse_b then 0.7
    when :pre_chorus then 0.8
    when :chorus, :bridge then 0.9
    when :outro then 0.5
    else 0.8
  end do
    
    # Basic pattern with variations
    case current_sect
    when :intro, :verse_a, :verse_b
      sample :drum_bass_soft, amp: 0.3, rate: 0.9
      sleep 0.5
      sample :drum_snare_soft, amp: 0.4
      sleep 0.75
      sample :drum_bass_soft, amp: 0.3, rate: 0.9
      sleep 0.5
      sample :drum_snare_soft, amp: 0.4
      sleep 0.25
      
    when :pre_chorus
      # More energetic pattern
      sample :drum_bass_soft, amp: 0.4, rate: 1.0
      sleep 0.375
      sample :drum_snare_soft, amp: 0.5
      sleep 0.375
      sample :drum_bass_soft, amp: 0.4, rate: 1.0
      sleep 0.375
      sample :drum_snare_soft, amp: 0.5
      sleep 0.375
      
    when :chorus, :bridge
      # Full power pattern
      sample :drum_bass_soft, amp: 0.5, rate: 1.1
      sleep 0.25
      sample :drum_snare_soft, amp: 0.6
      sleep 0.5
      sample :drum_bass_soft, amp: 0.4, rate: 1.0
      sleep 0.25
      sample :drum_snare_soft, amp: 0.6
      sleep 0.5
      
    when :outro
      # Fading pattern
      sample :drum_bass_soft, amp: 0.2, rate: 0.8
      sleep 1
      sample :drum_snare_soft, amp: 0.3
      sleep 1
    end
  end
end

# Drum fills for transitions
live_loop :drum_fills do
  sync :section_controller
  current_sect = get[:current_section]
  
  if current_sect == :pre_chorus
    # Build-up fill
    with_fx :level, amp: 0.3 do
      4.times do |i|
        sample :drum_tom_hi_soft, amp: 0.2 + (0.1 * i)
        sleep 0.25
      end
    end
  elsif current_sect == :chorus
    # Crash cymbal on chorus entry
    sample :drum_cymbal_open, amp: 0.4, sustain: 0.5
  elsif current_sect == :outro
    # Final fill
    sample :drum_roll, amp: 0.3, rate: 0.8
  end
end

live_loop :hihat_shuffle do
  sync_bpm :tick
  current_sect = get[:current_section]
  
  amp_level = case current_sect
    when :intro, :verse_a, :verse_b then 0.15
    when :pre_chorus then 0.2
    when :chorus, :bridge then 0.25
    when :outro then 0.1
    else 0.15
  end
  
  sample :drum_cymbal_closed, amp: amp_level, rate: 1.2
  sleep 0.25
  sample :drum_cymbal_closed, amp: amp_level * 0.75, rate: 1.1
  sleep 0.25
  sample :drum_cymbal_closed, amp: amp_level, rate: 1.2
  sleep 0.25
  sample :drum_cymbal_closed, amp: amp_level * 0.75, rate: 1.1
  sleep 0.25
end

# Improved bass line with section variations and better presence
live_loop :bass_line do
  sync :section_controller
  use_synth bass_synth
  
  with_fx :reverb, mix: 0.2 do
    with_fx :slicer, phase: 0.5 do
      with_fx :eq, low: 2.0, mid: 0.8, high: 0.5 do
        
        case get[:current_section]
        when :verse_a, :verse_b
          bass_pattern = [:eb2, :g2, :bb2, :c3]
          play_pattern_timed bass_pattern, [1.5, 0.5, 1, 1], amp: 0.5, release: 0.4
          
        when :pre_chorus
          bass_pattern = [:eb2, :f2, :g2, :ab2, :bb2, :c3]
          play_pattern_timed bass_pattern, [0.75, 0.75, 0.75, 0.75, 0.5, 0.5], amp: 0.6, release: 0.3
          
        when :chorus
          bass_pattern = [:eb2, :f2, :g2, :ab2, :bb2, :c3, :d3, :eb3]
          play_pattern_timed bass_pattern, [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5], amp: 0.7, release: 0.2
          
        when :bridge
          bass_pattern = [:f2, :ab2, :c3, :eb3, :bb2, :g2]
          play_pattern_timed bass_pattern, [1, 1, 1, 1, 1, 1], amp: 0.6, release: 0.4
          
        when :outro
          bass_pattern = [:eb2, :bb2, :eb2]
          play_pattern_timed bass_pattern, [2, 2, 4], amp: 0.4, release: 1
        end
      end
    end
  end
end

# Section-aware electric piano chords
live_loop :epiano_chords do
  sync :section_controller
  use_synth epiano_synth
  
  with_fx :reverb, mix: main_reverb do
    with_fx :lpf, cutoff: case get[:current_section]
      when :intro, :verse_a, :verse_b then 100
      when :pre_chorus then 110
      when :chorus, :bridge then 120
      when :outro then 80
      else 100
    end do
      
      case get[:current_section]
      when :intro, :verse_a, :verse_b
        chord_sequence = [chord(:eb3, :M9), chord(:c3, :m9), chord(:ab3, :M9), chord(:bb3, "7sus4")]
        play_chord chord_sequence.tick, amp: 0.3, release: 2
        sleep 2
        
      when :pre_chorus
        chord_sequence = [chord(:f3, :m9), chord(:bb3, :M7), chord(:eb3, :M9)]
        play_chord chord_sequence.tick, amp: 0.4, release: 1.5
        sleep 1.5
        
      when :chorus
        chord_sequence = [chord(:g3, :M9), chord(:c4, :m9), chord(:ab3, :M7), chord(:bb3, :dom7)]
        play_chord chord_sequence.tick, amp: 0.5, release: 1.5
        sleep 1.5
        
      when :bridge
        chord_sequence = [chord(:f3, :m9), chord(:bb3, :M7), chord(:eb3, :M9), chord(:ab3, :dom7)]
        play_chord chord_sequence.tick, amp: 0.4, release: 2
        sleep 2
        
      when :outro
        chord_sequence = [chord(:eb3, :M9), chord(:bb3, :M7)]
        play_chord chord_sequence.tick, amp: 0.2, release: 4
        sleep 4
      end
    end
  end
end

# Warm pad with section variations
live_loop :warm_pad do
  sync :section_controller
  use_synth pad_synth
  
  case get[:current_section]
  when :intro, :verse_a, :verse_b
    with_fx :reverb, mix: 0.8 do
      with_fx :lpf, cutoff: 80 do
        play_chord chord(main_key, :M7), amp: 0.15, attack: 2, release: 6
        sleep 8
      end
    end
    
  when :pre_chorus, :chorus
    with_fx :reverb, mix: 0.9 do
      with_fx :lpf, cutoff: 100 do
        play_chord chord(:g3, :M7), amp: 0.2, attack: 1, release: 4
        sleep 4
        play_chord chord(:c4, :m7), amp: 0.2, attack: 1, release: 4
        sleep 4
      end
    end
    
  when :bridge
    with_fx :reverb, mix: 0.7 do
      with_fx :lpf, cutoff: 90 do
        play_chord chord(:f3, :m9), amp: 0.18, attack: 2, release: 6
        sleep 8
      end
    end
    
  when :outro
    with_fx :reverb, mix: 0.9 do
      with_fx :lpf, cutoff: 60 do |c|
        play_chord chord(main_key, :M7), amp: 0.1, attack: 2, release: 8
        16.times do |i|
          control c, cutoff: 60 - (i * 3)
          sleep 0.5
        end
      end
    end
  end
end

# Nylon guitar arpeggios - only in certain sections
live_loop :guitar_arpeggios do
  sync :section_controller
  
  case get[:current_section]
  when :verse_a, :verse_b, :bridge
    use_synth guitar_synth
    with_fx :reverb, mix: 0.4 do
      with_fx :lpf, cutoff: 110 do
        guitar_pattern = chord(main_key, :M9).shuffle
        play_pattern_timed guitar_pattern, [0.25, 0.5, 0.25, 0.5], amp: 0.2
        sleep 2
      end
    end
  else
    sleep 2
  end
end

# Saxophone melody for specific sections only
live_loop :sax_melody do
  sync :section_controller
  
  case get[:current_section]
  when :chorus, :bridge
    use_synth lead_synth
    with_fx :reverb, mix: 0.7 do
      with_fx :delay, delay_time: delay_time do
        if get[:current_section] == :chorus
          melody_notes = [:eb4, :g4, :bb4, :eb5, :g4, :f4]
          play_pattern_timed melody_notes, [0.75, 0.5, 0.75, 0.5, 0.5, 0.5], amp: 0.4, release: 0.4
        else
          melody_notes = [:f4, :ab4, :c5, :eb5, :bb4, :ab4]
          play_pattern_timed melody_notes, [1, 0.5, 1, 0.5, 0.5, 0.5], amp: 0.35, release: 0.5
        end
        sleep 4
      end
    end
  else
    sleep 4
  end
end

# Vocal texture with section awareness
live_loop :vocal_texture do
  sync :section_controller
  
  case get[:current_section]
  when :pre_chorus, :chorus, :bridge
    with_fx :reverb, mix: 0.8 do
      with_fx :lpf, cutoff: 120 do
        sample :ambi_choir, rate: 0.8, amp: 0.2, attack: 1, release: 3
        sleep 8
      end
    end
  else
    sleep 8
  end
end

# Tambourine for specific sections
live_loop :tambourine do
  sync :section_controller
  
  case get[:current_section]
  when :pre_chorus, :chorus
    sample :perc_bell, rate: 1.5, amp: 0.2
    sleep 2
    sample :perc_bell, rate: 1.3, amp: 0.15
    sleep 2
  else
    sleep 4
  end
end

# Vinyl crackle for texture throughout
live_loop :vinyl_texture do
  sample :vinyl_hiss, amp: 0.05, rate: 0.3
  sleep 8
end

# Transition effects between sections
live_loop :transitions do
  sync :section_controller
  current_sect = get[:current_section]
  
  case current_sect
  when :pre_chorus
    # Rising pitch effect
    with_fx :pitch_shift, pitch: 12 do
      sample :ambi_drone, rate: 0.5, amp: 0.3, attack: 2, release: 2
    end
    
  when :bridge
    # Filter sweep
    with_fx :lpf, cutoff: 60 do |c|
      16.times do |i|
        control c, cutoff: 60 + (i * 8)
        sleep 0.25
      end
    end
    
  when :outro
    # Fade out effect
    with_fx :level, amp: 1.0 do |l|
      16.times do |i|
        control l, amp: 1.0 - (i * 0.0625)
        sleep 1
      end
    end
  end
end

# Additional percussion layer for chorus
live_loop :extra_percussion do
  sync :section_controller
  
  if get[:current_section] == :chorus
    sample