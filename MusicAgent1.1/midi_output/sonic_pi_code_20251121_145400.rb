use_bpm 76

# Define pentatonic scale in G major (Gong Shang Jiao Zhi Yu)
pentatonic_scale = (scale :g4, :major_pentatonic, num_octaves: 2)

# Melodic phrases for different sections with more variation
intro_melody = [:g4, :a4, :b4, :d5, :g5].ring
a_section_melody = [:g4, :a4, :b4, :d5, :b4, :a4, :g4, :e4, :d4, :e4, :g4, :a4, :b4, :d5, :g5, :d5].ring
b_section_melody = [:d5, :e5, :g5, :a5, :g5, :e5, :d5, :b4, :a4, :b4, :d5, :e5, :g5, :a5, :b5, :a5].ring
final_melody = [:g4, :a4, :b4, :d5, :b4, :a4, :g4, :e4, :d4, :e4, :g4, :a4, :g4, :e4, :d4, :c4].ring

# More varied yangqin arpeggio patterns
yangqin_arpeggios = [
  chord(:g3, '5'), chord(:c4, '5'), chord(:d4, '5'), chord(:g3, '5'),
  chord(:g3, '5'), chord(:a3, '5'), chord(:d4, '5'), chord(:g3, '5'),
  chord(:g3, 'M'), chord(:c4, 'M'), chord(:d4, 'sus4'), chord(:g3, 'M')
].ring

# Pipa ornamentation patterns
pipa_ornaments = [
  [:g4, :gs4, :a4], [:a4, :as4, :b4], [:b4, :c5, :d5], [:d5, :ds5, :e5],
  [:e5, :f5, :g5], [:g5, :fs5, :e5], [:e5, :ds5, :d5], [:d5, :cs5, :b4]
].ring

# Enhanced percussion patterns with variation
wooden_fish_varied = [
  [1, 0.8], [0, 0], [0, 0], [0.6, 0],
  [0, 0], [0.7, 0], [1, 0.5], [0, 0],
  [0.8, 0], [0, 0], [0.5, 0], [0.9, 0.3],
  [0, 0], [0.6, 0], [1, 0.7], [0, 0]
].ring

# More varied bass progression
bass_progression = [
  [:g2, :d3], [:c3, :g3], [:d3, :a3], [:g2, :d3],
  [:g2, :b2], [:c3, :e3], [:d3, :fs3], [:g2, :b2]
].ring * 4

# Introduction section (4 measures)
live_loop :introduction do
  stop
  use_synth :blade
  with_fx :reverb, room: 0.8 do
    4.times do |i|
      amp_val = 0.2 + (i * 0.05)
      play intro_melody.tick, attack: 0.5, release: 2, amp: amp_val
      sleep 2
    end
  end
end

# Bamboo flute (main melody) with dynamic development
live_loop :bamboo_flute do
  sync :introduction
  use_synth :hollow
  with_fx :reverb, room: 0.6, mix: 0.4 do
    with_fx :vibrato, depth: 0.1, phase: 4 do
      
      # A section (8 measures) with crescendo
      use_octave 0
      16.times do |i|
        amp_val = 0.4 + (i * 0.015)
        play a_section_melody[i], attack: 0.1, release: 0.3, amp: amp_val
        sleep 0.5
      end
      
      # B section (8 measures) - raised fifth with more intensity
      use_octave 1
      16.times do |i|
        amp_val = 0.5 + (i * 0.01)
        play b_section_melody[i], attack: 0.1, release: 0.3, amp: amp_val
        sleep 0.5
      end
      
      # A' section (8 measures) - return with ornaments and decrescendo
      use_octave 0
      16.times do |i|
        amp_val = 0.5 - (i * 0.0125)
        play final_melody[i], attack: 0.1, release: 0.4, amp: amp_val
        if i % 4 == 0
          with_fx :slicer, phase: 0.25 do
            play final_melody[i] + 12, release: 0.2, amp: 0.2
          end
        end
        sleep 0.5
      end
      
      # Final section (4 measures) with fade out
      8.times do |i|
        amp_val = 0.3 - (i * 0.025)
        play final_melody[i], attack: 0.3, release: 1.5, amp: amp_val
        sleep 1
      end
    end
  end
end

