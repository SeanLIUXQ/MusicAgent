import openai
import json
import os
import mido
from mido import MidiFile, MidiTrack, Message, MetaMessage
from io import BytesIO
import librosa  # 用于音频特征提取
import numpy as np  # 添加 numpy 以支持 key 估计
from basic_pitch.inference import predict  # 用于音频到MIDI转录
from basic_pitch import ICASSP_2022_MODEL_PATH
import pretty_midi  # 用于MIDI到音频合成和 bytes 转换
import io  # 添加 io 以支持 BytesIO for write
import re # 导入正则表达式库，用于清理和提取JSON

# Qwen API 配置（通过阿里云 DashScope）
# 请确保已设置环境变量 DASHSCOPE_API_KEY，或在此处直接赋值
# DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
DASHSCOPE_API_KEY = "sk-b2819f02c4e7492a83b7b04059094470" # 示例Key，请替换为你自己的
BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
MODEL_NAME = "qwen3-max"


# 假设用户环境已安装必要库：openai, mido, librosa, basic-pitch, pretty-midi, numpy。
# 如果未安装，请运行：pip install openai mido librosa basic-pitch pretty_midi numpy

def estimate_key(chroma_mean):
    """
    使用 Krumhansl-Schmuckler 算法从 chroma 估计 key（major/minor）。
    这是 librosa 缺少内置 key 估计的替代实现。
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
        print(f"Key 估计错误: {e}")
        return "C major"  # 默认回退


def extract_audio_features_and_midi(audio_file_path):
    """
    从音频文件提取特征（BPM, 调性等）和MIDI事件文本。
    使用 librosa 提取 BPM 和 chroma（调性），basic_pitch 转录为 MIDI。
    返回：(特征描述字符串 + MIDI JSON 字符串, 持续时间秒数)
    """
    try:
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
        - 风格提示: 基于简单钢琴旋律（用户输入）
        """

        # 使用 basic_pitch 转录为 MIDI
        print("Predicting MIDI for", audio_file_path + "...")
        model_output, midi_data, note_events = predict(audio_file_path)

        # 转换 PrettyMIDI 对象为 bytes
        if isinstance(midi_data, pretty_midi.PrettyMIDI):
            midi_buffer = io.BytesIO()
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
        midi_json = {
            "tempo": int(bpm),
            "tracks": []
        }
        for i, track in enumerate(mid.tracks):
            events = []
            for msg in track:
                if msg.is_meta and msg.type == 'set_tempo':
                    continue  # 跳过 tempo，已在根级
                event_dict = msg.dict()
                event_dict['time'] = msg.time  # delta time
                events.append(event_dict)
            if events:  # 只添加非空轨
                midi_json["tracks"].append({
                    "name": f"Track {i + 1}",
                    "events": events
                })

        midi_json_str = json.dumps(midi_json, indent=2)

        return (features_desc + "\n\nMIDI 事件序列（JSON）:\n" + midi_json_str, duration)

    except Exception as e:
        print(f"音频提取错误: {e}")
        # 回退到基本特征（无 MIDI）
        default_duration = 30.0  # 默认持续时间
        return (f"""
        音频特征（部分提取失败）：
        - BPM: 120.00 (默认)
        - 调性: C major (默认)
        - 持续时间: 未知
        - 平均能量: 0.5000 (默认)
        - 风格提示: 基于简单钢琴旋律（用户输入）

        MIDI 事件序列（JSON）：{{ "tempo": 120, "tracks": [] }}  # 转录失败，请检查 basic_pitch
        """, default_duration)

