# 夏日海滩流行电子乐 - 改进版
# 清新夏日感，热带元素，轻快节奏，动态结构

use_bpm 115

# 主时钟控制
set :master_beat, 0

live_loop :metronome do
  set :master_beat, (get[:master_beat] + 1) % 64
  sleep 1
end

define :current_beat do
  get[:master_beat]
end

define :current_chord_index do
  (current_beat / 4) % 4  # 每4拍换一个和弦
end

define :section do
  (current_beat / 16) % 4  # 16拍为一个段落
end

# 定义和声进行 - C大调明亮和弦
chord_progression = [
  chord(:c4, :maj),   # I
  chord(:g4, :maj),   # V
  chord(:a4, :min),   # vi
  chord(:f4, :maj)    # IV
]

# 定义钢鼓主题动机 - 上行琶音
steel_drum_motif = [
  [:c5, :e5, :g5, :c6],
  [:g4, :b4, :d5, :g5],
  [:a4, :c5, :e5, :a5],
  [:f4, :a4, :c5, :f5]
]

# 贝斯线模式
bass_pattern = [
  :c2, :r, :g2, :r,
  :a2, :r, :f2, :r
]

# 海浪采样
live_loop :ocean_waves do
  sample :ambi_soft_buzz, rate: 0.3, amp: 0.4, attack: 2, release: 4
  sleep 8
end

# 主节奏鼓组 - 改进版
live_loop :drums do
  current_section_val = section
  
  # 底鼓在强拍
  sample :bd_haus, amp: 0.8 if current_beat % 4 == 0
  
  # 军鼓在第二和第四拍
  sample :sn_dolf, amp: 0.6 if current_beat % 4 == 2
  
  # 踩镲密度根据段落变化
  density_val = case current_section_val
               when 0 then 2  # 稀疏的引子
               when 1, 3 then 4  # 完整段落
               when 2 then 1  # 分解段落
               end
              
  density_val.times do
    sample :drum_cymbal_closed, amp: 0.25
    sleep 1.0 / density_val
  end
  
  # 沙锤效果 - 只在完整段落出现
  if current_section_val == 1 || current_section_val == 3
    sample :perc_snap2, rate: 1.5, amp: 0.2 if spread(3, 8).tick
  end
  
  # 在段落过渡处添加鼓花
  if (current_beat % 16) == 15
    sample :drum_roll, rate: 0.8, amp: 0.4
  end
end

# 钢鼓主旋律 - 改进版
live_loop :steel_drum do
  use_synth :pretty_bell
  with_fx :reverb, room: 0.6 do
    current_section_val = section
    current_chord_idx = current_chord_index
    
    case current_section_val
    when 0  # 引子 - 稀疏
      if one_in(2)
        play_pattern_timed steel_drum_motif[current_chord_idx], [0.2, 0.2, 0.2, 0.4], amp: 0.6
      end
    when 2  # 分解段落 - 不同模式
      play_pattern_timed [:g5, :e5, :c5], [0.3, 0.3, 0.6], amp: 0.7
    else  # 主要段落
      play_pattern_timed steel_drum_motif[current_chord_idx], [0.2, 0.2, 0.2, 0.4], amp: 0.8
    end
    
    sleep 1
  end
end

# 尼龙弦吉他分解和弦 - 改进版
live_loop :guitar do
  use_synth :pluck
  with_fx :echo, decay: 2 do
    current_section_val = section
    current_chord_notes_val = chord_progression[current_chord_index]
    
    # 根据段落调整演奏密度
    if current_section_val != 2  # 分解段落不演奏吉他
      play_pattern_timed current_chord_notes_val, [0.25, 0.25, 0.25, 0.25], amp: 0.6
    end
    
    sleep 2
  end
end

# 跳跃贝斯线 - 改进版
live_loop :bass do
  use_synth :fm
  with_fx :lpf, cutoff: 80 do
    current_note_val = bass_pattern.tick
    current_section_val = section
    
    unless current_note_val == :r
      # 添加次低音增加重量和延音
      play current_note_val, release: 0.8, amp: 0.6
      play current_note_val - 12, release: 1.2, amp: 0.3  # 低八度
      
      # 在完整段落添加装饰音
      if (current_section_val == 1 || current_section_val == 3) && one_in(4)
        play current_note_val + 7, release: 0.2, amp: 0.2  # 五度装饰音
      end
    end
    sleep 0.5
  end
end

# 明亮合成器铺底 - 改进版
live_loop :pad do
  use_synth :hollow
  current_chord_val = chord_progression[current_chord_index]
  current_section_val = section
  
  # 根据段落调整铺底强度
  pad_amp_val = case current_section_val
               when 0 then 0.2  # 安静的引子
               when 1, 3 then 0.4  # 完整段落
               when 2 then 0.15  # 分解段落
               end
  
  play_chord current_chord_val, attack: 1, release: 3, amp: pad_amp_val
  sleep 4
end

# 小号短句（复古色彩）- 改进版
live_loop :trumpet do
  use_synth :beep
  with_fx :reverb, mix: 0.4 do
    current_section_val = section
    
    # 只在完整段落演奏小号
    if current_section_val == 1 || current_section_val == 3
      # 简单的旋律短句
      play_pattern_timed [:e5, :g5, :c6, :b5], [0.3, 0.3, 0.6, 0.8], amp: 0.5
    end
    
    sleep 4
  end
end

# 段落过渡效果
live_loop :transitions do
  sync :drums  # 与鼓循环同步
  
  if (current_beat % 16) == 0  # 段落开始
    sample :glitch_perc1, rate: 0.8, amp: 0.3
  elsif (current_beat % 16) == 15  # 段落结束
    sample :ambi_glass_rub, rate: 0.5, amp: 0.2
  end
  
  sleep 0.5
end

# 特殊效果 - 海鸥鸣叫等
live_loop :sfx do
  current_section_val = section
  
  # 随机加入环境音效 - 在分解段落增加频率
  sfx_probability = current_section_val == 2 ? 8 : 16
  
  if one_in(sfx_probability)
    sample :misc_cineboom, rate: 0.5, amp: 0.2
  end
  
  # 在引子段落添加海鸥音效
  if current_section_val == 0 && one_in(32)
    sample :ambi_glass_hum, rate: 0.3, amp: 0.15
  end
  
  sleep 4
end