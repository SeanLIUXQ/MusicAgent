# 中国北方革命民歌风格作品 - 改进版
# 陕甘宁边区传统民歌音乐语汇

use_bpm 76  # 行板速度

# 调式定义
gong_scale = scale(:g4, :major_pentatonic)  # G宫调式
zhi_scale = scale(:c4, :major_pentatonic)   # C徵调式

# 民族和声进行
harmony_progression_gong = [
  chord_degree(:i, :g4, :major_pentatonic, 3),   # G宫主和弦
  chord_degree(:iv, :g4, :major_pentatonic, 3),  # C角和弦
  chord_degree(:v, :g4, :major_pentatonic, 3),   # D徵和弦
  chord_degree(:ii, :g4, :major_pentatonic, 3)   # A羽和弦
]

harmony_progression_zhi = [
  chord_degree(:i, :c4, :major_pentatonic, 3),   # C徵主和弦
  chord_degree(:iv, :c4, :major_pentatonic, 3),  # F宫和弦
  chord_degree(:v, :c4, :major_pentatonic, 3),   # G商和弦
  chord_degree(:ii, :c4, :major_pentatonic, 3)   # D羽和弦
]

# 主旋律主题 - 板胡奏出完整民歌旋律
melody_theme_gong = [
  [:g4, 1], [:a4, 0.5], [:b4, 0.5], [:d5, 2],
  [:c5, 1], [:b4, 0.5], [:a4, 0.5], [:g4, 2],
  [:a4, 1], [:b4, 1], [:d5, 1], [:g5, 1],
  [:d5, 1.5], [:b4, 0.5], [:a4, 2]
]

melody_theme_zhi = [
  [:c5, 1], [:d5, 0.5], [:e5, 0.5], [:g5, 2],
  [:f5, 1], [:e5, 0.5], [:d5, 0.5], [:c5, 2],
  [:d5, 1], [:e5, 1], [:g5, 1], [:c6, 1],
  [:g5, 1.5], [:e5, 0.5], [:d5, 2]
]

# 旋律变奏发展
melody_variation = [
  [:b4, 0.5], [:d5, 0.5], [:g5, 1], [:d5, 0.5], [:b4, 0.5],
  [:a4, 1], [:g4, 0.5], [:a4, 0.5], [:b4, 2],
  [:c5, 0.5], [:b4, 0.5], [:a4, 1], [:g4, 0.5], [:e4, 0.5],
  [:g4, 2], [:r, 1]
]

# 全局动态控制变量
set :master_amp, 0.6

# 主控时序循环 - 替换所有sleep语句
live_loop :conductor do
  # 引子部分 - 较安静
  set :master_amp, 0.5
  cue :intro
  sleep 4
  
  # 第一段 - 主题呈示，稍强
  set :master_amp, 0.7
  cue :verse_1
  sleep 4
  
  # 第二段 - 发展段，继续增强
  set :master_amp, 0.8
  cue :verse_2
  sleep 4
  
  # 过渡段 - 准备高潮
  set :master_amp, 0.9
  cue :transition
  sleep 4
  
  # 高潮段 - 最强动态
  set :master_amp, 1.0
  cue :climax
  sleep 4
  
  # 尾声 - 逐渐减弱
  set :master_amp, 0.6
  cue :coda
  sleep 4
  
  # 结束 - 非常安静
  set :master_amp, 0.3
  cue :end
  sleep 4
end

# 【引子】竹笛悠远长音引入
live_loop :intro_dizi do
  sync :intro
  use_synth :hollow
  with_fx :reverb, mix: 0.8 do
    play_pattern_timed [:g5, :a5, :b5, :d6], [4, 4, 4, 4], amp: 0.4 * get(:master_amp)
  end
end

live_loop :intro_yangqin do
  sync :intro
  use_synth :pluck
  with_fx :echo, decay: 8 do
    play_chord chord(:g4, :maj7), amp: 0.3 * get(:master_amp), release: 4
    sleep 4
    play_chord chord(:c4, :maj7), amp: 0.3 * get(:master_amp), release: 4
    sleep 4
    play_chord chord(:d4, :sus4), amp: 0.3 * get(:master_amp), release: 4
    sleep 4
    play_chord chord(:a4, :min7), amp: 0.3 * get(:master_amp), release: 4
  end
end

# 【第一段】主题呈示部 - 改进音色
live_loop :banhu_melody do
  sync :verse_1
  use_synth :blade
  with_fx :vibrato, rate: 4, depth: 0.05 do
    melody_theme_gong.each do |note_val, duration_val|
      play note_val, release: duration_val * 0.8, amp: 0.6 * get(:master_amp), cutoff: 90
      sleep duration_val
    end
  end
end

