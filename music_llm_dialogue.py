#!/usr/bin/env python3
"""
music_llm_dialogue.py

与大语言模型的音乐对话脚本
- 上传原始音频文件
- 提取音频特征和MIDI信息
- 使用自然语言描述音乐需求（如"转换成适合安静场景下听的音乐"、"转换为摇滚风格"）
- 调用qwen3-max模型生成满足需求的MIDI文本
- 将MIDI文本转换为MID文件
- 使用midi_to_audio.py将MID文件转换为音频
- 支持循环对话

使用方法:
    python music_llm_dialogue.py
"""

import os
import json
import re
import subprocess
import sys
from pathlib import Path
from io import BytesIO

# DashScope API
from dashscope import Generation
import dashscope

# MIDI处理
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage

# 音频处理
import librosa
import numpy as np
from basic_pitch.inference import predict
import pretty_midi

# API配置
API_KEY = "替换成自己的API-Key"
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'


def estimate_key(chroma_mean):
    """
    使用 Krumhansl-Schmuckler 算法从 chroma 估计调性（major/minor）。
    """
    try:
        # 归一化 chroma
        chroma_norm = chroma_mean / np.linalg.norm(chroma_mean)

        # KS 模板
        major_profile = np.array([6.35, 2.26, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88])
        minor_profile = np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])

        keys = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        scores = {}

        for i in range(12):
            rotated_major = np.roll(major_profile, i)
            rotated_minor = np.roll(minor_profile, i)

            corr_major = np.corrcoef(chroma_norm, rotated_major)[0, 1]
            corr_minor = np.corrcoef(chroma_norm, rotated_minor)[0, 1]

            scores[f"{keys[i]} major"] = corr_major
            scores[f"{keys[i]} minor"] = corr_minor

        best_key = max(scores, key=scores.get)
        return best_key
    except Exception as e:
        print(f"调性估计失败: {e}")
        return "C major"  # 默认回退


def apply_style_transformation(midi_json, style_request, target_duration):
    """
    如果LLM返回的MIDI与原始相同，自动应用风格转换。
    """
    try:
        # 创建新的MIDI JSON副本
        new_midi_json = json.loads(json.dumps(midi_json))
        events = new_midi_json.get("events", [])
        
        if not events:
            return midi_json
        
        # 根据风格需求应用转换
        if "摇滚" in style_request or "rock" in style_request.lower():
            # 摇滚风格：添加电吉他，提高力度
            print("  应用摇滚风格转换：添加电吉他，提高力度到80-127")
            
            # 添加program_change事件（在第一个note_on之前）
            has_program_change = any(e.get("type") == "program_change" for e in events)
            if not has_program_change:
                # 找到第一个note_on事件
                first_note_on_idx = next((i for i, e in enumerate(events) if e.get("type") == "note_on"), None)
                if first_note_on_idx is not None:
                    # 在第一个note_on之前插入program_change
                    program_change = {
                        "type": "program_change",
                        "channel": 0,
                        "program": 25,  # 电吉他
                        "time": 0
                    }
                    events.insert(first_note_on_idx, program_change)
            
            # 提高所有note_on的velocity
            for event in events:
                if event.get("type") == "note_on":
                    original_vel = event.get("velocity", 64)
                    if original_vel < 80:
                        # 提高到80-127之间
                        new_vel = min(127, max(80, original_vel + 20))
                        event["velocity"] = new_vel
                    elif original_vel < 100:
                        # 进一步提高
                        event["velocity"] = min(127, original_vel + 15)
        
        elif "爵士" in style_request or "jazz" in style_request.lower():
            # 爵士风格：添加萨克斯，调整力度
            print("  应用爵士风格转换：添加萨克斯，调整力度到40-100")
            
            # 添加program_change事件
            has_program_change = any(e.get("type") == "program_change" for e in events)
            if not has_program_change:
                first_note_on_idx = next((i for i, e in enumerate(events) if e.get("type") == "note_on"), None)
                if first_note_on_idx is not None:
                    program_change = {
                        "type": "program_change",
                        "channel": 0,
                        "program": 65,  # 中音萨克斯
                        "time": 0
                    }
                    events.insert(first_note_on_idx, program_change)
            
            # 调整所有note_on的velocity
            for event in events:
                if event.get("type") == "note_on":
                    original_vel = event.get("velocity", 64)
                    if original_vel > 100:
                        # 降低到40-100之间
                        new_vel = max(40, min(100, original_vel - 20))
                        event["velocity"] = new_vel
                    elif original_vel < 40:
                        # 提高到40-100之间
                        new_vel = min(100, max(40, original_vel + 10))
                        event["velocity"] = new_vel
                    else:
                        # 在范围内，稍微调整以体现变化
                        event["velocity"] = max(40, min(100, original_vel + 5))
        
        elif "安静" in style_request or "轻柔" in style_request or "soft" in style_request.lower():
            # 轻柔风格：使用钢琴，降低力度
            print("  应用轻柔风格转换：使用钢琴，降低力度到30-70")
            
            # 添加program_change事件
            has_program_change = any(e.get("type") == "program_change" for e in events)
            if not has_program_change:
                first_note_on_idx = next((i for i, e in enumerate(events) if e.get("type") == "note_on"), None)
                if first_note_on_idx is not None:
                    program_change = {
                        "type": "program_change",
                        "channel": 0,
                        "program": 1,  # 钢琴
                        "time": 0
                    }
                    events.insert(first_note_on_idx, program_change)
            
            # 降低所有note_on的velocity
            for event in events:
                if event.get("type") == "note_on":
                    original_vel = event.get("velocity", 64)
                    if original_vel > 70:
                        # 降低到30-70之间
                        new_vel = max(30, min(70, original_vel - 30))
                        event["velocity"] = new_vel
                    elif original_vel < 30:
                        # 保持在30以上
                        event["velocity"] = max(30, original_vel)
                    else:
                        # 在范围内，稍微降低
                        event["velocity"] = max(30, min(70, original_vel - 10))
        
        new_midi_json["events"] = events
        return new_midi_json
    
    except Exception as e:
        print(f"  自动风格转换失败: {e}")
        return midi_json


