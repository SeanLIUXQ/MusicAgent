# Generated from audio file: violin_melody_render1.wav
# Music Description: A playful, repetitive melody played on a synthesized square wave, reminiscent of early video game music.

use_synth :square
use_synth_defaults attack: 0.1, release: 0.5, amp: 1.2

melody = [60, 62, 64, 65, 67, 69, 71, 72]

live_loop :game_melody do
  melody.each do |note|
    play note, sustain: 0.25
    sleep 0.25
  end
end