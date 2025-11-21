```ruby
# Late Romantic Classical Music with Impressionist Influences
# Inspired by Debussy, Rachmaninoff, and Mahler
# Improved version with better timing, transitions, and musical development

use_bpm 60  # Starting tempo (Più lento)

# Master timing system
$section_timer = 0
$current_section = :intro

# Master timing loop
live_loop :master_timer do
  $section_timer += 1
  
  # Update current section
  $current_section = case $section_timer
    when 0...90 then :intro
    when 90...240 then :exposition
    when 240...450 then :development
    when 450...540 then :climax
    when 540...690 then :recapitulation
    else :coda
  end
  
  sleep 1
end

# Define musical scales and chords
c_minor_scale = (scale :c, :minor)
eb_major_scale = (scale :eb, :major)
g_minor_scale = (scale :g, :minor)
f_minor_scale = (scale :f, :minor)
ab_major_scale = (scale :ab, :major)
c_major_scale = (scale :c, :major)
db_major_scale = (scale :db, :major)

# Main melodic motifs
descending_motif = [:c4, :bb3, :ab3]
fourth_leap = [:c4, :f4]
chromatic_rise = [:c4, :cs4, :d4, :eb4]

# Extended chords for harmonic richness with chromatic mixture
extended_chords = [
  chord(:c, :minor9),    # Cm9
  chord(:eb, :maj9),     # Ebmaj9
  chord(:g, :minor11),   # Gm11
  chord(:f, :minor7),    # Fm7
  chord(:ab, :maj7),     # Abmaj7
  chord(:c, :maj9),      # Cmaj9
  chord(:db, :maj7),     # Dbmaj7 (chromatic)
  chord(:e, :dim7)       # Edim7 (passing chord)
]

# Expressive performance functions
define :espressivo do |amp_val=1.0|
  with_fx :vowel, voice: 0.3 do
    with_fx :vibrato, rate: 6, depth: 0.1 do
      yield amp_val
    end
  end
end

define :dolce do |amp_val=1.0|
  with_fx :reverb, mix: 0.4, room: 0.6 do
    with_fx :lpf, cutoff: 90 do
      yield amp_val
    end
  end
end

# Strings section - violins, violas, cellos, basses
live_loop :strings_pad do
  use_synth :hollow
  use_octave -2
  
  current_time = $section_timer
  
  case $current_section
  when :intro
    # Intro - soft sustained strings with gradual entrance
    with_fx :reverb, mix: 0.8, room: 0.9 do
      if current_time < 30
        # Very soft beginning
        play_chord chord(:c, :m7), attack: 4, release: 8, amp: 0.15
      else
        # Building slightly
        play_chord chord(:c, :m7), attack: 4, release: 8, amp: 0.25 + (current_time * 0.002)
      end
      sleep 8
    end
    
  when :exposition
    # Exposition - supporting harmony with varied rhythm
    with_fx :reverb, mix: 0.7 do
      chord_progression = [
        chord(:c, :m9), chord(:eb, :maj9), 
        chord(:g, :m11), chord(:db, :maj7), chord(:f, :m7)
      ]
      durations = [6, 5, 4, 3, 6]  # Varied harmonic rhythm
      
      chord_progression.zip(durations).each do |current_chord, dur|
        dynamic_amp = 0.3 + (rand * 0.1)  # Subtle dynamic variation
        play_chord current_chord, attack: 1.5, release: dur - 1, amp: dynamic_amp
        sleep dur
      end
    end
    
  when :development
    # Development - building intensity with faster harmonic rhythm
    with_fx :reverb, mix: 0.6 do
      chord_progression = [
        chord(:g, :m11), chord(:bb, :maj7), 
        chord(:f, :m9), chord(:db, :maj7), chord(:ab, :maj7), chord(:c, :maj9)
      ]
      
      # Gradual crescendo through development
      development_progress = (current_time - 240).to_f / 210  # 0 to 1
      base_amp = 0.4 + (development_progress * 0.3)
      
      chord_progression.each do |current_chord|
        play_chord current_chord, attack: 0.8, release: 3.5, amp: base_amp + (rand * 0.1)
        sleep 4  # Faster harmonic rhythm
      end
    end
    
  when :climax
    # Extended climax - full intensity with dramatic progression
    with_fx :reverb, mix: 0.3 do
      climax_chords = [
        chord(:c, :maj9), chord(:g, :dom7), chord(:f, :maj7), 
        chord(:ab, :maj7), chord(:c, :maj9), chord(:eb, :maj9)
      ]
      
      climax_chords.each_with_index do |chord, idx|
        # Slight dynamic shaping within climax
        chord_amp = idx == 2 ? 1.1 : 0.9  # Emphasize middle chord
        play_chord chord, attack: 0.3, release: 3.5, amp: chord_amp
        sleep 5
      end
    end
    
  when :recapitulation
    # Recapitulation - returning themes with variation
    with_fx :reverb, mix: 0.7 do
      # Gradual decrescendo through recapitulation
      recap_progress = (current_time - 540).to_f / 150
      dynamic_level = 0.6 - (recap_progress * 0.3)
      
      varied_chords = [chord(:c, :m9), chord(:eb, :maj7), chord(:g, :m11), chord(:f, :m7)]
      varied_chords.each do |current_chord|
        play_chord current_chord, attack: 2, release: 5, amp: dynamic_level + (rand * 0.1)
        sleep 7
      end
    end
    
  when :coda
    # Coda - fading out with resolution
    with_fx :reverb, mix: 0.9, room: 1.0 do
      coda_chords = [chord(:c, :maj7), chord(:f, :maj7), chord(:c, :maj9)]
      fade_factor = [(690 - current_time).to_f / 60, 0.1].max  # Gradual fade
      
      coda_chords.each do |current_chord|
        play_chord current_chord, attack: 3, release: 8, amp: 0.15 * fade_factor
        sleep 8
      end
    end
  end
end

# Transition and build-up elements
live_loop :string_crescendo do
  sync_bpm :beat
  
  # Only activate during specific transition points
  transition_points = [85, 235, 445, 535]
  current_time = $section_timer
  
  if transition_points.include?(current_time)
    use_synth :hollow
    
    # Gradual crescendo over 8 beats
    8.times do |i|
      crescendo_amp = 0.2 + (i * 0.08)
      play_chord chord(:c, :m7), amp: crescendo_amp, attack: 0.3, release: 0.8
      sleep 1
    end
  else
    sleep 4
  end
end

# Harp arpeggios - introduction and transitions with more variety
live_loop :harp_arpeggios do
  use_synth :pluck
  use_octave 3
  
  current_time = $section_timer
  
  case $current_section
  when :intro
    # Intro arpeggios with varied patterns
    with_fx :reverb, mix: 0.6 do
      arp_patterns = [
        c_minor_scale.take(7).reverse,
        descending_motif + fourth_leap,
        c_minor_scale.take(5).shuffle
      ].ring
      
      current_arp = arp_patterns.tick
      timing_pattern = case current_arp.length
        when 7 then [0.25, 0.2, 0.3, 0.2, 0.25, 0.3, 0.4]
        when 4 then [0.3, 0.3, 0.3, 0.5]
        else [0.2, 0.25, 0.3, 0.25, 0.4]
      end
      
      play_pattern_timed current_arp, timing_pattern, amp: 0.3 + (rand * 0.1)
      sleep 6
    end
    
  when :development
    # Development transition with more activity
    if current_time.between?(240, 270)
      with_fx :reverb, mix: 0.5 do
        # Alternating patterns
        patterns = [chromatic_rise, [:eb4, :f4, :fs4, :g4]].ring
        current_pattern = patterns.tick
        
        play_pattern_timed current_pattern, [0.15, 0.12, 0.18, 0.2], amp: 0.4
        sleep 1.5
      end
    else
      sleep 8
    end
    
  when :coda
    # Coda arpeggios with major resolution
    with_fx :reverb, mix: 0.8 do
      major_arpeggios = [
        c_major_scale.take(5),
        [:c4, :e4, :g4, :c5],
        [:g3, :b3, :d4, :g4]
      ].ring
      
      current_arpeggio = major_arpeggios.tick
      play_pattern_timed current_arpeggio, [0.5, 0.4, 0.6, 0.5].take(current_arpeggio.length), 
                         amp: 0.25 - (current_time * 0.0002)  # Gradual fade
      sleep 8
    end
    
  else
    sleep 8
  end
end

# Cello melody - first theme with dynamic shaping
live_loop :cello_theme do
  use_synth :prophet
  use_octave 2
  
  current_time = $section_timer
  
  case $current_section
  when :exposition
    # First theme - lyrical cello melody with expression
    if current_time >= 105  # Delayed entrance for textural variety
      espressivo do |amp_base|
        melody_notes = [:c3, :eb3, :g3, :f3, :eb3, :c3, :bb2, :c3]
        rhythm_pattern = [1.5, 0.5, 1, 1, 0.5, 1, 1, 2]
        
        melody_notes.zip(rhythm_pattern).each_with_index do |(note, duration), i|
          # Dynamic shaping: crescendo on ascent, diminuendo on descent
          phrase_amp = i < 4 ? amp_base + (i * 0.03) : amp_base + 0.1 - ((i-4) * 0.025)
          play note, attack: 0.1, release: duration * 0.8, amp: phrase_amp * 0.7
          sleep duration
        end
      end
    else
      sleep 8
    end
    
  when :recapitulation
    # Theme return with variation and ornamentation
    dolce do |amp_base|
      varied_melody = [:c3, :eb3, :g3, :bb3, :ab3, :g3, :f3, :eb3, :d3, :c3]
      rhythm_variation = [1, 0.5, 0.5, 0.75, 0.25, 0.5, 0.5, 1, 0.5, 1.5]
      
      varied_melody.zip(rhythm_variation).each do |note, duration|
        # Softer dynamic in recapitulation
        play note, attack: 0.2, release: duration * 0.9, amp: amp_base * 0.6
        sleep duration
      end
    end
    
  else
    sleep 8
  end
end

# Woodwinds - second theme and dialogue with staggered entrance
live_loop :woodwinds do
  use_synth :sine
  use_octave 4
  
  current_time = $section_timer
  
  if $current_section == :exposition && current_time >= 135  # Delayed entrance
    # Second theme - woodwind dialogue with expression
    with_fx :reverb, mix: 0.3 do
      # Flute/Oboe line with dynamic shaping
      woodwind_melody = [:eb4, :f4, :g4, :ab4, :bb4, :ab4, :g4, :f4]
      espressivo do |amp_base|
        play_pattern_timed woodwind_melody, [0.5, 0.4, 0.6, 0.5, 0.7, 0.4, 0.5, 0.6], 
                           amp: amp_base * 0.45, attack: 0.05, release: 0.3
      end
      sleep 4
      
      # Response phrase with variation
      response_patterns = [
        [:g4, :ab4, :bb4, :c5, :bb4, :ab4],
        [:f4, :g4, :ab4, :bb4, :c5, :eb5, :c5]
      ].ring
      
      current_response = response_patterns.tick
      response_timing = current_response.length == 6 ? [0.4, 0.4, 0.6, 0.3, 0.4, 0.5] : [0.3, 0.3, 0.4, 0.5, 0.4, 0.6, 0.5]
      
      play_pattern_timed current_response, response_timing, amp: 0.4, attack: 0.05, release: 0.3
      sleep 6
    end
  elsif $current_section == :development
    # More active woodwinds in development
    if current_time.between?(300, 420)
      with_fx :reverb, mix: 0.4 do
        development_figures = [
          [:g4, :a4, :bb4, :c5, :d5, :eb5],
          [:f4, :g4, :a4, :bb4, :c5, :d5]
        ].ring
        
        current_figure = development_figures.tick
        play_pattern_timed current_figure, [0.3, 0.3, 0.4, 0.3, 0.4, 0.5], 
                           amp: 0.35, attack: 0.03, release: 0.2
        sleep 4
      end
    else
      sleep 8
    end
  else
    sleep 8
  end
end

# Woodwind response to cello theme
live_loop :woodwind_response do
  sync_bpm :beat
  
  # Only respond during appropriate sections
  if [$current_section == :exposition, $current_section == :recapitulation].any?
    use_synth :sine
    
    # Random chance to respond (creates more natural dialogue)
    if rand < 0.3
      response_melodies = [
        [:g4, :ab4, :bb4, :c5, :eb5, :c5],
        [:f4, :g4, :ab4, :bb4, :c5, :eb5, :d5, :c5],
        [:eb4, :f4, :g4, :ab4, :g4, :f4]
      ].ring
      
      current_response = response_melodies.tick
      timing_pattern = case current_response.length
        when 6 then [0.4, 0.4, 0.6, 0.3, 0.7, 0.5]
        when 8 then [0.3, 0.3, 0.4, 0.5, 0.4, 0.6, 0.4, 0.5]
        else [0.5, 0.4, 0.6, 0.5, 0.4, 0.6]
      end
      
      with_fx :reverb, mix: 0.2 do
        play_pattern_timed current_response, timing_pattern, amp: 0.25, attack: 0.05, release: 0.4
      end
    end
  end