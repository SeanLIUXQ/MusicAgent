# Chinese Classical Music: Jiangnan Sizhu Style - Improved Version
# Inspired by "Er Quan Ying Yue" (Moon Reflected on Second Spring)
# Enhanced with structural variations, dynamic progression, and authentic ornamentation

use_bpm 60  # Adagio to Andante tempo

# Global state variables for form and dynamics
set :current_form, :exposition
set :master_amp, 1.0
set :emotional_intensity, 0.5

# Define pentatonic scale patterns (Yu mode - traditional Chinese scale)
yu_scale_low = [:d3, :f3, :g3, :a3, :c4]
yu_scale_mid = [:d4, :f4, :g4, :a4, :c5]
yu_scale_high = [:d5, :f5, :g5, :a5, :c6]

# Expanded melodic themes with variations
main_theme_a = [:d4, :f4, :g4, :a4, :g4, :f4, :d4, :c4, :d4]
main_theme_b = [:a4, :c5, :d5, :c5, :a4, :g4, :f4, :d4]
climax_theme = [:d5, :f5, :g5, :a5, :g5, :f5, :d5, :c5, :a4, :g4]
extended_theme = [:d4, :f4, :g4, :a4, :c5, :a4, :g4, :f4, :d4, :c4, :d3, :f3, :g3]

# Transition phrases
define :transition_phrase do |duration_type|
  case duration_type
  when :short
    [:c4, :d4, :f4, :g4].each do |note_val|
      play note_val, attack: 0.1, release: 0.4, amp: 0.5
      sleep 0.2
    end
  when :long
    [:g3, :a3, :c4, :d4, :f4].each do |note_val|
      play note_val, attack: 0.15, release: 0.6, amp: 0.6
      sleep 0.3
    end
  end
end

# Form controller
live_loop :form_controller, sync: :start do
  forms = [:free_intro, :exposition, :development, :climax, :cadenza, :coda]
  current_form_val = forms.tick
  set :current_form, current_form_val
  
  case current_form_val
  when :climax
    set :emotional_intensity, 1.0
    set :master_amp, 1.0
  when :coda
    in_thread do
      8.times do |i|
        set :master_amp, 1.0 - (i * 0.125)
        sleep 2.0
      end
    end
  when :free_intro
    set :emotional_intensity, 0.3
  else
    set :emotional_intensity, 0.5 + (tick % 3) * 0.2
  end
  
  sleep 8  # Change form every 32 beats
end

# Erhu (main instrument) - enhanced with traditional techniques
live_loop :erhu_melody, sync: :start do
  use_synth :saw
  use_octave -1
  current_form_val = get(:current_form)
  master_amp_val = get(:master_amp)
  intensity_val = get(:emotional_intensity)
  
  case current_form_val
  when :free_intro
    with_fx :reverb, mix: 0.4 do
      with_fx :vowel, voice: 0.3 do
        with_fx :vibrato, depth: 0.08, delay: 0.5 do
          play_pattern_timed [:d3, :f3], [1.5, 2.0], attack: 0.2, release: 1.0, amp: 0.6 * master_amp_val
          sleep 1.0
          play :g3, attack: 0.1, release: 1.5, amp: 0.8 * master_amp_val
          sleep 2.0
        end
      end
    end
    
  when :exposition
    # Varied exposition based on tick
    if tick % 4 == 0
      with_fx :vibrato, depth: 0.1 do
        extended_theme.each do |note_val|
          play note_val, attack: 0.15, release: 0.8, amp: (0.7 * intensity_val * master_amp_val)
          sleep 0.6
        end
      end
    else
      main_theme_a.each do |note_val|
        play note_val, attack: 0.15, release: 0.8, amp: (0.7 * intensity_val * master_amp_val)
        sleep 0.8
      end
    end
    sleep 1.5
    
  when :development
    transition_phrase(:short)
    sleep 0.5
    
    with_fx :lpf, cutoff: 80 + (intensity_val * 40) do
      main_theme_b.each_with_index do |note_val, idx|
        play note_val, attack: 0.1, release: 0.6, amp: (0.5 + (idx * 0.05)) * intensity_val * master_amp_val
        sleep 0.6 - (idx * 0.05)
      end
    end
    
  when :climax
    # Crescendo build-up
    4.times do |i|
      play main_theme_b[i], amp: (0.5 + (i * 0.12)) * master_amp_val, release: 0.8 - (i * 0.1)
      sleep 0.5
    end
    
    # Dramatic climax
    with_fx :distortion, distort: 0.15 do
      with_fx :pitch_shift, pitch: 1 do
        climax_theme.each_with_index do |note_val, i|
          play note_val, attack: 0.05, release: 0.4, amp: (1.0 + (i * 0.03)) * master_amp_val
          sleep 0.4 - (i * 0.02)
        end
      end
    end
    
  when :cadenza
    # Free solo section
    with_fx :reverb, mix: 0.6 do
      with_fx :vibrato, depth: 0.15 do
        [:d4, :f4, :g4, :a4, :c5, :a4, :g4, :f4, :d4].each do |note_val|
          play note_val, attack: 0.2, release: 1.2, amp: 0.8 * master_amp_val
          sleep [0.8, 1.2, 0.6].choose
        end
      end
    end
    
  when :coda
    # Fading recapitulation
    with_fx :reverb, mix: 0.3 do
      [0.7, 0.5, 0.3].each do |amp_level|
        main_theme_a.each do |note_val|
          play note_val, attack: 0.2, release: 1.0, amp: amp_level * master_amp_val
          sleep 0.9
        end
      end
    end
  end
  
  sleep 4.0