def calculate_midi_json_duration(midi_json, ticks_per_beat=480):
    """
    计算MIDI JSON的总持续时间（秒）。
    """
    try:
        bpm = midi_json.get("tempo", 120)
        tempo = mido.bpm2tempo(bpm)  # 微秒/拍
        
        # 计算总ticks
        total_ticks = 0
        events = midi_json.get("events", [])
        for event in events:
            total_ticks += int(event.get("time", 0))
        
        # 转换为秒
        seconds_per_tick = (tempo / 1_000_000.0) / ticks_per_beat
        duration = total_ticks * seconds_per_tick
        
        return duration
    except Exception as e:
        print(f"计算MIDI JSON持续时间时出错: {e}")
        return None


def extract_audio_features_and_midi(audio_file_path):
    """
    从音频文件提取特征（BPM, 调性等）和MIDI事件文本。
    使用 librosa 提取 BPM 和 chroma（调性），basic_pitch 转录为 MIDI。
    返回：(特征描述字符串 + MIDI JSON 字符串, 音频持续时间秒数, 原始MIDI JSON对象, 原始MIDI持续时间秒数)
    """
    try:
        print(f"\n正在分析音频文件: {audio_file_path}")
        
        # 加载音频
        y, sr = librosa.load(audio_file_path, sr=None)

        # 提取 BPM
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        bpm = tempo.item() if hasattr(tempo, 'item') else float(tempo)
        if bpm <= 0:
            bpm = 120.0  # 默认 BPM
            print("BPM 检测失败，使用默认 120。")

        # 提取调性（chroma）
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        if chroma.shape[0] != 12:
            raise ValueError(f"Chroma 形状无效: {chroma.shape}")
        chroma_mean = chroma.mean(axis=1)
        key_str = estimate_key(chroma_mean)

        # 简单描述：持续时间、能量等
        duration = librosa.get_duration(y=y, sr=sr)
        rms = librosa.feature.rms(y=y)[0]
        energy = float(rms.mean().item()) if hasattr(rms.mean(), 'item') else float(rms.mean())

        features_desc = f"""
音频特征：
- BPM: {bpm:.2f}
- 调性: {key_str}
- 持续时间: {duration:.2f} 秒
- 平均能量: {energy:.4f}
"""

        # 使用 basic_pitch 转录为 MIDI
        print("正在使用 basic_pitch 转录为 MIDI...")
        model_output, midi_data, note_events = predict(audio_file_path)

        # 转换 PrettyMIDI 对象为 bytes
        if isinstance(midi_data, pretty_midi.PrettyMIDI):
            midi_buffer = BytesIO()
            midi_data.write(midi_buffer)
            midi_bytes = midi_buffer.getvalue()
            if not midi_bytes or len(midi_bytes) == 0:
                raise ValueError("MIDI数据为空，无法转换")
        else:
            raise ValueError(f"Unexpected MIDI data type: {type(midi_data)}")

        # 将 MIDI bytes 转换为 JSON 事件（使用 mido）
        try:
            mid = mido.MidiFile(file=BytesIO(midi_bytes))
        except Exception as e:
            raise ValueError(f"无法解析MIDI数据: {e}")
        
        # 转换为简化的MIDI JSON格式（单个events数组）
        events = []
        for track in mid.tracks:
            for msg in track:
                if msg.is_meta:
                    if msg.type == 'set_tempo':
                        # tempo信息已在features中
                        continue
                    # 跳过其他meta事件
                    continue
                
                # 转换为事件字典
                event_dict = {
                    'time': msg.time,
                    'type': msg.type,
                    'channel': getattr(msg, 'channel', 0)
                }
                
                if msg.type == 'note_on':
                    event_dict['note'] = msg.note
                    event_dict['velocity'] = msg.velocity
                elif msg.type == 'note_off':
                    event_dict['note'] = msg.note
                    event_dict['velocity'] = getattr(msg, 'velocity', 0)
                elif msg.type == 'program_change':
                    event_dict['program'] = msg.program
                
                events.append(event_dict)

        midi_json = {
            "tempo": int(bpm),
            "events": events
        }

        midi_json_str = json.dumps(midi_json, indent=2)
        
        # 计算原始MIDI的时间长度
        original_midi_duration = calculate_midi_json_duration(midi_json)
        if original_midi_duration is None:
            original_midi_duration = duration  # 如果计算失败，使用音频持续时间

        print(f"音频分析完成: BPM={bpm:.2f}, 调性={key_str}, 持续时间={duration:.2f}秒")
        print(f"提取到 {len(events)} 个MIDI事件")
        print(f"原始MIDI持续时间: {original_midi_duration:.2f} 秒")

        return (features_desc + "\n\nMIDI 事件序列（JSON）:\n" + midi_json_str, duration, midi_json, original_midi_duration)

    except Exception as e:
        print(f"音频提取错误: {e}")
        import traceback
        traceback.print_exc()
        # 回退到基本特征（无 MIDI）
        default_duration = 30.0  # 默认持续时间
        default_midi_json = {"tempo": 120, "events": []}
        return (f"""
音频特征（部分提取失败）：
- BPM: 120.00 (默认)
- 调性: C major (默认)
- 持续时间: 未知
- 平均能量: 0.5000 (默认)

MIDI 事件序列（JSON）：{{ "tempo": 120, "events": [] }}  # 转录失败
""", default_duration, default_midi_json, default_duration)


