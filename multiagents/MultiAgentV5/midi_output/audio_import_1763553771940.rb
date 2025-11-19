# Generated from audio file: violin_melody_render1.wav
# Music Description: A fast, playful, and repetitive melody played on a synthesized square wave, reminiscent of 8-bit video game music.

use_synth :square
use_synth_defaults attack: 0.05, release: 0.1, amp: 1.2

# Main melody with a bouncy, staccato feel
melody = [
  :c4, :d4, :e4, :f4, :g4, :a4, :b4, :c5,
  :b4, :a4, :g4, :f4, :e4, :d4, :c4, :b3,
  :c4, :d4, :e4, :f4, :g4, :a4, :b4, :c5,
  :b4, :a4, :g4, :f4, :e4, :d4, :c4, :b3
]

# Play the melody with short notes and slight rests for rhythm
melody.each_with_index do |note, i|
  play note, release: 0.1
  sleep 0.125
  if i % 4 == 3
    sleep 0.0625 # slight rest every 4th note
  end
end