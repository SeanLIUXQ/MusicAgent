# Tropical Pop House Reggae Fusion
# Improved version with dynamic structure and refined mix

use_bpm 120

# Define musical elements
main_key = :c4
chord_progression = [:c4, :g4, :a4, :f4]
melody_pattern = ring(72, 74, 76, 77, 79, 77, 76, 74)
bass_line_pattern = ring(48, 55, 52, 53)
percussion_rhythm = ring(1, 0, 1, 1, 0, 1, 0, 1)

# Master structure control
live_loop :song_structure do
  # INTRO (16 beats)
  cue :section_intro
  sleep 8
  
  # VERSE (32 beats)
  cue :section_verse
  sleep 8
  
  # CHORUS (32 beats)
  cue :section_chorus
  sleep 8
  
  # BREAKDOWN (16 beats)
  cue :section_breakdown
  sleep 8
  
  # FINAL CHORUS (32 beats)
  cue :section_final_chorus
  sleep 8
  
  # OUTRO (16 beats)
  cue :section_outro
  sleep 8
end

# Ocean sounds for intro and outro
live_loop :ocean_ambience do
  section = get[:current_section] || :section_intro
  if [:section_intro, :section_breakdown, :section_outro].include?(section)
    sample :ambi_soft_buzz, rate: 0.3, amp: 0.4
  else
    sample :ambi_soft_buzz, rate: 0.3, amp: 0.2
  end
  sleep 8
end

# Ukulele - primarily in intro and breakdown
live_loop :ukulele_arpeggio do
  section = sync :section_intro, :section_breakdown
  use_synth :pluck
  with_fx :reverb, mix: 0.4 do
    4.times do
      play_pattern_timed chord_progression, [0.5, 0.5, 0.5, 0.5], amp: 0.8
      sleep 2
    end
  end
end

# Electric piano chords with reggae skank rhythm in verse
live_loop :epiano_chords do
  section = sync :section_verse, :section_chorus, :section_final_chorus
  use_synth :piano
  current_section = get[:current_section]
  
  with_fx :reverb, room: 0.6 do
    8.times do
      if current_section == :section_verse
        # Reggae skank rhythm - chords on off-beats
        sleep 0.5
        play_chord chord(chord_progression.tick, :major7), amp: 0.7, release: 0.3
        sleep 0.5
        play_chord chord(chord_progression.look, :major7), amp: 0.7, release: 0.3
        sleep 0.5
      else
        # Full chords in chorus
        play_chord chord(chord_progression.tick, :major7), amp: 0.6, release: 1.5
        sleep 2
      end
    end
  end
end

# Bass line - simplified and more groovy
live_loop :bass_groove do
  use_synth :fm
  with_fx :lpf, cutoff: 80 do
    4.times do
      play bass_line_pattern.tick, amp: 0.8, release: 0.6
      sleep 0.5
    end
  end
end

# Improved drum pattern with four-on-the-floor house beat
live_loop :drum_beat do
  # Kick on every quarter note (four-on-the-floor)
  sample :bd_haus, amp: 0.9
  # Snare on beats 2 and 4
  sample :sn_dolf, amp: 0.7 if (beat % 2) == 0
  # Closed Hi-hat on every 8th note
  sample :drum_cymbal_closed, amp: 0.4
  sleep 0.5
end

# Latin percussion - more dynamic
live_loop :latin_percussion do
  section = get[:current_section]
  if [:section_chorus, :section_final_chorus].include?(section)
    sample :perc_snap2, amp: 0.4 if percussion_rhythm.tick == 1
    sample :perc_swash, amp: 0.3, rate: 1.2 if spread(3, 8).tick
  else
    sample :perc_snap2, amp: 0.2 if percussion_rhythm.tick == 1
  end
  sleep 0.125
end

# Steel drum accents - primarily in verse
live_loop :steel_drum_accents do
  section = sync :section_verse, :section_breakdown
  use_synth :pretty_bell
  with_fx :reverb, mix: 0.3 do
    16.times do
      play melody_pattern.choose, amp: 0.5, release: 0.5
      sleep 1
    end
  end
end

# Brass melody - only in chorus sections
live_loop :brass_melody do
  section = sync :section_chorus, :section_final_chorus
  use_synth :saw
  2.times do # 2 phrases of 16 beats each
    with_fx :reverb, room: 0.5 do
      play_pattern_timed [72, 76, 79, 81, 79, 76, 72], [0.5, 0.25, 0.25, 0.5, 0.25, 0.25, 0.5], amp: 0.7
      sleep 4
    end
  end
end

# Lead synth - only in chorus sections
live_loop :lead_synth do
  section = sync :section_chorus, :section_final_chorus
  use_synth :prophet
  with_fx :echo, decay: 2 do
    16.times do
      play melody_pattern.tick + 12, amp: 0.6, release: 0.3
      sleep 0.5
    end
  end
end

# Clap rhythm for final chorus only
live_loop :clap_rhythm do
  section = sync :section_final_chorus
  16.times do
    sample :drum_cymbal_closed, amp: 0.6
    sleep 1
  end
end

# Impact hits for section transitions
live_loop :impact_hits do
  section = sync :section_chorus, :section_final_chorus
  sample :drum_roll, rate: 3, amp: 0.5
  sleep 0.1
  sample :drum_splash_hard, amp: 0.7
end

# Master transition effects
live_loop :master_transitions do
  cue_val = sync :section_verse, :section_chorus, :section_breakdown, :section_final_chorus
  set :current_section, cue_val
  
  with_fx :lpf, cutoff: 70 do |ctrl|
    # Sweep the filter open over 2 beats
    16.times do
      control ctrl, cutoff: 70 + (line(0, 50, steps: 16).look)
      sleep 0.125
    end
  end
end

# Section indicator for debugging
live_loop :section_monitor do
  section = sync :section_intro, :section_verse, :section_chorus, :section_breakdown, :section_final_chorus, :section_outro
  set :current_section, section
  puts "Section: #{section}"
end