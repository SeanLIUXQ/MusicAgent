use_bpm 120
use_synth :saw
use_synth_defaults attack: 0.05, release: 0.3, amp: 0.9, cutoff: 80

melody_notes = [60, 62, 64, 65, 67, 69, 71, 72]

with_fx :distortion, distort: 0.6 do
  with_fx :reverb, room: 0.5, mix: 0.3 do
    live_loop :rock_melody do
      melody_notes.each do |midi_note|
        play midi_note, sustain: 0.15
        sleep 0.25
      end
    end
  end
end

live_loop :rock_drums do
  sample :drum_bass_hard, amp: 1.3
  sleep 0.25
  sample :drum_cymbal_closed, amp: 0.6
  sleep 0.25
  sample :drum_snare_hard, amp: 1.1
  sleep 0.25
  sample :drum_cymbal_closed, amp: 0.6
  sleep 0.25
end

live_loop :bass_line do
  sync :rock_drums
  use_synth :prophet
  play 36, amp: 1.2, release: 0.3
  sleep 0.75
  play 38, amp: 1.1, release: 0.2
  sleep 0.25
  play 36, amp: 1.0, release: 0.3
  sleep 1
end

live_loop :guitar_chords do
  sync :rock_drums
  use_synth :hollow
  play_chord chord(:e3, :power), amp: 0.8, release: 0.5
  sleep 2
  play_chord chord(:a3, :power), amp: 0.8, release: 0.5
  sleep 2
end