# Yangqin (accompaniment) with rhythmic variation
live_loop :yangqin do
  sync :introduction
  use_synth :pluck
  with_fx :lpf, cutoff: 90 do
    
    # A section - sparse
    16.times do |i|
      if i % 4 == 0
        play_chord yangqin_arpeggios.tick, amp: 0.3, release: 1.2
      end
      sleep 0.5
    end
    
    # B section - more active
    16.times do |i|
      if i % 2 == 0
        play_chord yangqin_arpeggios.tick, amp: 0.4, release: 0.8
      end
      sleep 0.5
    end
    
    # A' section - most active
    16.times do |i|
      play_chord yangqin_arpeggios.tick, amp: 0.35, release: 0.6
      sleep 0.5
    end
    
    # Final section - harmonics with fade
    8.times do |i|
      amp_val = 0.2 - (i * 0.0125)
      play_chord [chord(:g5, '5'), chord(:d6, '5')].choose, amp: amp_val, release: 2
      sleep 1
    end
  end
end

# Pipa (ornamentation) with earlier entry and varying density
live_loop :pipa do
  sync :introduction
  sleep 8  # Enter earlier in A section
  
  use_synth :pluck
  with_fx :reverb, room: 0.5 do
    # Play throughout with varying density
    48.times do |i|
      density_val = case
        when i < 16 then 0.3  # Sparse in A section
        when i < 32 then 0.6  # More active in B section  
        else 0.8              # Most active in A' section
      end
      
      if rand < density_val
        play_pattern_timed pipa_ornaments.tick, [0.08, 0.08, 0.34], amp: 0.25
      else
        sleep 0.5
      end
    end
  end
end

# Cello (bass line) with improved harmonic movement
live_loop :cello do
  sync :introduction
  use_synth :hollow
  with_fx :lpf, cutoff: 70 do
    
    # More varied bass progression
    32.times do |i|
      play_chord bass_progression[i], attack: 0.3, release: 1.8, amp: 0.3
      sleep 1
    end
    
    # Final section with descending pattern
    final_bass = [:g2, :f2, :e2, :d2, :c2, :b1, :a1, :g1].ring
    8.times do |i|
      play final_bass[i], attack: 1, release: 3, amp: 0.2
      sleep 2
    end
  end
end

# Enhanced wooden fish percussion
live_loop :wooden_fish do
  sync :introduction
  use_synth :perc_bell
  
  32.times do |i|
    amp_val, rate_val = wooden_fish_varied[i]
    if amp_val > 0
      sample :perc_bell, rate: 0.7 + (rate_val * 0.3), amp: amp_val * 0.15
    end
    sleep 0.25
  end
end

# Improved section transitions with anticipation
live_loop :section_markers do
  sync :introduction
  
  # Transition to B section
  sleep 8  # Half beat early for anticipation
  with_fx :reverb, room: 0.8 do
    sample :drum_roll, rate: 0.8, amp: 0.3
    sleep 0.5
    4.times do |j|
      sample :drum_tom_lo_hard, amp: 0.2 + (j * 0.1)
      sleep 0.25
    end
  end
  
  sleep 8  # After B section
  
  # Transition to A' section
  with_fx :reverb, room: 0.8 do
    sample :drum_roll, rate: 1.0, amp: 0.4
    sleep 0.5
    4.times do |j|
      sample :drum_tom_mid_hard, amp: 0.15 + (j * 0.08)
      sleep 0.25
    end
  end
  
  sleep 8  # Before final section
  
  # Final transition
  with_fx :reverb, room: 1.0 do
    8.times do |j|
      sample :drum_tom_hi_hard, amp: 0.1 + (j * 0.05), rate: 0.9 - (j * 0.05)
      sleep 0.125
    end
  end
end

# Add wind chimes for atmospheric texture
live_loop :wind_chimes do
  sync :introduction
  sleep 8  # Enter during B section
  
  with_fx :reverb, room: 0.9 do
    4.times do
      if rand < 0.7
        sample :perc_bell2, rate: rrand(0.8, 1.2), amp: 0.08, pan: rrand(-0.5, 0.5)
      end
      sleep 4
    end
  end
end

# Start the composition
in_thread do
  sleep 1
  cue :introduction
end

# Optional: Add a way to stop all loops gracefully
live_loop :master_control do
  sync :/stop_all
  stop
end