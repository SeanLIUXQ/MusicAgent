use_bpm 70

# Enhanced musical elements with variations
morin_khuur_melodies = [
  ring(:d4, :f4, :a4, :d5, :a4, :f4, :d4, :r),
  ring(:d4, :f4, :g4, :bb4, :a4, :f4, :d4, :c4),
  ring(:d4, :f4, :a4, :c5, :d5, :a4, :f4, :d4)
]

flute_melodies = [
  ring(:a4, :c5, :d5, :f5, :d5, :c5, :a4, :r),
  ring(:g4, :bb4, :c5, :eb5, :c5, :bb4, :g4, :f4),
  ring(:a4, :c5, :e5, :g5, :f5, :d5, :c5, :a4)
]

# Enhanced chord progressions
guitar_chord_sets = [
  ring([:d3, :a3, :d4], [:f3, :c4, :f4], [:a3, :e4, :a4], [:c4, :g4, :c5]),
  ring([:d3, :f3, :a3], [:g3, :bb3, :d4], [:f3, :a3, :c4], [:bb3, :d4, :f4]),
  ring([:d3, :a3, :d4], [:g3, :d4, :g4], [:c4, :g4, :c5], [:f3, :c4, :f4])
]

# Enhanced drum patterns with variation
drum_patterns = [
  ring(1, 0, 0.3, 0, 0.5, 0, 0.2, 0),
  ring(0.8, 0, 0.5, 0, 0.3, 0.2, 0, 0),
  ring(1, 0.2, 0, 0.5, 0, 0, 0.3, 0)
]

# Ambient pad with harmonic development
ambient_pad_progressions = [
  ring(:d2, :a2, :f2, :c3),
  ring(:g2, :d3, :bb2, :f3),
  ring(:d2, :g2, :c3, :f3)
]

# Environmental sounds
define :play_wind do
  with_fx :reverb, mix: 0.8 do
    with_fx :lpf, cutoff: rrand(50, 70) do
      sample :ambi_soft_buzz, rate: rrand(0.2, 0.4), amp: rrand(0.2, 0.4), attack: 2, release: 4
      sleep 8
    end
  end
end

define :play_horse_steps do
  with_fx :reverb, mix: 0.4 do
    sample :drum_tom_lo_soft, rate: rrand(0.4, 0.6), amp: rrand(0.15, 0.25), pan: -0.5
    sleep rrand(1.8, 2.2)
    sample :drum_tom_lo_soft, rate: rrand(0.4, 0.6), amp: rrand(0.15, 0.25), pan: 0.5
    sleep rrand(1.8, 2.2)
  end
end

# Enhanced morin khuur with variation and counter-melody
live_loop :morin_khuur, sync: :dynamic_structure do
  use_synth :hollow
  melody_idx = (tick(:morin_melody) % 48) / 16
  current_melody = morin_khuur_melodies[melody_idx % morin_khuur_melodies.size]
  
  with_fx :reverb, room: 0.8, mix: 0.6 do
    with_fx :echo, phase: [0.75, 1, 1.25].choose, decay: 4 do
      note_val = current_melody.tick(:morin_notes)
      unless note_val == :r
        play note_val, pan: rrand(-0.4, -0.2), amp: rrand(0.7, 0.9), attack: rrand(0.08, 0.12), release: rrand(0.25, 0.35)
        sleep 0.5
      else
        sleep 0.5
      end
    end
  end
end

# Enhanced flute with variation and spatial movement
live_loop :flute, sync: :dynamic_structure do
  use_synth :blade
  melody_idx = (tick(:flute_melody) % 48) / 16
  current_melody = flute_melodies[melody_idx % flute_melodies.size]
  
  with_fx :reverb, room: 0.9, mix: 0.7 do
    with_fx :pan, pan: rrand(-0.9, -0.7), pan_slide: 2 do
      note_val = current_melody.tick(:flute_notes)
      unless note_val == :r
        play note_val, amp: rrand(0.5, 0.7), attack: rrand(0.04, 0.06), release: rrand(0.18, 0.22)
        sleep 0.5
      else
        sleep 0.5
      end
    end
  end
end

