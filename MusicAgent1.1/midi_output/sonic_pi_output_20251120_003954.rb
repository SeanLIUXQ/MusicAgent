```ruby
# 夏日氛围音乐 - 热带浩室风格
# 改进版：添加歌曲结构、动态变化和更好的音乐性

use_bpm 110

# 歌曲段落定义
current_section = :intro
song_sections = [:intro, :verse, :build, :drop, :breakdown, :outro]
section_duration = 16  # 每段落16小节

# 扩展和弦进行
chord_progressions = {
  intro: [:c3, :g2, :a2, :f2],
  verse: [:c3, :g2, :am2, :f2],
  build: [:c3, :em2, :am2, :f2],
  drop: [:c3, :g2, :am2, :f2],
  breakdown: [:am2, :f2, :c3, :g2],
  outro: [:c3, :f2, :g2, :c3]
}

current_chord_idx = 0

# 使用内置采样作为备选
ocean_sample_path = "/path/to/ocean_waves.wav"
ocean_sample_path = :ambi_soft_buzz unless File.exist?(ocean_sample_path)

seagull_sample_path = "/path/to/seagull.wav" 
seagull_sample_path = :misc_cineboom unless File.exist?(seagull_sample_path)

# 段落管理器
live_loop :section_controller do
  cue :section_change
  
  case current_section
  when :intro
    set :master_level, 0.7
    set :pad_level, 0.2
    set :melody_level, 0.3
    set :bass_level, 0.4
    set :drum_level, 0.6
  when :verse
    set :master_level, 0.8
    set :pad_level, 0.4
    set :melody_level, 0.5
    set :bass_level, 0.6
    set :drum_level, 0.8
  when :build
    set :master_level, 0.9
    set :pad_level, 0.5
    set :melody_level, 0.6
    set :bass_level, 0.7
    set :drum_level, 0.9
  when :drop
    set :master_level, 1.0
    set :pad_level, 0.6
    set :melody_level, 0.8
    set :bass_level, 0.9
    set :drum_level, 1.0
  when :breakdown
    set :master_level, 0.6
    set :pad_level, 0.3
    set :melody_level, 0.4
    set :bass_level, 0.5
    set :drum_level, 0.4
  when :outro
    set :master_level, 0.5
    set :pad_level, 0.2
    set :melody_level, 0.3
    set :bass_level, 0.3
    set :drum_level, 0.3
  end
  
  sleep section_duration
  current_section = song_sections[(song_sections.index(current_section) + 1) % song_sections.length]
end

# 主混响效果 - 模拟夏日室内
with_fx :reverb, room: 0.8, damp: 0.7, mix: 0.4 do
  with_fx :eq, low: -0.2, mid: 0, high: 0.3, high_shelf: 0.5 do
    
    # 海浪环境音
    live_loop :ocean_background, sync: :section_controller do
      sample ocean_sample_path, rate: 0.8, amp: 0.3 * get[:master_level]
      sleep 8
    end
    
    # 节奏组 - 动态鼓点
    live_loop :drums, sync: :section_controller do
      drum_amp = get[:drum_level] * get[:master_level]
      
      case current_section
      when :intro
        # 稀疏节奏
        sample :bd_haus, amp: 0.8 * drum_amp
        sleep 1
      when :verse
        # 标准节奏
        4.times do |i|
          sample :bd_haus, amp: 0.8 * drum_amp
          sleep 0.5
          sample :drum_snare_soft, amp: 0.4 * drum_amp if i % 2 == 1
        end
      when :build, :drop
        # 强烈节奏
        8.times do |i|
          sample :bd_haus, amp: 1.0 * drum_amp
          sleep 0.25
          sample :drum_snare_soft, amp: 0.6 * drum_amp if i % 4 == 2
        end
      when :breakdown, :outro
        # 简化节奏
        sample :bd_haus, amp: 0.6 * drum_amp
        sleep 2
      end
    end
    
    # 动态踩镲
    live_loop :hihat_pattern, sync: :section_controller do
      case current_section
      when :intro, :breakdown
        # 简单模式
        4.times do
          sample :drum_cymbal_closed, amp: 0.2 * get[:master_level]
          sleep 1
        end
      when :verse, :build
        # 标准模式
        8.times do |i|
          if i % 2 == 1
            sample :drum_cymbal_open, amp: 0.4 * get[:master_level], attack: 0.02, release: 0.1
          else
            sample :drum_cymbal_closed, amp: 0.2 * get[:master_level]
          end
          sleep 0.5
        end
      when :drop
        # 密集模式
        16.times do |i|
          sample :drum_cymbal_closed, amp: 0.3 * get[:master_level], rate: 1.2 if i % 4 != 0
          sleep 0.25
        end
      end
    end
    
    # 持续打击乐 - 根据段落变化
    live_loop :percussion, sync: :section_controller do
      case current_section
      when :intro, :outro
        # 简单打击
        4.times do
          sample :perc_snap2, amp: 0.1 * get[:master_level], rate: 1.5
          sleep 1
        end
      when :verse, :breakdown
        # 中等密度
        8.times do
          sample :perc_snap2, amp: 0.15 * get[:master_level], rate: 1.5
          sleep 0.5
        end
      when :build, :drop
        # 高密度
        16.times do
          sample :perc_snap2, amp: 0.2 * get[:master_level], rate: 1.5
          sleep 0.25
        end
      end
    end
    
    # 动态钢鼓旋律
    live_loop :steel_drum_melody, sync: :section_controller do
      use_synth :pretty_bell
      melody_amp = get[:melody_level] * get[:master_level]
      
      case current_section
      when :intro
        # 简单动机
        play_pattern_timed [:c5, :e5, :g5], [0.5, 0.5, 1], amp: 0.4 * melody_amp
        sleep 2
      when :verse
        # 扩展动机
        play_pattern_timed [:c5, :e5, :g5, :a5], [0.5, 0.25, 0.25, 1], amp: 0.5 * melody_amp
        sleep 1
      when :build
        # 上升旋律
        play_pattern_timed [:c5, :e5, :g5, :a5, :c6], [0.25, 0.25, 0.25, 0.25, 1], amp: 0.6 * melody_amp
        sleep 0.5
      when :drop
        # 复杂模式
        play_pattern_timed [:c5, :e5, :g5, :a5, :g5, :e5, :c5, :d5], 
                          [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25], 
                          amp: 0.7 * melody_amp
      when :breakdown, :outro
        # 简化回归
        play_pattern_timed [:c5, :e5, :g5], [1, 1, 2], amp: 0.3 * melody_amp
        sleep 4
      end
    end
    
    # 马林巴琴分解和弦 - 带扩展音
    live_loop :marimba_arpeggio, sync: :section_controller do
      use_synth :kalimba
      current_root = chord_progressions[current_section][current_chord_idx]
      
      case current_section
      when :intro, :outro
        # 简单三和弦
        chord_notes = chord(current_root, :major)
        chord_notes.each do |note|
          play note + 12, amp: 0.3 * get[:master_level], release: 0.3
          sleep 0.5
        end
      when :verse, :breakdown
        # 添加七音
        chord_notes = chord(current_root, :maj7)
        chord_notes.each do |note|
          play note + 12, amp: 0.4 * get[:master_level], release: 0.3
          sleep 0.25
        end
        sleep 0.25
      when :build, :drop
        # 完整扩展和弦
        chord_notes = chord(current_root, :maj9)
        chord_notes.each do |note|
          play note + 12, amp: 0.5 * get[:master_level], release: 0.2
          sleep 0.125
        end
        sleep 0.25
      end
      
      current_chord_idx = (current_chord_idx + 1) % 4
    end
    
    # 动态贝斯线
    live_loop :bass_line, sync: :section_controller do
      use_synth :fm
      bass_amp = get[:bass_level] * get[:master_level]
      current_root = chord_progressions[current_section][current_chord_idx]
      
      case current_section
      when :intro, :breakdown
        # 简单根音
        play current_root, amp: 0.4 * bass_amp, release: 0.5, cutoff: 70
        sleep 2
      when :verse
        # 基础模式
        bass_pattern = [current_root, current_root + 7, current_root + 12]
        play_pattern_timed bass_pattern, [1, 0.5, 0.5], amp: 0.5 * bass_amp, release: 0.2, cutoff: 80
        sleep 1
      when :build, :drop
        # 复杂模式
        bass_pattern = [current_root, current_root + 5, current_root + 7, current_root + 12, current_root + 7, current_root + 5]
        play_pattern_timed bass_pattern, [0.5, 0.25, 0.25, 0.5, 0.25, 0.25], 
                          amp: 0.6 * bass_amp, release: 0.1, cutoff: 100
      end
    end
    
    # 合成器铺底 - 动态滤波器
    live_loop :pad_synth, sync: :section_controller do
      use_synth :hollow
      pad_amp = get[:pad_level] * get[:master_level]
      current_root = chord_progressions[current_section][current_chord_idx]
      
      case current_section
      when :intro, :outro
        play_chord chord(current_root, :major), amp: 0.2 * pad_amp, attack: 4, release: 8, cutoff: 60
        sleep 8
      when :verse, :breakdown
        play_chord chord(current_root, :maj7), amp: 0.4 * pad_amp, attack: 2, release: 6, cutoff: 80
        sleep 4
      when :build
        play_chord chord(current_root, :maj9), amp: 0.5 * pad_amp, attack: 1, release: 4, cutoff: 100
        sleep 2
      when :drop
        play_chord chord(current_root, :maj9), amp: 0.6 * pad_amp, attack: 0.5, release: 2, cutoff: 120
        sleep 1
      end
    end
    
    # 尤克里里节奏 - 段落变化
    live_loop :ukulele_rhythm, sync: :section_controller do
      use_synth :pluck
      current_root = chord_progressions[current_section][current_chord_idx]
      
      case current_section
      when :intro, :outro
        # 简单节奏
        with_fx :lpf, cutoff: 80 do
          play current_root + 7, amp: 0.2 * get[:master_level], release: 0.2
          sleep 2
        end
      when :verse, :breakdown
        # 切分节奏
        with_fx :lpf, cutoff: 90 do
          play current_root + 7, amp: 0.3 * get[:master_level], release: 0.1
          sleep 0.75
          play current_root + 4, amp: 0.3 * get[:master_level], release: 0.1
          sleep 0.25
        end
      when :build, :drop
        # 密集节奏
        with_fx :lpf, cutoff: 100 do
          2.times do
            play current_root + 7, amp: 0.4 * get[:master_level], release: 0.1
            sleep 0.25
            play current_root + 4, amp: 0.4 * get[:master_level], release: 0.1
            sleep 0.25
          end
        end
      end
    end
    
    # 哨笛主旋律 - 段落发展
    live_loop :whistle_lead, sync: :section_controller do
      use_synth :sine
      melody_amp = get[:melody_level] * get[:master_level]
      current_root = chord_progressions[current_section][current_chord_idx]
      
      case current_section
      when :intro
        # 简单旋律
        melody_pattern = [current_root + 12, current_root + 16]
        play_pattern_timed melody_pattern, [1, 1], amp: 0.3 * melody_amp
        sleep 2
      when :verse
        # 扩展旋律
        melody_pattern = [current_root + 12, current_root + 16, current_root + 12, current_root + 9]
        play_pattern_timed melody_pattern, [0.5, 0.5, 1, 1], amp: 0.5 * melody_amp
        sleep 1
      when :build
        # 上升旋律
        melody_pattern = [current_root + 12, current_root + 16, current_root + 19, current_root + 16]
        play_pattern_timed melody_pattern, [0.25, 0.25, 0.5, 0.25], amp: 0.6 * melody_amp
        sleep 0.75
      when :drop
        # 高潮旋律
        melody_pattern = [current_root + 12, current_root + 16, current_root + 19, current_root + 16, 
                         current_root + 12, current_root + 9, current_root + 7, current_root + 9]
        play_pattern_timed melody_pattern, [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25], 
                          amp: 0.8 * melody_amp
      when :breakdown, :outro
        # 简化旋律
        play current_root + 12, amp: 0.4 * melody_amp, release: 2
        sleep 4
      end
    end
    
    # 过渡效果和填充
    live_loop :transition_effects, sync: :section_controller do
      case current_section
      when :build
        # 上升效果
        with_fx :lpf, cutoff: 130 do
          with_fx :reverb, room: 0.9 do
            use_synth :saw
            play_chord chord(:c5, :major), amp: 0.2 * get[:master_level], release: 8, cutoff: rrand(60, 120)
          end
        end
      when :drop
        # 冲击效果
        sample :drum_roll, rate: 3, amp: 0.8 * get[:master_level]
        sample :glitch_perc5, amp: 0.4 * get[:master_level]
      when :breakdown
        # 海鸥过渡
        sample seagull_sample_path, amp: 0.3 * get[:master_level] if one_in(2)
      end
      sleep section_duration
    end
    
    # 康加鼓填充 - 只在特定段落
    live_loop :conga