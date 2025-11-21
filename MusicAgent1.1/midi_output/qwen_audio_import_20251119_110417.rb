use_synth :square
use_synth_defaults sustain: 0.1, release: 0.1

# Main melody with a slightly unsettling feel
melody = [:c4, :d4, :e4, :f4, :g4, :a4, :b4, :c5]

# Play the melody in a loop with a simple rhythmic pattern
live_loop :melody do
  melody.each do |note|
    play note, amp: 0.8
    sleep 0.25
  end
end