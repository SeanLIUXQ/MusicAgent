# 沂蒙山小调 - 中国北方传统民歌
# 风格：山东沂蒙山地区特色汉族民间小调
# 改进版：增强音乐性、动态变化和结构发展

use_bpm 85
use_synth_defaults amp: 0.8

# 中国传统五声调式（宫调）
pentatonic_scale = scale(:c4, :major_pentatonic, num_octaves: 2)

# 旋律音符序列 - 沂蒙山小调主旋律
melody_notes = [
  [:c4, 0.5], [:d4, 0.5], [:e4, 1], [:g4, 1],
  [:e4, 0.5], [:d4, 0.5], [:c4, 2],
  [:d4, 0.5], [:e4, 0.5], [:g4, 1], [:a4, 1],
  [:g4, 0.5], [:e4, 0.5], [:d4, 2],
  [:e4, 0.5], [:d4, 0.5], [:c4, 1], [:d4, 1],
  [:e4, 0.75], [:d4, 0.25], [:c4, 2]
]

# 第二段旋律增强变化
second_melody_notes = [
  [:c4, 0.5], [:d4, 0.5], [:e4, 1], [:g4, 1.5],  # 延长尾音
  [:e4, 0.25], [:d4, 0.25], [:c4, 2.5],          # 更快节奏，更长延音
  [:d4, 0.5], [:f4, 0.5], [:g4, 1], [:a4, 1.5],  # 添加f4增加变化
  [:g4, 0.5], [:e4, 0.5], [:d4, 3],              # 延长结尾
  [:e4, 0.75], [:d4, 0.25], [:c4, 1.5], [:d4, 1],
  [:e4, 1], [:d4, 0.5], [:c4, 3]                 # 更戏剧性的结尾
]

# 古筝琶音和声背景
guzheng_arpeggio = [:c3, :g3, :c4, :e4, :g4]

# 扬琴节奏点缀音符
yangqin_notes = [:g4, :a4, :c5, :d5]

# 全局控制变量
current_section = :intro

# 前奏：笛子模仿山野鸟鸣
live_loop :flute_intro do
  set :current_section, :intro
  with_fx :reverb, mix: 0.3 do
    with_synth :blade do
      4.times do |i|
        # 动态变化：逐渐增强
        intro_amp = 0.4 + (i * 0.05)
        play_pattern_timed [:g5, :a5, :g5, :e5], [0.25, 0.125, 0.125, 0.5], 
                          amp: intro_amp, attack: 0.1, release: 0.3
        sleep 1
      end
    end
  end
  set :current_section, :verse
  stop
end

# 古筝轻柔琶音铺垫 - 改进版
live_loop :guzheng_background do
  with_synth :pluck do
    with_fx :lpf, cutoff: 95 do
      with_fx :reverb, room: 0.3 do
        guzheng_arpeggio.each do |note_val|
          play note_val, 
               amp: 0.3, 
               attack: 0.05, 
               release: 1.5, 
               pan: -0.2,
               coef: 0.3  # 拨弦特性
          sleep 0.75  # 更流畅的节奏
        end
      end
    end
  end
end

# 二胡主旋律（第一段）- 改进版
live_loop :erhu_melody do
  sync :flute_intro
  with_synth :fm do  # 更好的二胡音色近似
    with_fx :reverb, room: 0.4 do
      with_fx :vibrato, depth: 0.08, rate: 6 do  # 更细微的颤音
        melody_notes.each_with_index do |(note_val, duration), idx|
          # 创建自然的乐句动态
          phrase_pos = idx % 8
          dynamic_amp = case phrase_pos
                       when 0, 1 then 0.6  # 柔和开始
                       when 2, 3 then 0.8  # 渐强
                       when 4, 5 then 1.0  # 高峰
                       when 6, 7 then 0.7  # 解决
                       else 0.8
                       end
          
          play note_val, 
               amp: dynamic_amp * 0.7, 
               attack: 0.15, 
               release: duration * 0.9,
               pan: 0.1,
               cutoff: 90  # 添加滤波器增加温暖感
          sleep duration
        end
      end
    end
  end
end

# 过渡段 - 新增
live_loop :transition do
  sync :erhu_melody
  set :current_section, :transition
  
  with_synth :hollow do
    # 上升过渡模式
    play_pattern_timed [:c4, :e4, :g4, :c5], [0.75, 0.75, 0.75, 1.5], 
                       amp: 0.5, release: 1.2
  end
  
  # 逐渐加速增加兴奋感
  4.times do |i|
    use_bpm 85 + (i * 2)
    sleep 1
  end
  
  set :current_section, :chorus