end

# Zhonghu (alto erhu) - optimized frequency range
live_loop :zhonghu_harmony, sync: :erhu_melody do
  use_synth :hollow
  use_octave -2
  master_amp_val = get(:master_amp)
  
  harmony_notes = [:d2, :f2, :g2, :a2, :c3]
  
  with_fx :reverb, mix: 0.5 do
    with_fx :lpf, cutoff: 400 do  # Limit high frequencies
      harmony_notes.each do |bass_note|
        play bass_note, attack: 0.3, release: 2.0, amp: 0.4 * master_amp_val
        sleep 2.5
      end
    end
  end
  
  sleep 1.0
end

# Pipa (plucked instrument) - rhythmic variations
live_loop :pipa_arpeggios, sync: :erhu_melody do
  use_synth :pluck
  use_octave 0
  master_amp_val = get(:master_amp)
  
  arpeggio_patterns = [
    [:d4, :f4, :a4, :c5],
    [:f4, :a4, :c5, :d5],
    [:g4, :c5, :d5, :f5]
  ]
  
  rhythms = [
    [0.2, 0.3, 0.2, 0.3],  # Standard
    [0.4, 0.1, 0.4, 0.1],  # Syncopated
    [0.15, 0.15, 0.15, 0.55]  # Rushed ending
  ]
  
  current_rhythm = rhythms.choose
  
  with_fx :echo, decay: 2 do
    arpeggio_patterns.each do |pattern|
      pattern.each_with_index do |pluck_note, i|
        play pluck_note, amp: 0.3 * master_amp_val, release: current_rhythm[i]
        sleep current_rhythm[i]
      end
      sleep 1.0
    end
  end
  
  sleep 2.0
end

# Guzheng (zither) - sustained bass with filtered range
live_loop :guzheng_bass, sync: :erhu_melody do
  use_synth :beep
  use_octave -3
  master_amp_val = get(:master_amp)
  
  bass_notes = [:d1, :g1, :c2]
  
  with_fx :lpf, cutoff: 60 do
    bass_notes.each do |low_note|
      play low_note, attack: 0.5, release: 3.0, amp: 0.3 * master_amp_val
      sleep 4.0
    end
  end
  
  sleep 2.0
end

# Xiao (flute) - moved to higher frequency range
live_loop :xiao_counterpoint, sync: :erhu_melody do
  use_synth :fm
  use_octave 2  # Move higher to avoid erhu range
  master_amp_val = get(:master_amp)
  
  counter_melody = [:a5, :g5, :f5, :d5, :c5, :d5, :f5, :g5]
  
  with_fx :reverb, room: 0.8 do
    with_fx :vowel, voice: 0.7 do
      with_fx :hpf, cutoff: 800 do  # Remove low frequencies
        counter_melody.each do |flute_note|
          play flute_note, attack: 0.2, release: 1.0, amp: 0.4 * master_amp_val
          sleep 1.2
        end
      end
    end
  end
  
  sleep 3.0
end

# Yangqin (hammered dulcimer) - polyrhythmic variations
live_loop :yangqin_rhythm, sync: :erhu_melody do
  use_synth :pulse
  use_octave 0
  master_amp_val = get(:master_amp)
  
  rhythm_notes = [:d4, :g4, :a4, :c5]
  
  with_fx :pan, pan: -0.3 do
    4.times do |repeat_count|
      rhythm_notes.each do |hammer_note|
        play hammer_note, attack: 0.05, release: 0.3, amp: (0.2 + (repeat_count * 0.05)) * master_amp_val
        sleep [0.5, 0.6, 0.4].choose  # Varied rhythm
      end
    end
  end
  
  sleep 2.0
end

# Traditional percussion foundation
live_loop :traditional_percussion, sync: :erhu_melody do
  master_amp_val = get(:master_amp)
  
  with_fx :lpf, cutoff: 200 do
    sample :drum_tom_hi_hard, rate: 0.3, amp: 0.1 * master_amp_val
    sleep 2.0
    sample :drum_tom_hi_hard, rate: 0.4, amp: 0.08 * master_amp_val
    sleep 2.0
  end
end

# Enhanced courtyard acoustic simulation
live_loop :courtyard_ambience, sync: :start do
  master_amp_val = get(:master_amp)
  
  with_fx :reverb, room: 0.9, damp: 0.7 do
    with_fx :echo, decay: 8 do
      sample :ambi_dark_woosh, rate: 0.3, amp: 0.1 * master_amp_val
      sleep 8
    end
  end
end