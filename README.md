# MusicAgent

## 赵明泽：v2已更新，最新代码在`multiagents`文件夹下。

**1. 在midi2music文件夹内，有midi转音频的相关代码环境**

**2. music_llm_dialogue.py是与LLM对话的demo脚本，可以完成上传音频、音频=>MIDI文件、解析JSON、输入自然语言与LLM交互、获取修改音乐风格后的JSON、MIDI=>音频，可以循环对话**  
1. 注意需要使用自己的API-Key，默认使用Qwen3-Max模型，可以自行选择模型  
2. 需要激活虚拟环境使用
3. 优先使用music_llm_dialogue_V2.py,V1是早期版本
4. 基本步骤：  
   【步骤1】用户上传原始音频文件（MP3/WAV等）  
   ↓  
   【步骤2】音频特征提取（extract_audio_features_and_midi）  
   ├─ 使用 librosa 提取：  
   │ ├─ BPM（节拍速度）  
   │ ├─ 调性（chroma特征 + Krumhansl-Schmuckler算法）  
   │ ├─ 持续时间  
   │ └─ 平均能量  
   │ └─ 使用 basic_pitch 转录为 MIDI：  
   ├─ predict() 函数将音频转换为 PrettyMIDI 对象  
   ├─ PrettyMIDI → MIDI bytes  
   └─ MIDI bytes → mido.MidiFile 解析  
   ↓  
   【步骤3】MIDI转换为JSON格式  
   ├─ 提取所有MIDI事件（note_on, note_off, program_change等）    
   ├─ 转换为JSON格式：  
   │ {  
   │ "tempo": 120,  
   │ "events": [  
   │ {"type": "note_on", "channel": 0, "note": 60, "velocity": 64, "time": 0},  
   │ ...  
   │ ]  
   │ }  
   └─ 计算原始MIDI持续时间  
   ↓  
   【步骤4】构建LLM对话上下文  
   ├─ System Prompt：定义LLM角色和任务  
   ├─ 初始消息：音频特征 + MIDI JSON文本  
   └─ LLM分析音频特征和MIDI结构（call_qwen_llm）  
   ↓ 【步骤5】用户输入风格转换需求  
   ├─ 例如："转换为摇滚风格"、"改为爵士风格"  
   ├─ 根据需求生成具体的风格转换指令  
   └─ 构建用户消息：  
   ├─ 原始音频信息（特征 + MIDI JSON）  
   ├─ 风格转换规则（摇滚/爵士/轻柔等）  
   └─ 强制要求（必须改变乐器、力度等）  
   ↓
   【步骤6】LLM生成新的MIDI JSON  
   ├─ 调用 qwen3-max 模型（DashScope API）  
   ├─ LLM返回修改后的MIDI JSON文本  
   └─ 提取MIDI JSON（extract_midi_json_from_text）  
   ↓  
   【步骤7】验证和自动风格转换  
   ├─ 检查生成的MIDI是否与原始相同  
   ├─ 检查是否包含program_change事件  
   ├─ 检查velocity是否有明显变化  
   └─ 如果变化不明显，自动应用风格转换（apply_style_transformation）  
   ├─ 摇滚：添加电吉他（program 25），提高力度到80-127  
   ├─ 爵士：添加萨克斯（program 65），调整力度到40-100  
   └─ 轻柔：添加钢琴（program 1），降低力度到30-70  
   ↓  
   【步骤8】MIDI JSON转换为.mid文件  
   ├─ midi_json_to_mid_file()  
   ├─ 创建MidiFile对象  
   ├─ 添加tempo设置  
   ├─ 转换所有事件为MIDI消息  
   ├─ 调整持续时间以匹配原始音频（adjust_midi_duration ）  
   └─ 保存为.mid文件（如 output_1.mid）  
   ↓  
   【步骤9】MIDI文件转换为音频  
   ├─ convert_mid_to_audio()  
   ├─ 调用 midi_to_audio.py 脚本  
   ├─ 使用 subprocess 执行：  
   │ python midi_to_audio.py output_1.mid --wav output_1_render.wav --mp3 output_1_render.mp3  
   └─ 生成最终音频文件  
   ↓  
   【步骤10】循环对话（可选）  
   └─ 用户可以继续输入新的风格需求，重复步骤5-9  