# Enhanced fingerstyle guitar with harmonic variation
live_loop :guitar, sync: :dynamic_structure do
  use_synth :pluck
  chord_idx = (tick(:guitar_chords) % 48) / 16
  current_chords = guitar_chord_sets[chord_idx % guitar_chord_sets.size]
  
  with_fx :reverb, room: 0.6, mix: 0.4 do
    chord_notes = current_chords.tick(:guitar_progression)
    chord_notes.each do |note|
      play note, release: rrand(1.3, 1.7), amp: rrand(0.35, 0.45)
      sleep 0.25
    end
  end
end

# Enhanced hand drum with authentic percussion variation
live_loop :hand_drum, sync: :dynamic_structure do
  pattern_idx = (tick(:drum_pattern) % 48) / 16
  current_pattern = drum_patterns[pattern_idx % drum_patterns.size]
  
  with_fx :reverb, room: 0.4, mix: 0.3 do
    hit_strength = current_pattern.tick(:drum_hits)
    if hit_strength > 0
      drum_sample = [:drum_tabla_tas1, :drum_tabla_tas3, :drum_tabla_na].choose
      sample drum_sample, rate: rrand(0.7, 0.9), amp: hit_strength * rrand(0.25, 0.35)
    end
    sleep 0.5
  end
end

# Enhanced ambient pad with harmonic development
live_loop :ambient_pad, sync: :dynamic_structure do
  use_synth :dark_ambience
  pad_idx = (tick(:pad_progression) % 48) / 16
  current_pad = ambient_pad_progressions[pad_idx % ambient_pad_progressions.size]
  
  with_fx :reverb, room: 1.0, mix: 0.8 do
    with_fx :lpf, cutoff: rrand(60, 80) do
      play current_pad.tick(:pad_notes), sustain: 6, amp: rrand(0.25, 0.35), attack: rrand(1.8, 2.2), release: rrand(3.8, 4.2)
      sleep 8
    end
  end
end

# Improved environmental elements with better timing
live_loop :environment, sync: :dynamic_structure do
  if one_in(3)
    play_wind
  end
  if (tick(:horse_steps) % 8) == 0
    play_horse_steps
  end
  sleep 4
end

# Enhanced dynamic structure with smooth transitions
live_loop :dynamic_structure do
  # Intro section - sparse and atmospheric
  section_duration = 16
  control :guitar, amp: 0.2, amp_slide: 2
  control :hand_drum, amp: 0.1, amp_slide: 2
  control :ambient_pad, amp: 0.2, amp_slide: 2
  control :morin_khuur, amp: 0.7, amp_slide: 2
  control :flute, amp: 0.4, amp_slide: 2
  sleep section_duration
  
  # Build up section
  control :guitar, amp: 0.4, amp_slide: 4
  control :hand_drum, amp: 0.4, amp_slide: 4
  control :ambient_pad, amp: 0.3, amp_slide: 4
  sleep section_duration
  
  # Main section A
  control :flute, amp: 0.8, amp_slide: 2
  control :morin_khuur, amp: 0.9, amp_slide: 2
  control :hand_drum, amp: 0.5, amp_slide: 2
  sleep section_duration * 2
  
  # Variation section B
  control :guitar, amp: 0.3, amp_slide: 4
  control :hand_drum, amp: 0.6, amp_slide: 4
  control :flute, amp: 0.6, amp_slide: 4
  control :morin_khuur, amp: 0.8, amp_slide: 4
  sleep section_duration * 2
  
  # Return to main section A'
  control :flute, amp: 0.9, amp_slide: 3
  control :morin_khuur, amp: 0.95, amp_slide: 3
  control :guitar, amp: 0.4, amp_slide: 3
  sleep section_duration * 2
  
  # Outro - gradual fade with smooth transitions
  fade_steps = 20
  fade_steps.times do |step|
    fade_factor = (fade_steps - step).to_f / fade_steps
    control :morin_khuur, amp: fade_factor * 0.8, amp_slide: 1
    control :flute, amp: fade_factor * 0.7, amp_slide: 1
    control :guitar, amp: fade_factor * 0.4, amp_slide: 1
    control :hand_drum, amp: fade_factor * 0.3, amp_slide: 1
    control :ambient_pad, amp: fade_factor * 0.2, amp_slide: 1
    sleep 2
  end
  
  # Final silence
  control :morin_khuur, amp: 0
  control :flute, amp: 0
  control :guitar, amp: 0
  control :hand_drum, amp: 0
  control :ambient_pad, amp: 0
  sleep 4
end