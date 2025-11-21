use_bpm 120

# Global section variable for song structure
section = :intro

# Define musical elements
chord_progression = [:c3, :g3, :a3, :f3].ring
melody_pattern = [:c4, :e4, :g4, :e4, :c4, :d4, :f4, :d4].ring
bass_notes = [:c2, :g2, :a2, :f2].ring
drum_kick = [1, 0, 0, 0, 1, 0, 0, 0].ring
drum_snare = [0, 0, 1, 0, 0, 0, 1, 0].ring
drum_hihat = [1, 1, 1, 1, 1, 1, 1, 1].ring

# Conductor loop to manage song structure
live_loop :conductor do
  sleep 8
  section = case section
            when :intro then :verse
            when :verse then :chorus
            when :chorus then :breakdown
            when :breakdown then :verse
            else :intro
            end
  puts "Moving to section: #{section}"
end

# Clock loop to keep chord progression synchronized
live_loop :chord_clock do
  chord_progression.tick
  sleep 4
end

# Main drum loop with section-based variation
live_loop :drums do
  case section
  when :intro, :verse
    # Simpler drums for intro and verse
    8.times do
      sample :bd_haus, amp: 2 if drum_kick.tick == 1
      sample :sn_dolf, amp: 1.5 if drum_snare.look == 1
      sample :drum_cymbal_closed, amp: 0.6, rate: 1.2 if drum_hihat.look == 1
      sleep 0.5
    end
  when :chorus
    # More energetic drums for chorus
    8.times do
      sample :bd_haus, amp: 2.5 if drum_kick.tick == 1
      sample :sn_dolf, amp: 1.8 if drum_snare.look == 1
      sample :drum_cymbal_closed, amp: 0.9, rate: 1.2
      sleep 0.25
    end
  when :breakdown
    # Minimal drums for breakdown
    4.times do
      sample :bd_haus, amp: 1.5
      sleep 1
      sample :sn_dolf, amp: 1
      sleep 1
    end
  end
end

# Bass line with improved filtering
live_loop :bass do
  use_synth :fm
  with_fx :lpf, cutoff: 110 do
    4.times do
      play bass_notes.tick, release: 0.3, amp: 1.2
      sleep 1
    end
  end
end

# Electric piano chords with section-based variation
live_loop :chords do
  use_synth :piano
  with_fx :reverb, room: 0.3 do
    case section
    when :intro, :verse
      play_chord chord(chord_progression.look, :major), amp: 0.6, release: 1.5
    when :chorus
      play_chord chord(chord_progression.look, :major), amp: 1.0, release: 2
    when :breakdown
      play_chord chord(chord_progression.look, :major), amp: 0.4, release: 3
    end
    sleep 2
  end
end

# Funky guitar with conditional effects
live_loop :guitar do
  use_synth :pluck
  case section
  when :intro, :verse
    with_fx :wobble, phase: 0.5, mix: 0.3 do
      8.times do
        play melody_pattern.tick, amp: 0.5, release: 0.2
        sleep 0.5
      end
    end
  when :chorus
    with_fx :wobble, phase: 0.25, mix: 0.6 do
      8.times do
        play melody_pattern.tick, amp: 0.8, release: 0.3
        sleep 0.5
      end
    end
  when :breakdown
    # No guitar in breakdown
    sleep 4
  end
end

# Arpeggiator that follows chord progression
live_loop :arpeggio do
  use_synth :prophet
  if section == :chorus || section == :breakdown
    current_chord_root = chord_progression.look + 12
    with_fx :slicer, phase: 0.25 do
      play_pattern_timed chord(current_chord_root, :major), [0.25, 0.25, 0.25, 0.25], amp: 0.4, release: 0.1
    end
  end
  sleep 1
end

# Shaker only in energetic sections
live_loop :shaker do
  if section == :chorus
    sample :perc_snap2, rate: 2, amp: 0.3
  end
  sleep 0.25
end

# Pad for atmosphere, only in specific sections
live_loop :pad do
  use_synth :hollow
  with_fx :reverb, mix: 0.7 do
    if section == :chorus || section == :breakdown
      current_chord_root = chord_progression.look
      play_chord chord(current_chord_root, :maj7), attack: 2, release: 6, amp: 0.4
    end
  end
  sleep 8
end