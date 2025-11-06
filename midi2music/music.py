from mido import Message, MidiFile, MidiTrack, MetaMessage

# 创建MIDI文件和音轨
mid = MidiFile()
track = MidiTrack()
mid.tracks.append(track)

# 设置较慢的速度 (80 BPM，忧郁的感觉)
track.append(MetaMessage('set_tempo', tempo=750000))

# 设置钢琴音色 (Program 0 = Acoustic Grand Piano)
track.append(Message('program_change', program=0, time=0))

# 定义忧郁的钢琴旋律 (C小调)
# C小调音阶: C, D, Eb, F, G, Ab, Bb
# MIDI音符: 60, 62, 63, 65, 67, 68, 70

melody = [
    # 第一段 - 缓慢忧郁的主题
    (60, 480, 70),  # C4 - 主音，长音符
    (63, 240, 65),  # Eb4 - 小三度，忧郁的核心
    (60, 240, 60),  # C4
    (58, 480, 68),  # Bb3 - 降七度
    (60, 960, 75),  # C4 - 长音结束乐句

    # 第二段 - 发展
    (65, 360, 72),  # F4
    (63, 120, 65),  # Eb4
    (60, 480, 70),  # C4
    (58, 240, 68),  # Bb3
    (56, 240, 65),  # Ab3 - 降六度，增加忧郁色彩
    (60, 960, 75),  # C4

    # 第三段 - 情绪高潮
    (67, 240, 80),  # G4
    (65, 240, 78),  # F4
    (63, 480, 75),  # Eb4
    (62, 240, 70),  # D4
    (60, 240, 68),  # C4
    (58, 480, 65),  # Bb3

    # 结尾 - 逐渐消失
    (63, 360, 70),  # Eb4
    (60, 120, 65),  # C4
    (58, 240, 60),  # Bb3
    (56, 240, 58),  # Ab3
    (60, 1920, 50),  # C4 - 很长的结束音，力度逐渐减弱
]

# 添加音符到音轨
for note, duration, velocity in melody:
    # Note on
    track.append(Message('note_on', note=note, velocity=velocity, time=0))
    # Note off
    track.append(Message('note_off', note=note, velocity=0, time=duration))

# 保存MIDI文件
mid.save('melancholy_piano.mid')
print("✓ 忧郁的钢琴旋律已生成！")
print("文件保存为: melancholy_piano.mid")
print("调性: C小调")
print("速度: 80 BPM (慢板)")
print("特点: 使用小调音阶、长音符、渐弱结尾来营造忧郁氛围")