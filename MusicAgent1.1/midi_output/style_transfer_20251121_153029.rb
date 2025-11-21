# Classical Style Transformation
# Converted from Chinese Folk to Classical Orchestral Style

use_bpm 76  # Andante tempo

# Classical scales and harmony
g_major_scale_notes = scale(:g4, :major)
c_major_scale_notes = scale(:c4, :major)

# Classical chord progressions
classical_progression_g = [
  chord(:g4, :M7),    # I
  chord(:c5, :M7),    # IV
  chord(:d5, :dom7),  # V7
  chord(:a4, :m7)     # vi
]

classical_progression_c = [
  chord(:c4, :M7),    # I
  chord(:f4, :M7),    # IV
  chord(:g4, :dom7),  # V7
  chord(:d4, :m7)     # vi
]

# Main melody themes - adapted for classical phrasing
melody_theme_exposition = [
  [:g4, 1], [:a4, 0.5], [:b4, 0.5], [:d5, 2],
  [:c5, 1], [:b4, 0.5], [:a4, 0.5], [:g4, 2],
  [:a4, 1], [:b4, 1], [:d5, 1], [:g5, 1],
  [:d5, 1.5], [:b4, 0.5], [:a4, 2]
]

melody_theme_recapitulation = [
  [:c5, 1], [:d5, 0.5], [:e5, 0.5], [:g5, 2],
  [:f5, 1], [:e5, 0.5], [:d5, 0.5], [:c5, 2],
  [:d5, 1], [:e5, 1], [:g5, 1], [:c6, 1],
  [:g5, 1.5], [:e5, 0.5], [:d5, 2]
]

# Melodic development section
melody_development = [
  [:b4, 0.5], [:d5, 0.5], [:g5, 1], [:d5, 0.5], [:b4, 0.5],
  [:a4, 1], [:g4, 0.5], [:a4, 0.5], [:b4, 2],
  [:c5, 0.5], [:b4, 0.5], [:a4, 1], [:g4, 0.5], [:e4, 0.5],
  [:g4, 2], [:r, 1]
]

# Global dynamic control
set :master_volume, 0.6

# Conductor loop - classical form structure
live_loop :conductor do
  # Exposition - moderate dynamic
  set :master_volume, 0.6
  cue :exposition
  sleep 4
  
  # Development - building intensity
  set :master_volume, 0.8
  cue :development
  sleep 4
  
  # Recapitulation - strong return
  set :master_volume, 0.9
  cue :recapitulation
  sleep 4
  
  # Coda - fading conclusion
  set :master_volume, 0.4
  cue :coda
  sleep 4
end

# 【Exposition】Flute and piano introduction
live_loop :exposition_flute do
  sync :exposition
  use_synth :sine
  with_fx :reverb, room: 0.7 do
    play_pattern_timed [:g5, :a5, :b5, :d6], [4, 4, 4, 4], 
                       amp: 0.5 * get(:master_volume), release: 3.5
  end
end

live_loop :exposition_piano do
  sync :exposition
  use_synth :piano
  with_fx :reverb, room: 0.5 do
    play_chord chord(:g4, :M7), amp: 0.4 * get(:master_volume), release: 4
    sleep 4
    play_chord chord(:c5, :M7), amp: 0.4 * get(:master_volume), release: 4
    sleep 4
    play_chord chord(:d5, :dom7), amp: 0.4 * get(:master_volume), release: 4
    sleep 4
    play_chord chord(:a4, :m7), amp: 0.4 * get(:master_volume), release: 4
  end
end

# 【Exposition】Violin melody
live_loop :violin_melody do
  sync :exposition
  use_synth :saw
  with_fx :reverb, room: 0.6 do
    melody_theme_exposition.each do |note_val, duration_val|
      play note_val, release: duration_val * 0.9, amp: 0.6 * get(:master_volume)
      sleep duration_val
    end
  end
end

# 【Exposition】Harp accompaniment
live_loop :harp_rhythm do
  sync :exposition
  use_synth :pluck
  with_fx :reverb, room: 0.4 do
    16.times do
      play chord(:g3, :major).choose, amp: 0.3 * get(:master_volume), release: 0.2
      sleep 0.5
    end
  end
end

# 【Development】Viola counterpoint
live_loop :viola_counterpoint do
  sync :development
  use_synth :saw
  with_fx :reverb, room: 0.6 do
    melody_development.each do |note_val, duration_val|
      if note_val != :r
        play note_val - 5, release: duration_val * 0.8, amp: 0.5 * get(:master_volume)
      end
      sleep duration_val
    end
  end
