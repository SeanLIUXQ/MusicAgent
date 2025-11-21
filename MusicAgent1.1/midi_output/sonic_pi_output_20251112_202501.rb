use_bpm 84

live_loop :melody do
  use_synth :piano
  
  # First chord with melody line
  play_pattern_timed [74, 62, 66, 69, 62, 38], [0, 0, 0, 0, 0, 0], 
    amp: [0.56, 0.32, 0.32, 0.32, 0.16, 0.4]
  
  sleep 0.419
  play 66, amp: 0.16
  sleep 0.419
  play 69, amp: 0.16
  sleep 0.558
  play 67, amp: 0.16
  sleep 0.419
  play 71, amp: 0.16
  sleep 0.279
  
  # Second section with higher melody
  play 78, amp: 0.56
  sleep 0.139
  play 74, amp: 0.16
  sleep 0.559
  play 81, amp: 0.56
  play 69, amp: 0.16
  sleep 0.418
  play 73, amp: 0.16
  sleep 0.419
  play 76, amp: 0.16
  sleep 0.559
  
  # Return to opening pattern
  play 78, amp: 0.56
  play 62, amp: 0.16
  sleep 0.418
  play 66, amp: 0.16
  sleep 0.419
  play 69, amp: 0.16
  sleep 0.558
  
  # Chord change and bass shift
  play_pattern_timed [67, 71, 74, 43], [0, 0, 0, 0], 
    amp: [0.32, 0.32, 0.32, 0.4]
  
  # Ascending melody line
  sleep 0.7
  play 79, amp: 0.72
  sleep 1.4
  play 83, amp: 0.72
  sleep 0.7
  play 86, amp: 0.72
  sleep 2.098
  play 83, amp: 0.72
  sleep 0.7
  
  # New chord progression
  play_pattern_timed [69, 73, 76, 45], [0, 0, 0, 0], 
    amp: [0.32, 0.32, 0.32, 0.4]
  
  sleep 0.7
  play 81, amp: 0.8
  sleep 1.4
  play 85, amp: 0.8
  sleep 0.7
  play 88, amp: 0.8
  sleep 1.4
  play 85, amp: 0.8
  sleep 0.7
  
  # Return to opening pattern
  play_pattern_timed [62, 66, 69, 38], [0, 0, 0, 0], 
    amp: [0.32, 0.32, 0.32, 0.4]
  
  sleep 0.7
  play 78, amp: 0.64
  sleep 2.098
  play 81, amp: 0.64
  sleep 0.7
  play 74, amp: 0.64
  sleep 2.098
  play 78, amp: 0.64
  sleep 0.7
end