end

# 扬琴节奏点缀 - 改进版
live_loop :yangqin_accent do
  sync :transition
  sleep 4  # 等待过渡结束
  
  with_synth :pluck do
    8.times do |i|  # 延长间奏
      yangqin_amp = 0.3 + (i * 0.025)  # 逐渐增强
      play yangqin_notes.choose, 
           amp: yangqin_amp, 
           release: 0.3, 
           pan: 0.4,
           coef: 0.2
      sleep [0.5, 0.75, 0.5, 0.25, 0.5, 0.5, 0.25, 0.75][i % 8]  # 更多节奏变化
    end
  end
end

# 增强的节奏发展 - 改进版
live_loop :drum_rhythm do
  tick
  beat_val = look % 16
  
  case beat_val
  when 0, 8
    sample :drum_tom_hi_hard, amp: 0.4, rate: 0.8
  when 4, 12
    sample :drum_tom_lo_hard, amp: 0.3, rate: 0.6
  when 2, 6, 10, 14
    sample :drum_tom_mid_soft, amp: 0.2, rate: 1.0
  end
  
  # 在第7和第15拍添加偶尔的重音以增加切分感
  if beat_val == 7 || beat_val == 15
    sample :drum_snare_soft, amp: 0.15, rate: 0.7
  end
  
  sleep 0.5  # 双倍时间分辨率以获得更多节奏变化
end

# 木鱼偶尔点缀 - 改进版
live_loop :wooden_fish do
  if one_in(6)  # 稍微增加频率
    wooden_amp = 0.15 + (rand * 0.1)  # 随机动态
    sample :perc_bell, amp: wooden_amp, rate: 0.5, pan: -0.2
  end
  sleep 1.5  # 更灵活的节奏
end

# 第二段旋律（增强变化）- 改进版
live_loop :second_melody do
  sync :yangqin_accent
  sleep 4  # 等待间奏结束
  
  with_synth :fm do
    with_fx :reverb, room: 0.5 do
      with_fx :vibrato, depth: 0.12, rate: 7 do  # 更强的颤音表达情感
        second_melody_notes.each_with_index do |(note_val, duration), idx|
          # 根据乐句位置调整动态
          phrase_pos = idx % 6
          dynamic_amp = case phrase_pos
                       when 0, 1 then 0.7
                       when 2, 3 then 0.9
                       when 4, 5 then 1.1  # 第二段更强
                       else 0.9
                       end
          
          play note_val, 
               amp: dynamic_amp * 0.7, 
               attack: 0.1, 
               release: duration * 0.7, 
               pan: 0.2,
               cutoff: 100  # 更明亮的音色
          sleep duration
        end
      end
    end
  end
end

# 尾声：渐慢渐弱，笛子悠长收尾 - 改进版
live_loop :ending do
  sync :second_melody
  sleep 8  # 等待第二段结束
  set :current_section, :ending
  
  # 所有元素的逐渐淡出
  with_fx :level, amp: 1 do |level_control|
    16.times do |i|
      control level_control, amp: 1.0 - (i * 0.0625)
      
      with_synth :blade do
        play [:c5, :g4, :e4, :c4].choose, 
             amp: 0.4 * (1.0 - (i * 0.06)),
             attack: 0.4, 
             release: 2.0,
             pan: 0.1
      end
      sleep [1.2, 1.4, 1.6, 2.0][i % 4]
    end
  end
  
  # 最后的回响
  with_fx :reverb, room: 0.9, mix: 0.8 do
    with_synth :hollow do
      play :c4, amp: 0.2, attack: 1.0, release: 6, pan: 0
      sleep 8
    end
  end
  
  # 停止所有循环
  stop
end

# 全局控制函数
define :fade_all do |duration_val|
  # 平滑淡出函数
  steps = duration_val / 0.1
  steps.to_i.times do |i|
    current_amp = 1.0 - (i.to_f / steps)
    control get[:master_amp], amp: current_amp if get[:master_amp]
    sleep 0.1
  end
end

define :change_tempo do |new_bpm, transition_time|
  # 逐渐改变速度
  current_bpm = current_bpm
  steps = (new_bpm - current_bpm).abs / 2
  direction = new_bpm > current_bpm ? 1 : -1
  
  steps.to_i.times do
    use_bpm current_bpm + direction * 2
    sleep transition_time / steps
  end
  use_bpm new_bpm
end