end

# 【Development】Cello bass line
live_loop :cello_bass do
  sync :development
  use_synth :sine
  cello_notes_sequence = [:g2, :c2, :d2, :a2]
  cello_notes_sequence.each do |note_val|
    play note_val, amp: 0.4 * get(:master_volume), release: 3.5
    sleep 4
  end
end

# 【Development】Woodwind ornaments
live_loop :oboe_ornament do
  sync :development
  use_synth :beep
  with_fx :reverb, room: 0.6 do
    sleep 2
    play_pattern_timed [:g5, :a5, :g5, :e5], [0.25, 0.25, 0.25, 0.25], 
                       amp: 0.4 * get(:master_volume)
    sleep 4
    play_pattern_timed [:d5, :e5, :d5, :b4], [0.25, 0.25, 0.25, 0.25], 
                       amp: 0.4 * get(:master_volume)
  end
end

# 【Development】Timpani rhythm
live_loop :timpani_rhythm do
  sync :development
  with_fx :reverb, room: 0.3 do
    4.times do |i|
      sample :drum_tom_hi, rate: 0.8, amp: 0.3 * get(:master_volume)
      sleep 1
      sample :drum_tom_mid, rate: 0.7, amp: 0.2 * get(:master_volume)
      sleep 1
    end
  end
end

# 【Development】String section texture
live_loop :string_section do
  sync :development
  use_synth :saw
  with_fx :reverb, room: 0.5 do
    play_chord chord(:g4, :M7), amp: 0.2 * get(:master_volume), release: 4
    sleep 2
    play_chord chord(:c5, :M7), amp: 0.2 * get(:master_volume), release: 4
    sleep 2
    play_chord chord(:d5, :dom7), amp: 0.2 * get(:master_volume), release: 4
    sleep 2
    play_chord chord(:a4, :m7), amp: 0.2 * get(:master_volume), release: 4
    sleep 2
  end
end

# 【Recapitulation】Full orchestra - French horn transition
live_loop :horn_transition do
  sync :recapitulation
  use_synth :prophet
  with_fx :reverb, room: 0.7 do
    play_pattern_timed [:c4, :d4, :e4, :g4, :a4, :b4, :c5, :d5], 
                       [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 4], 
                       amp: 0.5 * get(:master_volume), release: 0.9
  end
end

# 【Recapitulation】Main melody return
live_loop :recapitulation_melody do
  sync :recapitulation
  use_synth :saw
  with_fx :reverb, room: 0.7 do
    melody_theme_recapitulation.each do |note_val, duration_val|
      play note_val, release: duration_val * 0.7, amp: 0.8 * get(:master_volume)
      sleep duration_val
    end
  end
end

# 【Recapitulation】Full harmony
live_loop :recapitulation_harmony do
  sync :recapitulation
  use_synth :prophet
  classical_progression_c.each do |chord_notes|
    play_chord chord_notes, amp: 0.7 * get(:master_volume), release: 3.5
    sleep 4
  end
end

# 【Recapitulation】String pad
live_loop :string_pad do
  sync :recapitulation
  use_synth :sine
  play_chord chord(:c4, :maj9), amp: 0.4 * get(:master_volume), release: 16
  sleep 4
end

# 【Coda】Final statement - piano and flute
live_loop :coda_melody do
  sync :coda
  use_synth :piano
  with_fx :reverb, room: 0.8 do
    play_pattern_timed [:g4, :a4, :b4, :d5], [2, 1, 1, 4], 
                       amp: 0.5 * get(:master_volume), release: 2
    sleep 4
    play_pattern_timed [:c5, :b4, :a4], [1.5, 0.5, 4], 
                       amp: 0.4 * get(:master_volume), release: 2
  end
end

# 【Coda】Flute final note
live_loop :coda_flute do
  sync :coda
  use_synth :sine
  sleep 4
  play :g5, release: 12, amp: 0.3 * get(:master_volume)  # Final sustained note
end

# 【Coda】Final chord resolution
live_loop :coda_resolution do
  sync :coda
  use_synth :piano
  play_chord chord(:g4, :M7), amp: 0.2 * get(:master_volume), release: 10
  sleep 4
end

# Optional MIDI output (disabled by default)
live_loop :midi_output, auto_cue: false do
  use_real_time
  note_val, velocity_val = sync "/midi:*/note_on"
  midi note_val, velocity_val if note_val && velocity_val
end