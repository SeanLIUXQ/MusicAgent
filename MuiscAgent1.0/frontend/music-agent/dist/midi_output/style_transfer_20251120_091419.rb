use_synth :piano
use_synth_defaults attack: 0.05, release: 1.2, amp: 0.6

melody_notes = [60, 62, 64, 65, 67, 69, 71, 72]

with_fx :reverb, room: 0.7, mix: 0.3 do
  with_fx :pan, pan: -0.2 do
    live_loop :classical_melody do
      melody_notes.each do |note_value|
        my_amp = 0.5 + rand(0.2)
        play note_value, sustain: 0.5, amp: my_amp, release: 0.1
        sleep 0.5
      end
    end
  end
end

live_loop :harmony do
  use_synth :hollow
  chord_progression = [[48, 52, 55], [50, 53, 57], [52, 55, 59], [53, 57, 60]]
  chord_progression.each do |chord_tones|
    play_chord chord_tones, amp: 0.3, release: 2
    sleep 1.5
    play_chord chord_tones, amp: 0.2, release: 0.5
    sleep 0.5
  end
end

live_loop :conductor do
  cue :beat
  sleep 4
end