live_loop :pipa_rhythm do
  sync :verse_1
  use_synth :pluck
  with_fx :lpf, cutoff: 80 do
    16.times do
      play chord(:g3, :major).choose, amp: 0.2 * get(:master_amp), release: 0.1
      sleep 0.5
    end
  end
end

# 【第二段】旋律变奏发展 - 增加低音和打击乐
live_loop :erhu_counterpoint do
  sync :verse_2
  use_synth :blade
  with_fx :vibrato, rate: 4, depth: 0.05 do
    melody_variation.each do |note_val, duration_val|
      if note_val != :r
        play note_val - 5, release: duration_val * 0.7, amp: 0.5 * get(:master_amp), cutoff: 85
      end
      sleep duration_val
    end
  end
end

live_loop :bass_line do
  sync :verse_2
  use_synth :sine
  bass_notes = [:g2, :c2, :d2, :a2]
  bass_notes.each do |note_val|
    play note_val, amp: 0.3 * get(:master_amp), release: 3.5
    sleep 4
  end
end

live_loop :percussion_shaker do
  sync :verse_2
  32.times do
    sample :perc_snap2, rate: 1.5, amp: 0.1 * get(:master_amp) if spread(7, 8).tick
    sleep 0.5
  end
end

live_loop :dizi_ornament do
  sync :verse_2
  use_synth :fm
  with_fx :reverb, room: 0.7 do
    sleep 2
    play_pattern_timed [:g5, :a5, :g5, :e5], [0.25, 0.25, 0.25, 0.25], amp: 0.3 * get(:master_amp)
    sleep 4
    play_pattern_timed [:d5, :e5, :d5, :b4], [0.25, 0.25, 0.25, 0.25], amp: 0.3 * get(:master_amp)
  end
end

# 【过渡段】调性转换准备 - 增强过渡效果
live_loop :transition_sheng do
  sync :transition
  use_synth :hollow
  with_fx :echo, decay: 6 do
    with_fx :band_eq, freq: 800, res: 0.5, db: 6 do
      play_pattern_timed [:c4, :d4, :e4, :g4, :a4, :b4, :c5, :d5], 
                         [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 4], 
                         amp: 0.4 * get(:master_amp), release: 0.8
    end
  end
end

live_loop :transition_drums do
  sync :transition
  with_fx :lpf, cutoff: 90 do
    4.times do |i|
      sample :drum_tabla_te2, rate: 0.8 + (i * 0.1), amp: 0.4 * get(:master_amp)
      sleep 1
      sample :drum_tabla_te1, rate: 0.9 + (i * 0.1), amp: 0.3 * get(:master_amp)
      sleep 1
    end
  end
end

# 【高潮段】全乐队齐奏主题 - 转调到C徵调式
live_loop :climax_melody do
  sync :climax
  use_synth :blade
  use_octave 0
  with_fx :vibrato, rate: 5, depth: 0.08 do
    melody_theme_zhi.each do |note_val, duration_val|
      play note_val, release: duration_val * 0.6, amp: 0.8 * get(:master_amp), cutoff: 95
      sleep duration_val
    end
  end
end

live_loop :climax_rhythm do
  sync :climax
  with_fx :hpf, cutoff: 60 do
    4.times do
      sample :drum_tabla_te3, rate: 0.7, amp: 0.4 * get(:master_amp)
      sleep 1
      3.times do
        sample :drum_tabla_na, rate: 0.8, amp: 0.3 * get(:master_amp)
        sleep 0.5
      end
    end
  end
end

live_loop :climax_harmony do
  sync :climax
  use_synth :prophet
  harmony_progression_zhi.each do |chord_notes|
    play_chord chord_notes, amp: 0.6 * get(:master_amp), release: 3.5, cutoff: 80
    sleep 4
  end
end

live_loop :climax_pad do
  sync :climax
  use_synth :hollow
  play_chord chord(:c4, :maj9), amp: 0.3 * get(:master_amp), release: 16
  sleep 4
end

# 【尾声】主题片段再现 - 逐渐减弱
live_loop :coda_melody do
  sync :coda
  use_synth :sine
  with_fx :reverb, mix: 0.9 do
    play_pattern_timed [:g4, :a4, :b4, :d5], [2, 1, 1, 4], 
                       amp: 0.4 * get(:master_amp), release: 2
    sleep 4
    play_pattern_timed [:c5, :b4, :a4], [1.5, 0.5, 4], 
                       amp: 0.3 * get(:master_amp), release: 2
  end
end

live_loop :coda_dizi do
  sync :coda
  use_synth :hollow
  sleep 4
  play :g5, release: 12, amp: 0.2 * get(:master_amp)  # 竹笛远去的长音收束
end

live_loop :coda_fade do
  sync :end
  use_synth :hollow
  play_chord chord(:g4, :maj7), amp: 0.1 * get(:master_amp), release: 10
  sleep 4
end