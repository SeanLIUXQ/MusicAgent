# Hong Kong Style Modern Music - Improved Version
# Fusion of Cantopop elements with modern electronic production with clear structure

use_bpm 100

# Define musical elements
scale_pattern = scale(:c4, :major_pentatonic, num_octaves: 2)
chord_progression = [chord(:c4, :major), chord(:g4, :major), chord(:a4, :minor), chord(:f4, :major)]
bass_line_pattern = [:c2, :g2, :a2, :f2]

# Varied melody with different phrases
melody_variations = [
  [:c5, :e5, :g5, :a5, :g5, :e5, :c5, :rest],
  [:g5, :a5, :c6, :d6, :c6, :a5, :g5, :rest],
  [:a5, :c6, :e6, :g6, :e6, :c6, :a5, :rest],
  [:c5, :d5, :e5, :g5, :a5, :g5, :e5, :d5]
]

# Traditional Chinese instrument embellishments (in key)
erhu_embellishments = scale(:c4, :major_pentatonic).shuffle[0..5]
guzheng_pattern = [:c4, :e4, :g4, :a4, :c5, :e5, :g5]

# Environmental sounds (Hong Kong street ambiance)
street_sounds = [:ambi_glass_hum, :ambi_drone, :ambi_soft_buzz]

# Song structure management
section = :intro

live_loop :section_manager do
  case section
  when :intro
    sleep 8
    section = :verse
  when :verse
    sleep 8
    section = :chorus
  when :chorus
    sleep 8
    section = :bridge
  when :bridge
    sleep 8
    section = :outro
  when :outro
    sleep 8
    stop
  end
end

# Introduction - Environmental sounds and piano
live_loop :intro_ambiance do
  if section == :intro
    with_fx :reverb, room: 0.8 do
      sample street_sounds.choose, rate: 0.5, amp: 0.3
      sleep 8
    end
  else
    sleep 8
  end
end

live_loop :intro_piano do
  if section == :intro
    use_synth :piano
    with_fx :echo, decay: 4 do
      play_pattern_timed scale_pattern, 0.25, release: 0.3, amp: 0.4
    end
    sleep 2
  else
    sleep 2
  end
end

# Dynamic drum patterns by section
live_loop :drums do
  case section
  when :intro
    sample :bd_haus, amp: 0.4
    sleep 1
  when :verse
    sample :bd_haus, amp: 0.6
    sleep 0.5
    sample :drum_cymbal_closed, amp: 0.3
    sleep 0.5
  when :chorus
    sample :bd_haus, amp: 0.8
    sample :sn_dolf, amp: 0.5
    sleep 0.25
    sample :drum_cymbal_closed, amp: 0.4
    sleep 0.25
    sample :bd_haus, amp: 0.6
    sleep 0.25
    sample :drum_cymbal_open, amp: 0.3
    sleep 0.25
  when :bridge
    sample :bd_haus, amp: 0.5
    sleep 0.75
    sample :sn_dolf, amp: 0.4
    sleep 0.25
  when :outro
    sample :bd_haus, amp: 0.3
    sleep 2
  end
end

# Improved bass line with variation
live_loop :bass do
  use_synth :fm
  current_chord = chord_progression.tick
  with_fx :lpf, cutoff: 80 do
    # Play root and fifth for stronger foundation
    play current_chord[0], release: 0.6, amp: 0.6
    sleep 0.75
    play current_chord[2], release: 0.3, amp: 0.4
    sleep 0.25
    play current_chord[0], release: 0.6, amp: 0.6
    sleep 1
  end
end

# Main melody with Cantopop influence and variation
live_loop :lead_melody do
  if [:verse, :chorus, :bridge].include?(section)
    use_synth :prophet
    current_melody = melody_variations.tick
    melody_amp = case section
                when :verse then 0.5
                when :chorus then 0.7
                when :bridge then 0.4
                else 0.5
                end
    
    with_fx :reverb, room: 0.6 do
      play_pattern_timed current_melody, [0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5, 1],
                        attack: 0.1, release: 0.3, amp: melody_amp
    end
    sleep 4
  else
    sleep 4
  end
end

# String section for emotional depth - section specific
live_loop :strings do
  if [:verse, :chorus, :bridge].include?(section)
    use_synth :hollow
    string_amp = case section
                when :verse then 0.3
                when :chorus then 0.5
                when :bridge then 0.4
                else 0.3
                end
    
    with_fx :reverb, room: 0.9 do
      play_chord chord_progression.tick, attack: 1, release: 3, amp: string_amp
      sleep 4
    end
  else
    sleep 4
  end
end

# Traditional Chinese instrument embellishments - section specific
live_loop :chinese_instruments do
  if [:verse, :bridge].include?(section)
    use_synth :sine
    with_fx :ping_pong do
      play erhu_embellishments.choose, release: 0.5, amp: 0.4, pan: rrand(-0.3, 0.3)
      sleep 1
    end
  else
    sleep 1
  end
end

# Arpeggiated synth for space and texture - chorus only
live_loop :arpeggios do
  if section == :chorus
    use_synth :dsaw
    with_fx :wobble, phase: 2 do
      play_pattern_timed chord_progression.tick, 0.125, release: 0.1, amp: 0.2
    end
    sleep 1
  else
    sleep 1
  end
end

# Guzheng patterns for traditional flavor - verse and bridge
live_loop :guzheng do
  if [:verse, :bridge].include?(section)
    use_synth :pluck
    with_fx :echo, decay: 2 do
      play_pattern_timed guzheng_pattern.shuffle, 0.125, amp: 0.3
    end
    sleep 4
  else
    sleep 4
  end
end

# Clear section transitions
live_loop :transitions do
  sync :section_manager
  case section
  when :intro
    sample :bd_boom, amp: 0.5
  when :chorus
    with_fx :reverb, room: 1 do
      sample :glitch_bass_g, amp: 0.3
    end
  when :outro
    with_fx :lpf, cutoff: 60 do
      sample :vinyl_rewind, rate: 0.3, amp: 0.4
    end
  end
end