def call_qwen_llm(prompt, audio_text, target_duration=None):
    """
    调用 Qwen LLM，并使用更健壮的JSON解析逻辑。
    target_duration: 目标持续时间（秒），如果提供，将在提示词中明确要求匹配此持续时间。
    """
    if not DASHSCOPE_API_KEY:
        raise ValueError("请设置环境变量 DASHSCOPE_API_KEY")

    client = openai.OpenAI(
        api_key=DASHSCOPE_API_KEY,
        base_url=BASE_URL,
        timeout=120.0,  # 增加超时时间到120秒
    )

    # 优化提示词，要求LLM展示思考步骤
    duration_requirement = ""
    if target_duration is not None:
        # 计算需要的大概事件数量（假设每个事件平均0.1秒）
        estimated_events = int(target_duration * 10)
        duration_requirement = f"""
【重要要求 - 必须严格遵守】
1. 生成的MIDI音乐必须精确匹配原始音频的持续时间：{target_duration:.2f} 秒。
2. 请生成足够多的MIDI事件来覆盖整个 {target_duration:.2f} 秒的持续时间。
3. 建议生成至少 {estimated_events} 个事件，确保音乐在整个持续时间内都有内容。
4. 不要只生成几秒钟的音乐然后停止，必须生成完整的 {target_duration:.2f} 秒音乐。
5. 如果音乐需要重复，请明确重复整个音乐片段，确保覆盖整个持续时间。
6. 所有事件的时间戳（time字段）应该累加起来达到 {target_duration:.2f} 秒的总时长。
"""
    
    full_prompt = f"""你是一个音乐生成专家。以下是原始音频的文本表示（特征 + MIDI 事件）：
{audio_text}

用户需求：{prompt}
{duration_requirement}

请按照以下步骤创作音乐：

【思考步骤】（可选，可以省略）
1. 分析原始音频特征（BPM、调性、风格等）
2. 理解用户需求，确定需要调整的方向
3. 设计新的音乐特征（BPM、调性、描述等）
4. 构思MIDI事件序列，确保音乐完整流畅{"，并且总时长精确匹配原始音频持续时间" if target_duration is not None else ""}

【关键输出要求 - 必须严格遵守】
1. 如果你要展示思考步骤，请先输出思考步骤
2. 然后必须输出一个完整的JSON对象
3. JSON必须使用 ```json 和 ``` 包裹，格式如下（注意：只使用单个轨道，不要多个轨道）：
```json
{{
    "features": {{
        "bpm": 120,
        "key": "C major",
        "duration": {target_duration if target_duration is not None else 30.0},
        "energy": 0.5,
        "description": "简要描述新音乐风格"
    }},
    "midi": {{
        "tempo": 120,
        "events": [
            {{"type": "note_on", "channel": 0, "note": 60, "velocity": 64, "time": 0}},
            {{"type": "note_off", "channel": 0, "note": 60, "velocity": 0, "time": 480}},
            {{"type": "note_on", "channel": 0, "note": 62, "velocity": 64, "time": 480}},
            {{"type": "note_off", "channel": 0, "note": 62, "velocity": 0, "time": 480}}
        ]
    }}
}}
```
4. 【严格要求】JSON结构必须严格遵循以下规则：
   - "features"对象必须包含：bpm（数字）、key（字符串）、duration（数字）、energy（数字）、description（字符串）
   - "midi"对象必须包含：tempo（数字）、events（数组，包含所有MIDI事件）
   - 每个事件必须包含：type（字符串，必须是"note_on"、"note_off"或"program_change"）、channel（数字0-15）、time（数字，delta time）
   - note_on事件必须包含：note（数字0-127）、velocity（数字0-127）
   - note_off事件必须包含：note（数字0-127）、velocity（数字，通常为0）
   - program_change事件必须包含：program（数字0-127）
   - 不要使用tracks数组，直接使用events数组
5. JSON必须完整，不能截断，必须包含所有必要的字段
6. 不要在任何地方添加额外的文本、解释或注释
7. 确保JSON格式完全正确，可以被直接解析
8. 所有数字必须是有效的数字类型，不能是字符串

【重要提醒】
- JSON必须用 ```json 和 ``` 包裹
- JSON必须完整，包含所有闭合括号
- 不要输出任何JSON之外的内容（除了可选的思考步骤）
- 确保MIDI事件序列完整，覆盖整个持续时间{"（{target_duration:.2f} 秒）" if target_duration is not None else ""}
- 只使用单个轨道，所有事件都在一个events数组中

现在请生成音乐JSON。"""

    messages = [{"role": "user", "content": full_prompt}]

    try:
        stream = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.7,
            max_tokens=8192, # 增加max_tokens以容纳更复杂的音乐和完整JSON
            stream=True
        )

        content = ""
        thinking_content = ""  # 用于存储思考步骤
        json_started = False
        buffer = ""
        
        print("\n" + "="*60)
        print("🤖 LLM 正在生成中...")
        print("="*60 + "\n")
        
        # 实时显示进度和思考步骤
        chunk_count = 0
        for chunk in stream:
            try:
                if chunk.choices and len(chunk.choices) > 0 and hasattr(chunk.choices[0], 'delta'):
                    delta = chunk.choices[0].delta.content if hasattr(chunk.choices[0].delta, 'content') else None
                    if delta is not None:
                        content += delta
                        chunk_count += 1
                        
                        # 检测JSON开始
                        if not json_started:
                            buffer += delta
                            # 检查是否开始JSON部分
                            if '{' in buffer or '```json' in buffer.lower():
                                # 如果buffer中有思考内容，先显示
                                if buffer and not buffer.strip().startswith('{'):
                                    thinking_content += buffer
                                    # 格式化显示思考步骤
                                    if any(keyword in buffer for keyword in ["思考", "步骤", "分析", "理解", "设计", "构思"]):
                                        print(f"\n💭 {buffer}", end='', flush=True)
                                    else:
                                        print(buffer, end='', flush=True)
                                buffer = ""
                                json_started = True
                            else:
                                thinking_content += delta
                                # 高亮显示关键思考步骤
                                if any(keyword in delta for keyword in ["思考", "步骤", "分析", "理解", "设计", "构思", "【", "】"]):
                                    print(f"\n💭 {delta}", end='', flush=True)
                                else:
                                    print(delta, end='', flush=True)
                        else:
                            # JSON部分，直接显示
                            print(delta, end='', flush=True)
                        
                        # 每100个chunk显示一次进度提示（不覆盖，换行显示）
                        if chunk_count % 100 == 0 and chunk_count > 0:
                            print(f"\n[进度: 已接收 {chunk_count} 个数据块]", flush=True)
            except Exception as e:
                print(f"\n⚠️ 处理数据块时出错: {e}")
                continue
        
        print("\n\n" + "="*60)
        print("✅ 生成完成！")
        print("="*60 + "\n")

        if not content:
            print("LLM 返回空内容！检查 API Key、模型名或网络。")
            return None

        # 保存原始内容用于调试（只在调试模式下显示）
        print(f"\n📊 接收统计: 总长度 {len(content)} 字符, 数据块 {chunk_count} 个")
        print(f"🔍 [DEBUG] 原始内容前200字符: {repr(content[:200])}")
        print(f"🔍 [DEBUG] 原始内容后200字符: {repr(content[-200:])}")

        # --- 改进的JSON提取和清理逻辑 ---
        json_str = ""
        
        # 方法1: 优先匹配被 ```json ... ``` 包裹的代码块（使用贪婪匹配）
        # 改进：允许代码块前后有空白字符，使用贪婪匹配确保匹配完整JSON
        print(f"\n🔍 [DEBUG] 开始提取JSON...")
        match = re.search(r'```\s*json\s*(\{.*\})\s*```', content, re.DOTALL)
        if match:
            json_str = match.group(1)
            print(f"✅ 使用方法1提取JSON（```json代码块）")
            print(f"🔍 [DEBUG] 提取的JSON长度: {len(json_str)} 字符")
            print(f"🔍 [DEBUG] 提取的JSON前200字符: {repr(json_str[:200])}")
        else:
            # 方法2: 匹配 ``` 代码块（可能是markdown格式，不包含json标记）
            # 改进：检查代码块内容是否以{开始，使用贪婪匹配
            print(f"🔍 [DEBUG] 方法1失败，尝试方法2...")
            match = re.search(r'```\s*(\{.*\})\s*```', content, re.DOTALL)
            if match and match.group(1).strip().startswith('{'):
                json_str = match.group(1)
                print(f"✅ 使用方法2提取JSON（```代码块）")
                print(f"🔍 [DEBUG] 提取的JSON长度: {len(json_str)} 字符")
                print(f"🔍 [DEBUG] 提取的JSON前200字符: {repr(json_str[:200])}")
            else:
                # 方法3: 如果没有代码块标记，寻找被 {...} 包裹的第一个完整JSON对象
                # 使用更智能的匹配，找到最外层的{}，正确处理字符串中的花括号
                start_index = content.find('{')
                if start_index != -1:
                    # 从第一个{开始，找到匹配的}
                    depth = 0
                    end_index = start_index
                    in_string = False
                    escape_next = False
                    
                    for i in range(start_index, len(content)):
                        char = content[i]
                        
                        if escape_next:
                            escape_next = False
                            continue
                        
                        if char == '\\':
                            escape_next = True
                            continue
                        
                        if char == '"' and not escape_next:
                            in_string = not in_string
                            continue
                        
                        if not in_string:
                            if char == '{':
                                depth += 1
                            elif char == '}':
                                depth -= 1
                                if depth == 0:
                                    end_index = i
                                    break
                    
                    if end_index > start_index:
                        json_str = content[start_index:end_index+1]
                        print(f"✅ 使用方法3提取JSON（深度匹配）")
                        print(f"🔍 [DEBUG] 提取的JSON长度: {len(json_str)} 字符")
                        print(f"🔍 [DEBUG] 提取的JSON前200字符: {repr(json_str[:200])}")
                        print(f"🔍 [DEBUG] 开始位置: {start_index}, 结束位置: {end_index}")
                    else:
                        print(f"⚠️ 深度匹配未找到完整的JSON对象")
                        print(f"🔍 [DEBUG] 开始位置: {start_index}, 结束位置: {end_index}")

        if not json_str:
            print("\n❌ 错误：在LLM的输出中未找到有效的JSON结构。")
            print("\n" + "="*60)
            print("🔍 调试信息")
            print("="*60)
            print(f"原始内容长度: {len(content)} 字符")
            print(f"\n原始内容预览（前500字符）:\n{content[:500]}")
            if len(content) > 500:
                print(f"\n原始内容结尾（后500字符）:\n{content[-500:]}")
            # 检查是否包含JSON相关关键词
            if '{' in content:
                first_brace = content.find('{')
                print(f"\n✅ 发现 '{{' 字符，位置: {first_brace}")
                print(f"第一个 '{{' 前后文本:\n{repr(content[max(0, first_brace-50):first_brace+100])}")
            else:
                print("\n❌ 未发现 '{' 字符")
            if '```' in content:
                print("✅ 发现代码块标记 '```'")
            else:
                print("❌ 未发现代码块标记 '```'")
            print("="*60 + "\n")
            return None
        
        print(f"✅ 成功提取JSON，长度: {len(json_str)} 字符")
        print(f"🔍 [DEBUG] JSON字符串统计:")
        quote_count = json_str.count('"')
        print(f"  - 开括号数量: {json_str.count('{')}")
        print(f"  - 闭括号数量: {json_str.count('}')}")
        print(f"  - 开方括号数量: {json_str.count('[')}")
        print(f"  - 闭方括号数量: {json_str.count(']')}")
        print(f"  - 引号数量: {quote_count}")
        
        # 验证JSON是否完整（检查是否以{开始，以}结束）
        json_str = json_str.strip()
        print(f"🔍 [DEBUG] 清理后的JSON长度: {len(json_str)} 字符")
        starts_with_brace = json_str.startswith('{')
        ends_with_brace = json_str.endswith('}')
        print(f"🔍 [DEBUG] 是否以花括号开始: {starts_with_brace}, 是否以花括号结束: {ends_with_brace}")
        if not json_str.startswith('{') or not json_str.endswith('}'):
            print("⚠️ 警告：JSON可能不完整，尝试修复...")
            print(f"🔍 [DEBUG] 修复前JSON前100字符: {repr(json_str[:100])}")
            print(f"🔍 [DEBUG] 修复前JSON后100字符: {repr(json_str[-100:])}")
            # 尝试找到最后一个完整的}
            last_brace = json_str.rfind('}')
            if last_brace > 0:
                json_str = json_str[:last_brace+1]
                print(f"✅ 已修复：截取到最后一个 '}}' 位置 {last_brace}")
            else:
                print("❌ 错误：无法找到完整的JSON结构")
                print(f"JSON字符串预览: {json_str[:200]}")
                return None

        # 清理和修复JSON字符串
        def clean_json_string(s):
            # 首先移除注释（// 和 /* */）- 但要小心，不要移除字符串中的注释
            # 简单方法：移除行尾注释（不在引号内的）
            lines = s.split('\n')
            cleaned_lines = []
            for line in lines:
                # 检查是否在字符串中
                in_string = False
                escape_next = False
                comment_pos = -1
                
                for i, char in enumerate(line):
                    if escape_next:
                        escape_next = False
                        continue
                    if char == '\\':
                        escape_next = True
                        continue
                    if char == '"' and not escape_next:
                        in_string = not in_string
                        continue
                    if not in_string and char == '/' and i + 1 < len(line) and line[i+1] == '/':
                        comment_pos = i
                        break
                
                if comment_pos >= 0:
                    line = line[:comment_pos]
                cleaned_lines.append(line)
            
            s = '\n'.join(cleaned_lines)
            
            # 移除块注释 /* */（不在字符串中的）
            # 这里简化处理，直接移除所有块注释
            s = re.sub(r'/\*.*?\*/', '', s, flags=re.DOTALL)
            
            # 移除尾随逗号（在 } 或 ] 之前）
            s = re.sub(r',(\s*[}\]])', r'\1', s)
            
            # 修复未加引号的键（但要小心，不要替换值中的内容）
            # 只修复明显的未加引号键（在 { 或 , 之后，: 之前）
            # 使用更精确的正则表达式，避免替换值中的内容
            s = re.sub(r'([{,]\s*)([a-zA-Z_][a-zA-Z0-9_]*)\s*:', r'\1"\2":', s)
            
            # 移除非ASCII字符（但保留JSON字符串值中的中文字符）
            # 只删除JSON结构外的非ASCII字符，保留JSON字符串值中的中文字符
            # 使用更智能的方法：只删除不在引号内的非ASCII字符
            result = []
            in_string = False
            escape_next = False
            
            for char in s:
                if escape_next:
                    escape_next = False
                    result.append(char)
                    continue
                if char == '\\':
                    escape_next = True
                    result.append(char)
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    result.append(char)
                    continue
                # 如果在字符串内，保留所有字符（包括中文）
                if in_string:
                    result.append(char)
                else:
                    # 在字符串外，只保留ASCII字符和必要的JSON结构字符
                    if ord(char) >= 0x20 and ord(char) <= 0x7E or char in '\n\r\t':
                        result.append(char)
                    # 否则删除（这些是JSON结构外的非ASCII字符）
            
            s = ''.join(result)
            
            return s

        # 严格的JSON验证函数
        def validate_json_structure(data):
            """验证JSON结构是否符合要求"""
            errors = []
            print(f"\n🔍 [DEBUG] 开始验证JSON结构...")
            print(f"🔍 [DEBUG] JSON顶层类型: {type(data).__name__}")
            
            # 检查顶层结构
            if not isinstance(data, dict):
                errors.append("JSON根对象必须是字典")
                print(f"🔍 [DEBUG] ❌ JSON根对象类型错误: {type(data).__name__}")
                return False, errors
            
            print(f"🔍 [DEBUG] ✅ JSON根对象是字典")
            print(f"🔍 [DEBUG] JSON顶层键: {list(data.keys())}")
            
            # 检查features字段
            if "features" not in data:
                errors.append("缺少'features'字段")
                print(f"🔍 [DEBUG] ❌ 缺少'features'字段")
            else:
                features = data["features"]
                print(f"🔍 [DEBUG] ✅ 找到'features'字段，类型: {type(features).__name__}")
                if not isinstance(features, dict):
                    errors.append("'features'必须是对象")
                    print(f"🔍 [DEBUG] ❌ 'features'类型错误: {type(features).__name__}")
                else:
                    print(f"🔍 [DEBUG] 'features'键: {list(features.keys())}")
                    required_features = ["bpm", "key", "duration", "energy", "description"]
                    for field in required_features:
                        if field not in features:
                            errors.append(f"'features'缺少字段: {field}")
                            print(f"🔍 [DEBUG] ❌ 'features'缺少字段: {field}")
                        else:
                            print(f"🔍 [DEBUG] ✅ 'features.{field}'存在，值: {features[field]}, 类型: {type(features[field]).__name__}")
                    # 验证字段类型
                    if "bpm" in features and not isinstance(features["bpm"], (int, float)):
                        errors.append("'features.bpm'必须是数字")
                        print(f"🔍 [DEBUG] ❌ 'features.bpm'类型错误: {type(features['bpm']).__name__}")
                    if "duration" in features and not isinstance(features["duration"], (int, float)):
                        errors.append("'features.duration'必须是数字")
                        print(f"🔍 [DEBUG] ❌ 'features.duration'类型错误: {type(features['duration']).__name__}")
                    if "energy" in features and not isinstance(features["energy"], (int, float)):
                        errors.append("'features.energy'必须是数字")
                        print(f"🔍 [DEBUG] ❌ 'features.energy'类型错误: {type(features['energy']).__name__}")
                    if "key" in features and not isinstance(features["key"], str):
                        errors.append("'features.key'必须是字符串")
                        print(f"🔍 [DEBUG] ❌ 'features.key'类型错误: {type(features['key']).__name__}")
                    if "description" in features and not isinstance(features["description"], str):
                        errors.append("'features.description'必须是字符串")
                        print(f"🔍 [DEBUG] ❌ 'features.description'类型错误: {type(features['description']).__name__}")
            
            # 检查midi字段
            if "midi" not in data:
                errors.append("缺少'midi'字段")
                print(f"🔍 [DEBUG] ❌ 缺少'midi'字段")
            else:
                midi = data["midi"]
                print(f"🔍 [DEBUG] ✅ 找到'midi'字段，类型: {type(midi).__name__}")
                if not isinstance(midi, dict):
                    errors.append("'midi'必须是对象")
                    print(f"🔍 [DEBUG] ❌ 'midi'类型错误: {type(midi).__name__}")
                else:
                    print(f"🔍 [DEBUG] 'midi'键: {list(midi.keys())}")
                    # 检查tempo
                    if "tempo" not in midi:
                        errors.append("'midi'缺少'tempo'字段")
                        print(f"🔍 [DEBUG] ❌ 'midi'缺少'tempo'字段")
                    elif not isinstance(midi["tempo"], (int, float)):
                        errors.append("'midi.tempo'必须是数字")
                        print(f"🔍 [DEBUG] ❌ 'midi.tempo'类型错误: {type(midi['tempo']).__name__}")
                    else:
                        print(f"🔍 [DEBUG] ✅ 'midi.tempo'存在，值: {midi['tempo']}, 类型: {type(midi['tempo']).__name__}")
                    
                    # 检查events（新格式，单个轨道）
                    if "events" not in midi:
                        errors.append("'midi'缺少'events'字段（请使用单个轨道格式）")
                        print(f"🔍 [DEBUG] ❌ 'midi'缺少'events'字段")
                    elif not isinstance(midi["events"], list):
                        errors.append("'midi.events'必须是数组")
                        print(f"🔍 [DEBUG] ❌ 'midi.events'类型错误: {type(midi['events']).__name__}")
                    else:
                        print(f"🔍 [DEBUG] ✅ 'midi.events'存在，类型: {type(midi['events']).__name__}, 长度: {len(midi['events'])}")
                        # 验证每个事件
                        for i, event in enumerate(midi["events"]):
                            if i < 3:  # 只打印前3个事件的详细信息
                                print(f"🔍 [DEBUG] 验证事件[{i}]: {event}")
                            if not isinstance(event, dict):
                                errors.append(f"事件[{i}]必须是对象")
                                continue
                            
                            # 检查必需字段
                            if "type" not in event:
                                errors.append(f"事件[{i}]缺少'type'字段")
                                continue  # 如果缺少type，跳过后续检查
                            
                            event_type = event.get("type")
                            if event_type not in ["note_on", "note_off", "program_change"]:
                                errors.append(f"事件[{i}]的'type'必须是'note_on'、'note_off'或'program_change'，当前值: {repr(event_type)}")
                                continue  # 如果type无效，跳过后续检查
                            
                            if "channel" not in event:
                                errors.append(f"事件[{i}]缺少'channel'字段")
                            elif not isinstance(event["channel"], (int, float)) or not (0 <= int(event["channel"]) <= 15):
                                errors.append(f"事件[{i}]的'channel'必须是0-15之间的数字，当前值: {repr(event.get('channel'))}")
                            
                            if "time" not in event:
                                errors.append(f"事件[{i}]缺少'time'字段")
                            elif not isinstance(event["time"], (int, float)):
                                errors.append(f"事件[{i}]的'time'必须是数字，当前值: {repr(event.get('time'))}")
                            
                            # 根据类型检查特定字段
                            if event_type == "note_on":
                                if "note" not in event:
                                    errors.append(f"事件[{i}]（note_on）缺少'note'字段")
                                elif not isinstance(event.get("note"), (int, float)) or not (0 <= int(event.get("note")) <= 127):
                                    errors.append(f"事件[{i}]（note_on）的'note'必须是0-127之间的数字")
                                if "velocity" not in event:
                                    errors.append(f"事件[{i}]（note_on）缺少'velocity'字段")
                                elif not isinstance(event.get("velocity"), (int, float)) or not (0 <= int(event.get("velocity")) <= 127):
                                    errors.append(f"事件[{i}]（note_on）的'velocity'必须是0-127之间的数字")
                            elif event_type == "note_off":
                                if "note" not in event:
                                    errors.append(f"事件[{i}]（note_off）缺少'note'字段")
                                elif not isinstance(event.get("note"), (int, float)) or not (0 <= int(event.get("note")) <= 127):
                                    errors.append(f"事件[{i}]（note_off）的'note'必须是0-127之间的数字")
                            elif event_type == "program_change":
                                if "program" not in event:
                                    errors.append(f"事件[{i}]（program_change）缺少'program'字段")
                                elif not isinstance(event.get("program"), (int, float)) or not (0 <= int(event.get("program")) <= 127):
                                    errors.append(f"事件[{i}]（program_change）的'program'必须是0-127之间的数字")
                    
                    # 检查是否使用了旧的tracks格式（不应该有）
                    if "tracks" in midi:
                        errors.append("检测到旧的'tracks'格式，请使用单个'events'数组格式")
                        print(f"🔍 [DEBUG] ❌ 检测到旧的'tracks'格式")
            
            if errors:
                print(f"🔍 [DEBUG] ❌ JSON验证失败，共 {len(errors)} 个错误")
                return False, errors
            print(f"🔍 [DEBUG] ✅ JSON验证通过")
            return True, []
        
        # 尝试解析JSON，带修复机制
        for attempt in range(5):
            try:
                if attempt == 0:
                    # 第一次尝试：直接解析
                    print(f"\n🔍 [DEBUG] 尝试 {attempt + 1}/5: 直接解析JSON")
                    result = json.loads(json_str)
                    print(f"🔍 [DEBUG] ✅ JSON解析成功")
                    print(f"🔍 [DEBUG] 解析后的顶层键: {list(result.keys())}")
                    # 验证结果是否包含必要字段
                    if "midi" in result and "features" in result:
                        # 严格验证JSON结构
                        is_valid, errors = validate_json_structure(result)
                        if is_valid:
                            print(f"🔍 [DEBUG] ✅ JSON结构验证通过")
                            return result
                        else:
                            print(f"⚠️ JSON结构验证失败:")
                            for error in errors[:10]:  # 只显示前10个错误
                                print(f"  - {error}")
                            if len(errors) > 10:
                                print(f"  ... 还有 {len(errors) - 10} 个错误")
                            print(f"尝试修复...")
                            raise json.JSONDecodeError("Invalid JSON structure", json_str, 0)
                    else:
                        print(f"🔍 [DEBUG] ❌ JSON缺少必要字段")
                        print(f"🔍 [DEBUG] 存在的键: {list(result.keys())}")
                        print(f"警告：JSON缺少必要字段，尝试修复...")
                        raise json.JSONDecodeError("Missing required fields", json_str, 0)
                elif attempt == 1:
                    # 第二次尝试：清理后解析
                    print(f"\n🔍 [DEBUG] 尝试 {attempt + 1}/5: 清理后解析JSON")
                    cleaned = clean_json_string(json_str)
                    print(f"🔍 [DEBUG] 清理前长度: {len(json_str)}, 清理后长度: {len(cleaned)}")
                    result = json.loads(cleaned)
                    print(f"🔍 [DEBUG] ✅ JSON解析成功")
                    if "midi" in result and "features" in result:
                        is_valid, errors = validate_json_structure(result)
                        if is_valid:
                            print(f"🔍 [DEBUG] ✅ JSON结构验证通过")
                            return result
                        raise json.JSONDecodeError("Invalid JSON structure", cleaned, 0)
                    raise json.JSONDecodeError("Missing required fields", cleaned, 0)
                elif attempt == 2:
                    # 第三次尝试：更激进的清理（使用clean_json_string，它会保留JSON字符串值中的中文字符）
                    print(f"\n🔍 [DEBUG] 尝试 {attempt + 1}/5: 更激进的清理")
                    cleaned = clean_json_string(json_str)
                    print(f"🔍 [DEBUG] 清理前长度: {len(json_str)}, 清理后长度: {len(cleaned)}")
                    result = json.loads(cleaned)
                    print(f"🔍 [DEBUG] ✅ JSON解析成功")
                    if "midi" in result and "features" in result:
                        is_valid, errors = validate_json_structure(result)
                        if is_valid:
                            print(f"🔍 [DEBUG] ✅ JSON结构验证通过")
                            return result
                        raise json.JSONDecodeError("Invalid JSON structure", cleaned, 0)
                    raise json.JSONDecodeError("Missing required fields", cleaned, 0)
                elif attempt == 3:
                    # 第四次尝试：修复不完整的JSON（如果被截断）
                    # 尝试补全缺失的闭合括号
                    open_braces = json_str.count('{')
                    close_braces = json_str.count('}')
                    if open_braces > close_braces:
                        missing = open_braces - close_braces
                        # 尝试智能补全
                        fixed_json = json_str
                        # 检查是否在数组中
                        open_brackets = json_str.count('[')
                        close_brackets = json_str.count(']')
                        if open_brackets > close_brackets:
                            fixed_json += ']' * (open_brackets - close_brackets)
                        # 补全对象闭合
                        fixed_json += '}' * missing
                        result = json.loads(fixed_json)
                        if "midi" in result and "features" in result:
                            is_valid, errors = validate_json_structure(result)
                            if is_valid:
                                print("✅ 成功修复不完整的JSON")
                                return result
                            else:
                                print(f"⚠️ 修复后的JSON结构验证失败，尝试下一个方法...")
                    raise json.JSONDecodeError("Failed to fix", json_str, 0)
                else:
                    # 第五次尝试：最激进的修复
                    # 使用clean_json_string清理（它会保留JSON字符串值中的中文字符）
                    cleaned = clean_json_string(json_str)
                    # 尝试补全
                    open_braces = cleaned.count('{')
                    close_braces = cleaned.count('}')
                    if open_braces > close_braces:
                        cleaned += '}' * (open_braces - close_braces)
                    open_brackets = cleaned.count('[')
                    close_brackets = cleaned.count(']')
                    if open_brackets > close_brackets:
                        cleaned += ']' * (open_brackets - close_brackets)
                    result = json.loads(cleaned)
                    if "midi" in result and "features" in result:
                        is_valid, errors = validate_json_structure(result)
                        if is_valid:
                            print("✅ 成功修复JSON（激进模式）")
                            return result
                        else:
                            print(f"⚠️ 修复后的JSON结构验证失败")
                    raise json.JSONDecodeError("Failed to fix", cleaned, 0)
            except json.JSONDecodeError as e:
                if attempt < 4:
                    print(f"⚠️ JSON解析失败（尝试 {attempt + 1}/5）: {str(e)[:100]}")
                    continue
                else:
                    # 最后一次尝试失败，输出调试信息
                    print(f"\n❌ JSON解析最终失败: {e}")
                    print("\n" + "="*60)
                    print("🔍 详细调试信息")
                    print("="*60)
                    print(f"原始JSON字符串长度: {len(json_str)} 字符")
                    print(f"\n原始JSON字符串前500字符:\n{repr(json_str[:500])}")
                    if len(json_str) > 500:
                        print(f"\n原始JSON字符串后500字符:\n{repr(json_str[-500:])}")
                    # 尝试找到错误位置
                    try:
                        error_pos = e.pos
                        print(f"\n错误位置: {error_pos}")
                        print(f"错误位置前后文本:\n{repr(json_str[max(0, error_pos-50):error_pos+50])}")
                    except:
                        pass
                    # 统计括号数量
                    open_braces_count = json_str.count('{')
                    open_brackets_count = json_str.count('[')
                    close_braces_count = json_str.count('}')
                    close_brackets_count = json_str.count(']')
                    print(f"\n括号统计:")
                    print(f"  开括号: {{={open_braces_count}, [={open_brackets_count}")
                    print(f"  闭括号: }}={close_braces_count}, ]={close_brackets_count}")
                    if open_braces_count != close_braces_count:
                        print(f"  ⚠️ 花括号不匹配: 缺少 {abs(open_braces_count - close_braces_count)} 个")
                    if open_brackets_count != close_brackets_count:
                        print(f"  ⚠️ 方括号不匹配: 缺少 {abs(open_brackets_count - close_brackets_count)} 个")
                    print("="*60 + "\n")
                    return None

    except Exception as e:
        print(f"LLM 调用时发生未知错误: {e}")
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
            print(f"MIDI持续时间已匹配: {current_duration:.2f} 秒")
            return mid_file
        
        # 创建新的MIDI文件
        new_mid = MidiFile(ticks_per_beat=mid_file.ticks_per_beat)
        
        if current_duration < target_duration:
            # 音乐太短，需要重复音乐片段
            print(f"MIDI持续时间太短: {current_duration:.2f} 秒 -> {target_duration:.2f} 秒")
            print(f"将重复音乐片段以达到目标持续时间...")
            
            # 计算需要重复多少次（向上取整）
            repeat_count = int(target_duration / current_duration) + 1
            
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
                
                # 计算需要完整重复多少次，以及最后一次需要缩放多少
                full_repeats = int(target_duration / current_duration)
                remaining_duration = target_duration - (full_repeats * current_duration)
                
                # 完整重复音乐消息
                for repeat in range(full_repeats):
                    for msg in music_messages:
                        # 直接添加消息（保持原样）
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
                                # 如果创建失败，直接添加原消息
                                new_track.append(msg)
                        else:
                            new_track.append(msg)
                
                new_mid.tracks.append(new_track)
        else:
            # 音乐太长，需要按比例缩放
            scale_factor = target_duration / current_duration
            print(f"调整MIDI持续时间: {current_duration:.2f} 秒 -> {target_duration:.2f} 秒 (缩放比例: {scale_factor:.3f})")
            
            # 复制所有轨道，缩放时间
            for track in mid_file.tracks:
                new_track = MidiTrack()
                for msg in track:
                    # 缩放delta time
                    if hasattr(msg, 'time'):
                        new_time = int(msg.time * scale_factor)
                        # 创建新消息，保持其他属性不变
                        try:
                            if msg.is_meta:
                                # 对于MetaMessage，需要特殊处理
                                msg_dict = msg.dict()
                                msg_type = msg_dict.pop('type')
                                msg_dict.pop('time', None)  # 移除time，稍后单独设置
                                # 创建新的MetaMessage
                                new_msg = MetaMessage(msg_type, time=new_time, **msg_dict)
                            else:
                                # 对于普通Message
                                msg_dict = msg.dict()
                                msg_type = msg_dict.pop('type')
                                msg_dict.pop('time', None)  # 移除time，稍后单独设置
                                new_msg = Message(msg_type, time=new_time, **msg_dict)
                            new_track.append(new_msg)
                        except Exception as e:
                            # 如果创建失败，直接修改原消息的time属性（如果可能）
                            print(f"警告: 无法创建新消息，使用原消息: {e}")
                            # 尝试直接修改time属性
                            try:
                                msg.time = new_time
                                new_track.append(msg)
                            except:
                                # 如果无法修改，直接添加原消息
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