def call_qwen_llm(messages):
    """
    调用 Qwen LLM API。
    """
    try:
        response = Generation.call(
            api_key=API_KEY,
            model="qwen3-max",
            messages=messages,
            result_format="message",
        )
        
        if response.status_code == 200:
            content = response.output.choices[0].message.content
            return content
        else:
            print(f"API调用失败: {response.status_code}")
            print(f"错误信息: {response.message}")
            return None
    except Exception as e:
        print(f"调用LLM时出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def extract_midi_json_from_text(text):
    """
    从LLM返回的文本中提取MIDI JSON。
    尝试多种方法提取JSON。
    """
    # 方法1: 尝试直接解析整个文本为JSON
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and ("tempo" in parsed or "events" in parsed):
            return parsed
    except:
        pass
    
    # 方法2: 查找JSON代码块（支持多行）
    json_patterns = [
        r'```json\s*(\{[\s\S]*?\})\s*```',
        r'```\s*(\{[\s\S]*?"tempo"[\s\S]*?"events"[\s\S]*?\})\s*```',
        r'(\{[\s\S]*?"tempo"[\s\S]*?"events"[\s\S]*?\})',
    ]
    
    for pattern in json_patterns:
        matches = re.findall(pattern, text, re.DOTALL)
        for match in matches:
            try:
                parsed = json.loads(match)
                if isinstance(parsed, dict) and ("tempo" in parsed or "events" in parsed):
                    return parsed
            except:
                continue
    
    # 方法3: 查找包含"tempo"和"events"的JSON对象（更精确的匹配）
    try:
        # 找到所有可能的JSON对象
        brace_count = 0
        start_idx = -1
        for i, char in enumerate(text):
            if char == '{':
                if brace_count == 0:
                    start_idx = i
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0 and start_idx != -1:
                    json_str = text[start_idx:i+1]
                    try:
                        parsed = json.loads(json_str)
                        if isinstance(parsed, dict) and ("tempo" in parsed or "events" in parsed):
                            return parsed
                    except:
                        pass
    except:
        pass
    
    # 如果都失败了，返回None
    print("警告: 无法从LLM响应中提取有效的JSON")
    print(f"响应文本前500字符: {text[:500]}...")
    return None


def calculate_midi_duration(mid_file):
    """
    计算MIDI文件的实际持续时间（秒）。
    """
    try:
        # 计算所有轨道中的最大时间
        max_time = 0.0
        tempo = 500000  # 默认120 BPM (500000微秒/拍)
        ticks_per_beat = mid_file.ticks_per_beat
        
        for track in mid_file.tracks:
            current_time = 0.0
            
            for msg in track:
                if msg.is_meta and msg.type == 'set_tempo':
                    tempo = msg.tempo
                else:
                    # 将ticks转换为秒
                    ticks = msg.time
                    seconds_per_tick = (tempo / 1_000_000.0) / ticks_per_beat
                    current_time += ticks * seconds_per_tick
                    max_time = max(max_time, current_time)
        
        return max_time
    except Exception as e:
        print(f"计算MIDI持续时间时出错: {e}")
        # 如果计算失败，尝试使用pretty_midi加载文件来计算
        try:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.mid', delete=False) as tmp:
                mid_file.save(tmp.name)
                pm = pretty_midi.PrettyMIDI(tmp.name)
                duration = pm.get_end_time()
                os.unlink(tmp.name)
                return duration
        except Exception as e2:
            print(f"使用pretty_midi计算持续时间也失败: {e2}")
            return None


def adjust_midi_duration(mid_file, target_duration):
    """
    调整MIDI文件的持续时间以匹配目标持续时间。
    如果音乐太短，会重复音乐片段；如果太长，会按比例缩放。
    """
    try:
        # 计算当前持续时间
        current_duration = calculate_midi_duration(mid_file)
        
        if current_duration is None or current_duration <= 0:
            print("无法计算当前MIDI持续时间，跳过调整。")
            return mid_file
        
        if abs(current_duration - target_duration) < 0.1:
            # 持续时间已经匹配（误差小于0.1秒）
            print(f"✅ MIDI持续时间已匹配: {current_duration:.2f} 秒")
            return mid_file
        
        # 创建新的MIDI文件
        new_mid = MidiFile(ticks_per_beat=mid_file.ticks_per_beat)
        
        if current_duration < target_duration:
            # 音乐太短，需要重复音乐片段
            print(f"⚠️ MIDI持续时间太短: {current_duration:.2f} 秒 -> {target_duration:.2f} 秒")
            print(f"将重复音乐片段以达到目标持续时间...")
            
            # 计算需要完整重复多少次，以及最后一次需要缩放多少
            full_repeats = int(target_duration / current_duration)
            remaining_duration = target_duration - (full_repeats * current_duration)
            
            # 复制所有轨道
            for track in mid_file.tracks:
                new_track = MidiTrack()
                
                # 提取非meta消息（这些是需要重复的音乐内容）
                music_messages = []
                meta_messages = []
                
                for msg in track:
                    if msg.is_meta:
                        meta_messages.append(msg)
                    else:
                        music_messages.append(msg)
                
                # 只在开始时添加meta消息
                for meta_msg in meta_messages:
                    new_track.append(meta_msg)
                
                # 完整重复音乐消息
                for repeat in range(full_repeats):
                    for msg in music_messages:
                        new_track.append(msg)
                
                # 如果还有剩余时间，添加部分重复
                if remaining_duration > 0.1:  # 至少0.1秒才添加
                    scale = remaining_duration / current_duration
                    print(f"添加部分重复: {remaining_duration:.2f} 秒 (缩放比例: {scale:.3f})")
                    for msg in music_messages:
                        if hasattr(msg, 'time'):
                            new_time = int(msg.time * scale)
                            try:
                                msg_dict = msg.dict()
                                msg_type = msg_dict.pop('type')
                                msg_dict.pop('time', None)
                                new_msg = Message(msg_type, time=new_time, **msg_dict)
                                new_track.append(new_msg)
                            except:
                                new_track.append(msg)
                        else:
                            new_track.append(msg)
                
                new_mid.tracks.append(new_track)
        else:
            # 音乐太长，需要按比例缩放
            scale_factor = target_duration / current_duration
            print(f"⚠️ 调整MIDI持续时间: {current_duration:.2f} 秒 -> {target_duration:.2f} 秒 (缩放比例: {scale_factor:.3f})")
            
            # 复制所有轨道，缩放时间
            for track in mid_file.tracks:
                new_track = MidiTrack()
                for msg in track:
                    # 缩放delta time
                    if hasattr(msg, 'time'):
                        new_time = max(1, int(msg.time * scale_factor))  # 至少1 tick
                        # 创建新消息，保持其他属性不变
                        try:
                            if msg.is_meta:
                                msg_dict = msg.dict()
                                msg_type = msg_dict.pop('type')
                                msg_dict.pop('time', None)
                                new_msg = MetaMessage(msg_type, time=new_time, **msg_dict)
                            else:
                                msg_dict = msg.dict()
                                msg_type = msg_dict.pop('type')
                                msg_dict.pop('time', None)
                                new_msg = Message(msg_type, time=new_time, **msg_dict)
                            new_track.append(new_msg)
                        except Exception as e:
                            print(f"警告: 无法创建新消息，使用原消息: {e}")
                            try:
                                msg.time = new_time
                                new_track.append(msg)
                            except:
                                new_track.append(msg)
                    else:
                        new_track.append(msg)
                new_mid.tracks.append(new_track)
        
        return new_mid
    except Exception as e:
        print(f"调整MIDI持续时间时出错: {e}")
        import traceback
        traceback.print_exc()
        return mid_file


def midi_json_to_mid_file(midi_json, output_path, target_duration=None):
    """
    将MIDI JSON转换为MID文件。
    target_duration: 目标持续时间（秒），如果提供，将调整生成的MIDI以匹配此持续时间。
    """
    try:
        mid = MidiFile(ticks_per_beat=480)
        
        # 创建meta轨道设置tempo
        meta_track = MidiTrack()
        mid.tracks.append(meta_track)
        bpm = midi_json.get("tempo", 120)
        meta_track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))
        
        # 创建主轨道
        track = MidiTrack()
        mid.tracks.append(track)
        
        events = midi_json.get("events", [])
        processed_count = 0
        
        for event in events:
            try:
                delta_time = int(event.get("time", 0))
                msg_type = event.get("type")
                channel = int(event.get("channel", 0))
                
                if msg_type == "note_on":
                    note = event.get("note")
                    velocity = event.get("velocity")
                    if note is not None and velocity is not None:
                        track.append(Message("note_on", channel=channel, note=int(note), 
                                            velocity=int(velocity), time=delta_time))
                        processed_count += 1
                elif msg_type == "note_off":
                    note = event.get("note")
                    if note is not None:
                        track.append(Message("note_off", channel=channel, note=int(note), 
                                            velocity=int(event.get("velocity", 0)), time=delta_time))
                        processed_count += 1
                elif msg_type == "program_change":
                    program = event.get("program")
                    if program is not None:
                        track.append(Message("program_change", channel=channel, 
                                            program=int(program), time=delta_time))
                        processed_count += 1
            except Exception as e:
                print(f"警告: 跳过格式错误的事件: {event}, 错误: {e}")
                continue
        
        # 如果提供了目标持续时间，调整MIDI
        if target_duration is not None:
            print(f"\n正在调整MIDI持续时间以匹配原始音频: {target_duration:.2f} 秒")
            mid = adjust_midi_duration(mid, target_duration)
        
        mid.save(output_path)
        print(f"MIDI文件已保存: {output_path} (处理了 {processed_count} 个事件)")
        
        # 验证最终持续时间
        final_duration = calculate_midi_duration(mid)
        if final_duration is not None:
            print(f"MIDI实际持续时间: {final_duration:.2f} 秒")
            if target_duration is not None:
                diff = abs(final_duration - target_duration)
                if diff < 0.5:
                    print(f"✅ MIDI持续时间已匹配目标（误差: {diff:.2f} 秒）")
                else:
                    print(f"⚠️ 警告: MIDI持续时间与目标持续时间相差 {diff:.2f} 秒")
        
        return output_path
    except Exception as e:
        print(f"转换MIDI文件时出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def convert_mid_to_audio(mid_file_path):
    """
    使用midi_to_audio.py将MID文件转换为音频。
    """
    try:
        mid_file = Path(mid_file_path)
        if not mid_file.exists():
            print(f"错误: MIDI文件不存在: {mid_file_path}")
            return None
        
        # 生成输出文件名
        output_base = mid_file.stem
        wav_path = mid_file.parent / f"{output_base}_render.wav"
        mp3_path = mid_file.parent / f"{output_base}_render.mp3"
        
        # 调用midi_to_audio.py
        script_path = Path(__file__).parent / "midi_to_audio.py"
        if not script_path.exists():
            print(f"错误: 找不到midi_to_audio.py: {script_path}")
            return None
        
        print(f"\n正在使用midi_to_audio.py转换MIDI为音频...")
        cmd = [sys.executable, str(script_path), str(mid_file), 
               "--wav", str(wav_path), "--mp3", str(mp3_path)]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"音频转换成功!")
            print(f"WAV文件: {wav_path}")
            if mp3_path.exists():
                print(f"MP3文件: {mp3_path}")
            return str(wav_path)
        else:
            print(f"音频转换失败:")
            print(result.stderr)
            return None
    except Exception as e:
        print(f"调用midi_to_audio.py时出错: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """
    主函数：实现循环对话界面。
    """
    print("=" * 60)
    print("欢迎使用音乐LLM对话脚本！")
    print("=" * 60)
    
    # 第一步：上传音频文件
    print("\n【步骤1】请提供原始音频文件路径:")
    audio_path = input("音频文件路径: ").strip().replace('"', '').replace("'", "")
    
    if not os.path.exists(audio_path):
        print(f"错误: 文件 '{audio_path}' 不存在！")
        return
    
    # 提取音频特征和MIDI
    audio_text, original_duration, original_midi_json, original_midi_duration = extract_audio_features_and_midi(audio_path)
    
    print(f"\n原始音频持续时间: {original_duration:.2f} 秒")
    print(f"原始MIDI持续时间: {original_midi_duration:.2f} 秒")
    
    # 初始化对话消息
    system_prompt = """你是一个专业的音乐制作助手。你的任务是根据用户提供的原始音频特征和MIDI信息，以及用户的音乐需求描述，生成满足需求的MIDI数据。

用户会提供：
1. 原始音频的特征（BPM、调性、持续时间等）
2. 原始音频的MIDI事件序列（JSON格式）
3. 音乐需求描述（如"转换成适合安静场景下听的音乐"、"转换为摇滚风格"等）

你需要：
1. 理解用户的音乐需求
2. **必须根据需求实际改变音乐参数**，不能返回与原始MIDI完全相同的数据
3. 基于原始MIDI数据，根据需求进行转换和调整（只改变风格，不改变时间长度）
4. 返回一个有效的MIDI JSON格式，包含：
   - "tempo": BPM值（整数）
   - "events": MIDI事件数组，每个事件包含：
     - "time": 时间偏移（整数，单位：ticks，通常480 ticks = 1拍）
     - "type": 事件类型（"note_on", "note_off", "program_change"等）
     - "channel": MIDI通道（0-15）
     - 对于note_on/note_off: "note"（音符，0-127）, "velocity"（力度，0-127）
     - 对于program_change: "program"（乐器程序，0-127）

风格转换指导（必须根据需求实际应用，不能只返回原始数据）：

- **摇滚风格**：
  * 必须添加program_change事件，使用电吉他（program 25-28）或失真吉他（program 30-31）
  * 必须增加力度（velocity 80-127），特别是重拍，原始力度如果低于80，必须提高到80以上
  * 可以添加低音贝斯（program 33-40），使用通道1-2
  * 可以添加鼓点（使用通道9，program 0，音符35-42）
  * 保持强节奏感，力度变化明显
  * 示例：如果原始velocity是60，摇滚风格应该改为90-110
  
- **爵士风格**：
  * 必须添加program_change事件，使用爵士钢琴（program 1-2）或爵士吉他（program 26）
  * 可以添加萨克斯（program 65-66）或小号（program 56-57），使用不同通道
  * 力度变化更细腻（velocity 40-100），但必须与原始不同
  * 可以添加复杂的和声，使用多个通道
  * 节奏更自由，可以有轻微的摇摆感
  * 示例：如果原始是单一乐器，爵士风格应该添加萨克斯或小号作为主旋律
  
- **安静场景/轻柔风格**：
  * 必须添加program_change事件，使用钢琴（program 1）或弦乐（program 48-51）
  * 必须降低力度（velocity 30-70），原始力度如果高于70，必须降低到70以下
  * 使用更柔和的乐器音色
  * 减少重拍，增加延音
  * 示例：如果原始velocity是100，轻柔风格应该改为40-60
  
- **其他风格**：
  * 根据具体需求调整乐器（program_change）、力度（velocity）、和声（音符组合）
  * 可以使用多个通道来添加不同乐器
  * 保持时间结构不变，只改变音色和力度
  * **关键**：必须实际改变参数，不能返回与原始完全相同的数据

重要提示：
- **必须保持原始音频的时间长度**：生成的MIDI总时长必须与原始音频完全一致
- **必须实际改变音乐参数**：不能返回与原始MIDI完全相同的数据，必须根据需求改变乐器、力度、和声等
- 只改变音乐风格（如乐器、音色、力度、和声等），不要改变时间结构
- 保持原始MIDI事件的时间相对关系，只调整音符、力度、乐器等参数
- 如果原始MIDI没有program_change事件，必须添加以改变乐器
- 必须改变velocity值来体现不同风格
- 可以使用多个通道来添加不同乐器（如主旋律、伴奏、低音等）
- 请确保返回的JSON格式正确，可以直接被解析
- 请只返回JSON格式的MIDI数据，不要包含其他解释文字
- 如果需要，可以用```json代码块包裹
- 确保所有事件的时间值都是整数
- 确保音符、力度、通道等值都在有效范围内"""
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"原始音频信息:\n{audio_text}\n\n请先分析这段音频的特征，并确认你已理解音频的MIDI结构。"}
    ]
    
    print("\n正在与LLM建立连接...")
    response = call_qwen_llm(messages)
    if response:
        print(f"\nLLM初始响应:\n{response[:200]}...\n")
        messages.append({"role": "assistant", "content": response})
    else:
        print("警告: LLM初始响应失败，但可以继续尝试对话。")
    
    # 循环对话
    conversation_count = 0
    while True:
        print("\n" + "=" * 60)
        print("【对话循环】请输入你的音乐需求（输入'quit'或'exit'退出）:")
        print("例如:")
        print("  - 转换成适合安静场景下听的音乐")
        print("  - 转换为摇滚风格")
        print("  - 加快节奏，提高音调")
        print("  - 改为爵士风格")
        print("=" * 60)
        
        user_input = input("\n你的需求: ").strip()
        
        if user_input.lower() in ['quit', 'exit', '退出', 'q']:
            print("\n感谢使用！再见！")
            break
        
        if not user_input:
            print("输入不能为空，请重新输入。")
            continue
        
        # 根据用户需求生成具体的风格转换指令
        style_instructions = ""
        if "摇滚" in user_input or "rock" in user_input.lower():
            style_instructions = """
【摇滚风格转换规则 - 必须严格执行】：
1. **乐器改变（必须）**：
   - 在第一个note_on事件之前，添加program_change事件，channel=0, program=25（电吉他）
   - 如果原始有多个通道，为每个通道添加program_change
   - 可以添加低音贝斯：channel=1, program=33（电贝斯）
   
2. **力度改变（必须）**：
   - 所有note_on事件的velocity必须提高到80-127之间
   - 如果原始velocity < 80，必须改为80-127
   - 重拍（每小节第一拍）的velocity应该更高（100-127）
   
3. **可以添加的元素**：
   - 可以添加鼓点：channel=9, program=0, note=36（底鼓）, note=38（军鼓）
   - 可以添加低音线：使用channel=1，添加低音音符（比主旋律低1-2个八度）
   
4. **时间结构**：
   - 保持所有事件的time值不变
   - 只改变program、velocity、note（用于和声）"""
        
        elif "爵士" in user_input or "jazz" in user_input.lower():
            style_instructions = """
【爵士风格转换规则 - 必须严格执行】：
1. **乐器改变（必须）**：
   - 在第一个note_on事件之前，添加program_change事件，channel=0, program=65（中音萨克斯）
   - 或者使用channel=0, program=26（爵士吉他）
   - 可以添加钢琴伴奏：channel=1, program=1（钢琴）
   
2. **力度改变（必须）**：
   - 所有note_on事件的velocity调整为40-100之间
   - 如果原始velocity > 100，必须降低到40-100
   - 如果原始velocity < 40，提高到40-100
   - 力度变化要细腻，不要过于极端
   
3. **可以添加的元素**：
   - 可以添加和声：使用channel=1，添加和弦音符（主旋律上方或下方3-7度）
   - 可以添加低音线：使用channel=2，添加低音音符
   
4. **时间结构**：
   - 保持所有事件的time值不变
   - 只改变program、velocity、note（用于和声）"""
        
        elif "安静" in user_input or "轻柔" in user_input or "soft" in user_input.lower():
            style_instructions = """
【轻柔风格转换规则 - 必须严格执行】：
1. **乐器改变（必须）**：
   - 在第一个note_on事件之前，添加program_change事件，channel=0, program=1（钢琴）
   - 或者使用channel=0, program=48（弦乐合奏）
   
2. **力度改变（必须）**：
   - 所有note_on事件的velocity必须降低到30-70之间
   - 如果原始velocity > 70，必须降低到30-70
   - 轻柔的力度变化，避免突然的强音
   
3. **时间结构**：
   - 保持所有事件的time值不变
   - 只改变program、velocity"""
        
        # 添加用户需求到对话（明确要求保持时间长度并实际改变风格）
        user_message = f"""原始音频信息:
{audio_text}

重要要求：
- 原始音频持续时间: {original_duration:.2f} 秒
- 原始MIDI持续时间: {original_midi_duration:.2f} 秒
- **必须保持原始时间长度不变**，只改变音乐风格
- **必须实际改变音乐参数**：不能返回与原始MIDI完全相同的数据

请根据以下需求修改MIDI（只改变风格，不改变时间长度）:
{user_input}

{style_instructions}

【强制要求 - 必须执行】：
1. **必须添加program_change事件**：在第一个note_on事件之前，根据风格添加program_change事件
2. **必须改变所有velocity值**：根据风格调整所有note_on事件的velocity值
3. **必须保持time值不变**：所有事件的time值必须与原始MIDI完全相同
4. **必须返回完整的MIDI JSON**：包含所有原始事件，但修改了program和velocity

请返回修改后的MIDI JSON数据，确保：
- 总时长与原始音频一致（{original_duration:.2f} 秒）
- 必须包含program_change事件来改变乐器
- 必须改变所有note_on事件的velocity值来体现风格
- 不能返回与原始MIDI完全相同的数据
- 所有事件的time值必须与原始MIDI完全相同"""
        messages.append({"role": "user", "content": user_message})
        
        # 调用LLM
        print("\n正在处理你的需求...")
        response = call_qwen_llm(messages)
        
        if not response:
            print("LLM调用失败，请重试。")
            messages.pop()  # 移除失败的用户消息
            continue
        
        print(f"\nLLM响应:\n{response}\n")
        messages.append({"role": "assistant", "content": response})
        
        # 提取MIDI JSON
        midi_json = extract_midi_json_from_text(response)
        
        if not midi_json:
            print("无法从响应中提取MIDI JSON，请重试或修改需求描述。")
            continue
        
        # 验证生成的MIDI是否实际改变了
        print("\n正在验证生成的MIDI是否实际改变了风格...")
        
        if midi_json == original_midi_json:
            print("❌ 错误: 生成的MIDI与原始MIDI完全相同，没有实际改变风格！")
            print("正在自动应用风格转换...")
            
            # 自动应用风格转换
            midi_json = apply_style_transformation(original_midi_json, user_input, original_duration)
            
            if midi_json == original_midi_json:
                print("⚠️ 自动转换失败，请手动指定风格。")
                retry = input("\n是否继续生成MIDI文件？(y/n): ").strip().lower()
                if retry != 'y':
                    continue
            else:
                print("✅ 已自动应用风格转换")
        
        # 检查是否包含program_change事件
        has_program_change = any(event.get("type") == "program_change" for event in midi_json.get("events", []))
        original_has_program_change = any(event.get("type") == "program_change" for event in original_midi_json.get("events", []))
        
        if not has_program_change:
            print("⚠️ 警告: 生成的MIDI没有包含program_change事件，可能没有改变乐器。")
            print("正在自动添加program_change事件...")
            # 自动添加program_change
            if "摇滚" in user_input or "rock" in user_input.lower():
                midi_json = apply_style_transformation(midi_json, "摇滚", original_duration)
            elif "爵士" in user_input or "jazz" in user_input.lower():
                midi_json = apply_style_transformation(midi_json, "爵士", original_duration)
            elif "安静" in user_input or "轻柔" in user_input or "soft" in user_input.lower():
                midi_json = apply_style_transformation(midi_json, "轻柔", original_duration)
        else:
            program_changes = [event.get("program") for event in midi_json.get("events", []) if event.get("type") == "program_change"]
            print(f"✅ 检测到乐器改变: 使用了乐器程序 {program_changes}")
        
        # 检查velocity是否有变化
        original_velocities = [event.get("velocity", 0) for event in original_midi_json.get("events", []) if event.get("type") in ["note_on", "note_off"]]
        new_velocities = [event.get("velocity", 0) for event in midi_json.get("events", []) if event.get("type") in ["note_on", "note_off"]]
        
        if original_velocities and new_velocities:
            original_vel_set = set(original_velocities)
            new_vel_set = set(new_velocities)
            
            if original_vel_set == new_vel_set:
                print("⚠️ 警告: 生成的MIDI的velocity值与原始MIDI相同，可能没有改变力度。")
                print("正在自动调整velocity值...")
                # 自动调整velocity
                if "摇滚" in user_input or "rock" in user_input.lower():
                    midi_json = apply_style_transformation(midi_json, "摇滚", original_duration)
                elif "爵士" in user_input or "jazz" in user_input.lower():
                    midi_json = apply_style_transformation(midi_json, "爵士", original_duration)
                elif "安静" in user_input or "轻柔" in user_input or "soft" in user_input.lower():
                    midi_json = apply_style_transformation(midi_json, "轻柔", original_duration)
            else:
                # 检查变化是否明显
                original_avg = sum(original_velocities) / len(original_velocities) if original_velocities else 0
                new_avg = sum(new_velocities) / len(new_velocities) if new_velocities else 0
                diff = abs(original_avg - new_avg)
                
                if diff < 10:  # 变化不明显
                    print(f"⚠️ 警告: velocity变化不明显（平均变化 {diff:.1f}），正在自动增强...")
                    if "摇滚" in user_input or "rock" in user_input.lower():
                        midi_json = apply_style_transformation(midi_json, "摇滚", original_duration)
                    elif "爵士" in user_input or "jazz" in user_input.lower():
                        midi_json = apply_style_transformation(midi_json, "爵士", original_duration)
                    elif "安静" in user_input or "轻柔" in user_input or "soft" in user_input.lower():
                        midi_json = apply_style_transformation(midi_json, "轻柔", original_duration)
                else:
                    print(f"✅ 检测到力度变化: 原始力度范围 {min(original_velocities) if original_velocities else 0}-{max(original_velocities) if original_velocities else 0}, "
                          f"新力度范围 {min(new_velocities) if new_velocities else 0}-{max(new_velocities) if new_velocities else 0}")
                    print(f"   平均力度变化: {original_avg:.1f} -> {new_avg:.1f} (变化 {diff:.1f})")
        
        # 检查事件数量是否有变化
        original_event_count = len(original_midi_json.get("events", []))
        new_event_count = len(midi_json.get("events", []))
        if original_event_count != new_event_count:
            print(f"✅ 检测到事件数量变化: 原始 {original_event_count} 个事件，新 {new_event_count} 个事件")
        else:
            print(f"ℹ️ 事件数量未变: {original_event_count} 个事件")
        
        # 转换为MID文件（传递原始时间长度）
        conversation_count += 1
        output_mid_path = f"output_{conversation_count}.mid"
        print(f"\n正在将MIDI JSON转换为MID文件: {output_mid_path}")
        print(f"目标持续时间: {original_duration:.2f} 秒（将自动调整以匹配）")
        mid_file = midi_json_to_mid_file(midi_json, output_mid_path, target_duration=original_duration)
        
        if not mid_file:
            print("MIDI文件生成失败。")
            continue
        
        # 转换为音频
        audio_file = convert_mid_to_audio(mid_file)
        
        if audio_file:
            print(f"\n✅ 处理完成！")
            print(f"   MIDI文件: {mid_file}")
            print(f"   音频文件: {audio_file}")
        else:
            print(f"\n⚠️ MIDI文件已生成，但音频转换失败。")
            print(f"   你可以手动使用midi_to_audio.py转换: python midi_to_audio.py {mid_file}")


if __name__ == "__main__":
    main()


