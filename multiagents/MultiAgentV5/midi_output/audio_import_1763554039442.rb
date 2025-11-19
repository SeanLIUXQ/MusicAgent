# Generated from audio file: violin_melody_render1.wav
# Music Description: A fast, playful melody played on a synthesized square wave, reminiscent of 8-bit video game music.

use_synth :square
use_synth_defaults attack: 0.05, release: 0.5, sustain: 0.8

# Main melody with a bouncy, repetitive pattern
melody = [
  [:c4, 0.25], [:d4, 0.25], [:e4, 0.25], [:f4, 0.25],
  [:g4, 0.25], [:a4, 0.25], [:b4, 0.25], [:c5, 0.25],
  [:b4, 0.25], [:a4, 0.25], [:g4, 0.25], [:f4, 0.25],
  [:e4, 0.25], [:d4, 0.25], [:c4, 0.25], [:c4, 0.25]
]

# Play the melody in a loop
live_loop :main_melody do
  melody.each do |note, duration|
    play note, release: 0.1
    sleep duration
  end
end