def json_to_midi_and_audio(music_json, output_base="output", target_duration=None):
    """
    将 LLM 返回的 JSON 转换为 MIDI 文件，并合成音频（WAV）。
    使用单个轨道格式（events数组）。
    target_duration: 目标持续时间（秒），如果提供，将调整生成的MIDI以匹配此持续时间。
    """
    if not music_json or "midi" not in music_json:
        print("无效的 music_json 数据，无法生成MIDI。")
        return None
        
    # MIDI 部分
    mid = MidiFile(ticks_per_beat=480)
    
    # 优先使用JSON中定义的tempo
    bpm = music_json.get("midi", {}).get("tempo", 120)
    meta_track = MidiTrack()
    mid.tracks.append(meta_track)
    meta_track.append(MetaMessage('set_tempo', tempo=mido.bpm2tempo(bpm)))

    # 使用单个轨道格式（events数组）
    midi_data = music_json.get("midi", {})
    events = midi_data.get("events", [])
    
    print(f"\n🔍 [DEBUG] 开始处理MIDI事件...")
    print(f"🔍 [DEBUG] MIDI数据键: {list(midi_data.keys())}")
    print(f"🔍 [DEBUG] 事件数量: {len(events)}")
    
    if not events:
        print("警告: MIDI数据中没有事件，无法生成MIDI。")
        return None
    
    # 创建单个轨道
    track = MidiTrack()
    mid.tracks.append(track)

    processed_count = 0
    skipped_count = 0
    for i, event in enumerate(events):
        if i < 5:  # 只打印前5个事件的详细信息
            print(f"🔍 [DEBUG] 处理事件[{i}]: {event}")
        try:
            delta_time = int(event.get("time", 0))
            msg_type = event.get("type")

            if msg_type == "note_on":
                # 安全地获取note和velocity，如果不存在则使用默认值
                note = event.get("note")
                velocity = event.get("velocity")
                if note is None or velocity is None:
                    print(f"⚠️ 警告: note_on事件[{i}]缺少必要字段 (note={note}, velocity={velocity})，跳过")
                    skipped_count += 1
                    continue
                if i < 5:
                    print(f"🔍 [DEBUG] 添加note_on事件: note={note}, velocity={velocity}, channel={event.get('channel', 0)}, time={delta_time}")
                track.append(
                    Message("note_on", channel=int(event.get("channel", 0)), note=int(note), velocity=int(velocity),
                            time=delta_time))
                processed_count += 1
            elif msg_type == "note_off":
                # 安全地获取note，velocity默认为0
                note = event.get("note")
                if note is None:
                    print(f"⚠️ 警告: note_off事件[{i}]缺少note字段，跳过")
                    skipped_count += 1
                    continue
                if i < 5:
                    print(f"🔍 [DEBUG] 添加note_off事件: note={note}, channel={event.get('channel', 0)}, time={delta_time}")
                track.append(
                    Message("note_off", channel=int(event.get("channel", 0)), note=int(note), velocity=int(event.get("velocity", 0)),
                            time=delta_time))
                processed_count += 1
            elif msg_type == "program_change":
                # 安全地获取program
                program = event.get("program")
                if program is None:
                    print(f"⚠️ 警告: program_change事件[{i}]缺少program字段，跳过")
                    skipped_count += 1
                    continue
                if i < 5:
                    print(f"🔍 [DEBUG] 添加program_change事件: program={program}, channel={event.get('channel', 0)}, time={delta_time}")
                track.append(Message("program_change", channel=int(event.get("channel", 0)), program=int(program),
                                     time=delta_time))
                processed_count += 1
            else:
                print(f"⚠️ 警告: 未知的事件类型: {msg_type}，跳过事件[{i}]")
                skipped_count += 1
            # 可以根据需要在这里扩展支持其他MIDI事件类型
        except (ValueError, KeyError, TypeError) as e:
            print(f"❌ 跳过格式错误的MIDI事件[{i}]: {event}，错误: {e}")
            import traceback
            traceback.print_exc()
            skipped_count += 1
    
    print(f"\n🔍 [DEBUG] MIDI事件处理完成:")
    print(f"  - 总事件数: {len(events)}")
    print(f"  - 成功处理: {processed_count}")
    print(f"  - 跳过/失败: {skipped_count}")
    print(f"  - 轨道中的消息数: {len(track)}")


    # 如果提供了目标持续时间，调整MIDI以匹配
    if target_duration is not None:
        print(f"\n目标持续时间: {target_duration:.2f} 秒")
        mid = adjust_midi_duration(mid, target_duration)
    
    midi_filename = f"{output_base}.mid"
    mid.save(midi_filename)
    print(f"MIDI 文件已保存: {midi_filename}")
    
    # 验证最终持续时间
    final_duration = calculate_midi_duration(mid)
    if final_duration is not None:
        print(f"MIDI实际持续时间: {final_duration:.2f} 秒")
        if target_duration is not None:
            diff = abs(final_duration - target_duration)
            if diff > 0.5:
                print(f"⚠️ 警告: MIDI持续时间与目标持续时间相差 {diff:.2f} 秒")
            else:
                print(f"✅ MIDI持续时间已匹配目标（误差: {diff:.2f} 秒）")

    # 音频合成（可选，需要 fluidsynth 和 SoundFont）
    try:
        pm = pretty_midi.PrettyMIDI(midi_filename)
        audio_filename = f"{output_base}.wav"
        # 注意：synthesize需要正确配置FluidSynth和SoundFont才能工作
        # 在某些系统上可能需要指定soundfont路径，例如：
        # pm.synthesize(fs=44100, soundfont='/path/to/your/soundfont.sf2')
        audio_data = pm.synthesize(fs=44100) 
        import soundfile as sf
        sf.write(audio_filename, audio_data, 44100)
        print(f"音频文件已合成: {audio_filename}")
    except Exception as e:
        print(f"音频合成失败: {e}")
        print("提示：音频合成依赖于FluidSynth和SoundFont文件。请确保它们已正确安装和配置。")
        print("MIDI文件已成功生成，你可以使用其他工具播放它。")

    # 打印特征
    features = music_json.get("features", {})
    print(f"生成音乐特征: BPM={features.get('bpm')}, Key={features.get('key')}, Description={features.get('description')}")

    return midi_filename


def main():
    print("欢迎使用 Qwen MIDI 生成对话脚本（带音频转录）！")
    print("首先，请提供原始音频文件路径：")
    audio_path = input("音频文件路径: ").strip().replace('"', '') # 移除可能存在的引号

    if not os.path.exists(audio_path):
        print(f"文件 '{audio_path}' 不存在！退出。")
        return

    print("提取音频特征和 MIDI 文本...")
    audio_text, original_duration = extract_audio_features_and_midi(audio_path)
    print(f"提取完成！原始音频持续时间: {original_duration:.2f} 秒")
    print("预览：")
    print(audio_text[:500] + "..." if len(audio_text) > 500 else audio_text)

    print("\n开始对话循环。输入你的音乐需求，或输入 'quit' 退出。")
    while True:
        demand = input("\n> 你的音乐需求 (例如 '转换成摇滚风格'): ").strip()
        if demand.lower() in ['quit', 'exit', 'q']:
            print("再见！")
            break

        if not demand:
            print("请输入有效需求。")
            continue

        print("调用 Qwen LLM 生成新音乐...")
        music_json = call_qwen_llm(demand, audio_text, target_duration=original_duration)

        if music_json:
            # 创建一个合法的文件名
            safe_demand = re.sub(r'[\\/*?:"<>|]', "", demand)
            filename = f"generated_{safe_demand[:20].replace(' ', '_')}"
            
            json_to_midi_and_audio(music_json, filename, target_duration=original_duration)
            print("生成流程完成！")
        else:
            print("由于之前的错误，生成失败。")


if __name__ == "__main__":
    main()