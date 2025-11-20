#!/usr/bin/env python3
"""
multi_agent_music_system.py
--------------------------------------
一个独立的多智能体音乐生成系统：
  用户输入提示 -> 多智能体协作 -> 生成 ABC 音乐代码
  -> 自动转换为 MIDI 和 WAV 文件

依赖：
  pip install openai music21 midi2audio
  并安装系统工具：
    - fluidsynth + soundfont.sf2  (推荐)
    或
    - timidity

运行示例：
...

"""

import os
import re
import json
import argparse
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from openai import OpenAI
import mido
from music21 import converter, midi

try:
    from midi2audio import FluidSynth

    HAVE_MIDI2AUDIO = True
except ImportError:
    HAVE_MIDI2AUDIO = False
# ------------------------------
# 可选：通义 Qwen-Omni 音频 → Sonic Pi 模块
# ------------------------------
try:
    from qwen_omni_audio_to_sonicpi import call_qwen_audio_to_code
    HAVE_QWEN_AUDIO = True
except Exception:
    # 没装这个文件 / 环境没配好时，继续使用旧的 basic_pitch 流程
    HAVE_QWEN_AUDIO = False


# ------------------------------
# Sonic Pi 保留字和内置函数列表
# ------------------------------

SONIC_PI_RESERVED_WORDS = {
    # 核心函数
    'play', 'sample', 'sleep', 'live_loop', 'use_bpm', 'use_synth', 'with_fx',
    'sync', 'cue', 'in_thread',

    # 音阶和和弦
    'chord', 'scale', 'note', 'octave', 'tonic', 'degree',

    # 效果与控制
    'amp', 'pan', 'rate', 'attack', 'decay', 'sustain', 'release',
    'cutoff', 'res', 'slide', 'phase', 'mix', 'pre_amp',

    # 音色
    'sine', 'saw', 'tri', 'square', 'dsaw', 'fm', 'subpulse', 'prophet',
    'tb303', 'blade', 'piano', 'pluck', 'hoover', 'zawa',

    # 采样
    'drum', 'loop', 'perc', 'elec', 'ambi', 'guit', 'bass', 'vinyl',

    # 模式与模式工具
    'ring', 'range', 'spread', 'choose', 'shuffle', 'tick', 'look',
    'line', 'ramp', 'sine', 'cosine', 'triangle', 'square', 'saw',

    # 控制和流程
    'if', 'else', 'elsif', 'unless', 'while', 'until', 'for', 'loop',
    'break', 'next', 'return', 'def', 'end', 'do', 'then',

    # Ruby 关键字
    'class', 'module', 'require', 'include', 'extend', 'attr_reader',
    'attr_writer', 'attr_accessor', 'private', 'public', 'protected',
    'true', 'false', 'nil', 'self', 'super',

    # 其他常用函数
    'puts', 'print', 'p', 'inspect', 'to_s', 'to_i', 'to_f',
    'length', 'size', 'count', 'first', 'last', 'rest', 'drop',
    'take', 'map', 'each', 'select', 'reject', 'find', 'detect',
}
MAX_SLEEP_BEATS = 8.0


def get_sonic_pi_naming_constraints():
    """
    返回一段描述，列出不能用于变量名的保留字，并给出一些建议。
    供系统 prompt 使用。
    """
    reserved_list = sorted(list(SONIC_PI_RESERVED_WORDS))
    text = (
            "Sonic Pi has many built-in function names and Ruby keywords that "
            "must NOT be used as variable names. These include (but are not limited to):\n\n"
            + ", ".join(reserved_list) +
            "\n\n"
            "Rules:\n"
            "1. Never assign to these names, e.g. `chord =` or `scale =` is forbidden.\n"
            "2. Use safe alternative variable names like `chord_notes`, `scale_pattern`, "
            "`melody_notes`, `bass_line`, `drum_pattern`, etc.\n"
            "3. Do not redefine core control structures or methods: if, while, loop, play, sample, etc.\n"
    )
    return text


def fix_reserved_word_variables(code):
    """
    对生成好的 Sonic Pi 代码做一个安全后处理：
    检查是否有将 Sonic Pi 保留字用作变量名的情况，并进行简单替换。

    例如：
        chord = [:c4, :e4, :g4]
    会被替换为：
        chord_notes = [:c4, :e4, :g4]

    这个函数会查找变量赋值语句（如 chord = ...），并将其替换为安全的变量名。
    注意：这个函数只处理明显的变量赋值情况，不会替换函数调用。

    Args:
        code: Sonic Pi Ruby 代码字符串

    Returns:
        修复后的代码字符串
    """
    # 常见的变量名替换映射（仅处理最常见的冲突）
    variable_replacements = {
        'chord': 'chord_notes',
        'scale': 'scale_pattern',
    }

    # 将字符串按行拆分处理
    lines = code.split('\n')
    fixed_lines = []

    # 正则匹配简单的变量赋值语句：  name = something
    assign_pattern = re.compile(r'^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=')

    for line in lines:
        m = assign_pattern.match(line)
        if m:
            var_name = m.group(1)
            if var_name in variable_replacements or var_name in SONIC_PI_RESERVED_WORDS:
                # 找到冲突变量名，进行替换
                new_var_name = variable_replacements.get(var_name, f"{var_name}_var")
                fixed_line = line.replace(var_name, new_var_name, 1)
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)


class MusicAgent:
    def __init__(self, name, role_desc, client, model="deepseek-chat"):
        self.name = name
        self.role_desc = role_desc
        self.client = client
        self.model = model

    def chat(self, messages):
        """
        调用模型生成回复
        """
        resp = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=0.8,
        )
        return resp.choices[0].message.content


def ensure_dir(path: str):
    """
    确保目录存在
    """
    Path(path).mkdir(parents=True, exist_ok=True)

def limit_sleep_durations(code: str, max_beats: float = MAX_SLEEP_BEATS) -> str:
    """
    后处理函数：限制 Sonic Pi 代码中数值型 sleep 的最大时长。

    只处理类似：
        sleep 16
        sleep 8.0
        sleep 14   # comment
    这样的形式，不会动：
        sleep some_var
        sleep rand
        sleep 0.25
    等。

    Args:
        code: Sonic Pi Ruby 代码字符串
        max_beats: 最大允许的拍数（超过则压缩到该值）

    Returns:
        处理后的代码字符串
    """
    # 匹配：sleep + 数字 + 可选的注释
    pattern = re.compile(r"(sleep\s+)(\d+(?:\.\d+)?)(\s*(?:#.*)?)")

    def repl(match: re.Match) -> str:
        prefix, num_str, suffix = match.group(1), match.group(2), match.group(3) or ""
        try:
            value = float(num_str)
        except ValueError:
            # 不是简单的数字（理论上不会），直接跳过
            return match.group(0)

        # 本来就不长的 sleep，不改
        if value <= max_beats:
            return match.group(0)

        new_val = max_beats

        # 尽量保留原来的“小数风格”
        if "." in num_str:
            decimals = len(num_str.split(".")[1])
            fmt = f"{{:.{decimals}f}}"
            new_num_str = fmt.format(new_val).rstrip("0").rstrip(".")
        else:
            # 原来是整数，就用整数格式
            if float(int(new_val)) == float(new_val):
                new_num_str = str(int(new_val))
            else:
                new_num_str = str(new_val)

        return f"{prefix}{new_num_str}{suffix}"

    return pattern.sub(repl, code)


def load_docs_content():
    """
    尝试加载 docs.txt / sonic_pi_docs.txt 等，给模型一点 Sonic Pi 参考
    """
    try:
        # 可根据项目结构调整文档路径
        candidates = [
            Path(__file__).parent / "docs.txt",
            Path(__file__).parent / "sonic_pi_docs.txt",
            Path(__file__).parent / "data" / "sonic_pi_docs.txt",
        ]
        for docs_path in candidates:
            if docs_path.exists():
                with open(docs_path, "r", encoding="utf-8") as f:
                    return f.read()
        return ""
    except Exception as e:
        print(f"Warning: Could not load docs.txt: {e}")
        return ""


def sonic_pi_code_to_midi(sonic_pi_code, output_path, client, log_callback=None):
    """
    Compile Sonic Pi code to MIDI file using Compiler agent

    Args:
        sonic_pi_code: Sonic Pi Ruby code
        output_path: Path to save MIDI file
        client: OpenAI client
        log_callback: Optional callback function for logging

    Returns:
        Path to saved MIDI file or None if failed
    """

    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    if mido is None:
        log("[❌] 'mido' library not installed, cannot create MIDI file.\n")
        log("    请先在当前虚拟环境中安装 mido： pip install mido\n")
        return None
    log("🔧 Step 4: Compiler - Converting Sonic Pi code to MIDI events...\n")

    compiler = MusicAgent(
        "Compiler",
        "Analyze Sonic Pi Ruby music code and extract precise MIDI note events with timing, velocity, and channel. "
        "The JSON schema is: "
        "{"
        "\"tempo\": <int BPM>, "
        "\"time_signature\": [numerator, denominator], "
        "\"tracks\": ["
        "  {\"name\": \"Track Name\", \"channel\": 0}, ..."
        "], "
        "\"events\": ["
        "  {"
        "    \"time\": <float seconds>, "
        "    \"note\": <int MIDI note number>, "
        "    \"velocity\": <int 0-127>, "
        "    \"duration\": <float seconds>, "
        "    \"channel\": <int MIDI channel 0-15>, "
        "    \"track_index\": <int track index>"
        "  }, ..."
        "]"
        "}",
        client,
        model="deepseek-chat"
    )

    compiler_prompt = [
        {"role": "system", "content":
            "You are a precise MIDI compiler for Sonic Pi. "
            "You take Sonic Pi Ruby music code and analyze all play commands, patterns, loops, and timing, "
            "and then output a strict JSON object describing the resulting MIDI performance. "
            "You must carefully handle: tempo (use_bpm), time signature (if present), sleeps, loops, and nested structures. "
            "Assume a performance window of the first 16 bars or 60 seconds, whichever comes first. "
            "The JSON must not include comments or extra keys. "
            "All times should be in seconds from the start (time=0.0). "
            "If there are no notes, output an empty events array. "
            "IMPORTANT: Only output the JSON, wrapped in ```json ... ```."},
        {"role": "user", "content":
            "Sonic Pi code:\n\n"
            f"{sonic_pi_code}\n\n"
            "Now extract all MIDI events (note-on and note-off represented via note, velocity, duration)."
            "\n"
            "JSON schema:\n"
            "{\n"
            "  \"tempo\": 120,\n"
            "  \"time_signature\": [4, 4],\n"
            "  \"tracks\": [\n"
            "    {\"name\": \"Main\", \"channel\": 0}\n"
            "  ],\n"
            "  \"events\": [\n"
            "    {\n"
            "      \"time\": 0.0,\n"
            "      \"note\": 60,\n"
            "      \"velocity\": 100,\n"
            "      \"duration\": 0.5,\n"
            "      \"channel\": 0,\n"
            "      \"track_index\": 0\n"
            "    }\n"
            "  ]\n"
            "}\n"
            "\n"
            "Constraints:\n"
            "- time: seconds from start (float)\n"
            "- note: MIDI note number 0-127\n"
            "- velocity: 0-127\n"
            "- duration: seconds (float > 0)\n"
            "- channel: 0-15\n"
            "- track_index: 0-based index into tracks array\n"
            "- Default tempo is 120 BPM if not specified\n"
            "- Default time signature is [4,4] if not specified\n"
            "- Default track list is a single track if not specified\n"
            "- Default velocity is 80 if not specified\n"
            "- Output only the JSON, wrapped in ```json ... ```"}
    ]

    log("Analyzing Sonic Pi code and extracting MIDI information...\n")
    midi_json_str = compiler.chat(compiler_prompt)
    log("\n🔧 Compiler analysis completed.\n")
    log(f"Compiler JSON Output:\n{midi_json_str[:1000]}...\n")

    # Extract JSON from response
    json_match = re.search(r"```json(.*?)```", midi_json_str, re.DOTALL)
    if json_match:
        midi_json_str = json_match.group(1).strip()
    else:
        # Try to find JSON in the response
        json_match = re.search(r"\{.*\"events\".*\}", midi_json_str, re.DOTALL)
        if json_match:
            midi_json_str = json_match.group(0)

    try:
        midi_data = json.loads(midi_json_str)
        log(f"Successfully parsed MIDI JSON with {len(midi_data.get('events', []))} events\n")
    except json.JSONDecodeError as e:
        log(f"Error parsing MIDI JSON: {e}\n")
        log(f"Compiler output: {midi_json_str[:500]}\n")
        return None

    # Create MIDI file from JSON data
    try:
        mid = mido.MidiFile()
        track = mido.MidiTrack()
        mid.tracks.append(track)

        tempo_bpm = midi_data.get("tempo", 120)
        time_signature = midi_data.get("time_signature", [4, 4])

        # Set tempo
        tempo = mido.bpm2tempo(tempo_bpm)
        track.append(mido.MetaMessage('set_tempo', tempo=tempo, time=0))

        # Set time signature
        if isinstance(time_signature, (list, tuple)) and len(time_signature) == 2:
            num, den = time_signature
            track.append(mido.MetaMessage(
                'time_signature',
                numerator=int(num),
                denominator=int(den),
                clocks_per_click=24,
                notated_32nd_notes_per_beat=8,
                time=0
            ))

        ticks_per_beat = mid.ticks_per_beat

        events = midi_data.get("events", [])
        if not events:
            log("No events in MIDI data, creating empty MIDI file.\n")
            mid.save(output_path)
            log(f"[✅] Empty MIDI file created at: {output_path}\n")
            return output_path

        # Sort events by time
        events.sort(key=lambda e: float(e.get("time", 0.0)))

        last_time = 0.0
        for event in events:
            event_time = float(event.get("time", 0.0))
            note = int(event.get("note", 60))
            velocity = int(event.get("velocity", 80))
            duration = float(event.get("duration", 0.5))
            channel = int(event.get("channel", 0))

            # Convert event time to delta ticks
            delta_time = event_time - last_time
            delta_ticks = int(delta_time * (ticks_per_beat * tempo_bpm / 60.0))
            if delta_ticks < 0:
                delta_ticks = 0

            # Note on
            track.append(mido.Message(
                'note_on',
                note=note,
                velocity=velocity,
                time=delta_ticks,
                channel=channel
            ))

            # Note off after duration
            duration_ticks = int(duration * (ticks_per_beat * tempo_bpm / 60.0))
            if duration_ticks < 1:
                duration_ticks = 1
            track.append(mido.Message(
                'note_off',
                note=note,
                velocity=0,
                time=duration_ticks,
                channel=channel
            ))

            last_time = event_time

        # Save MIDI file
        mid.save(output_path)
        log(f"[✅] MIDI file compiled and saved: {output_path}\n")
        return output_path

    except Exception as e:
        log(f"[❌] Error creating MIDI file: {e}\n")
        import traceback
        error_trace = traceback.format_exc()
        log(f"Traceback:\n{error_trace}\n")
        return None


def multi_agent_generate_sonic_pi(prompt_text, client, user_feedback=None, previous_code=None, output_dir=None,
                                  log_callback=None):
    """
    Multi-agent collaboration to generate Sonic Pi format music code (Ruby code) and compile to MIDI
    Contains five roles:
      1. Translator: Translates user requirements into professional music generation terminology
      2. Composer: Responsible for initial draft
      3. Critic: Reviews and provides improvement suggestions
      4. Arranger: Integrates feedback and outputs final Sonic Pi code
      5. Compiler: Compiles Sonic Pi code to MIDI file

    Args:
        prompt_text: Music description prompt
        client: OpenAI client
        user_feedback: Optional user feedback to incorporate into critic prompt
        previous_code: Optional previous code version for iterative improvement
        output_dir: Optional directory to save MIDI file (default: current directory)
        log_callback: Optional callback function for logging (e.g., GUI log panel)

    Returns:
        (sonic_pi_code, midi_path) - The final Sonic Pi code and path to compiled MIDI file (or None if failed)
    """

    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    docs_content = load_docs_content()
    naming_constraints = get_sonic_pi_naming_constraints()

    # 1. Translator Agent
    translator = MusicAgent(
        "Translator",
        "Translate user requirements into structured, detailed, and technically precise music generation instructions. "
        "Focus on genre, mood, tempo, instrumentation, structure (intro, verse, chorus, etc.), and key motifs. "
        "Do not write any code; only describe WHAT to generate in music terms.",
        client,
        model="deepseek-chat"
    )

    # 2. Composer Agent
    composer = MusicAgent(
        "Composer",
        "Compose initial Sonic Pi Ruby music code based on a detailed music specification. "
        "Use clear structure, variables, and comments. Avoid using Sonic Pi built-in function names and Ruby keywords "
        "as variable names. Use safe variable names like melody_notes, bass_line, drum_pattern, etc.",
        client,
        model="deepseek-chat"
    )

    # 3. Critic Agent
    critic = MusicAgent(
        "Critic",
        "Critically review Sonic Pi music code, checking musicality, structure, variation, and playability. "
        "Point out issues: monotony, lack of progression, unbalanced mix, missing transitions, etc. "
        "Provide concrete suggestions on how to improve the code and music.",
        client,
        model="deepseek-chat"
    )

    # 4. Arranger Agent
    arranger = MusicAgent(
        "Arranger",
        "Take the initial Sonic Pi code and the critic's feedback, then produce an improved final Sonic Pi script. "
        "Apply all relevant feedback, enhance musical development, add subtle variations, and ensure structure is clear. "
        "Respect the variable naming constraints and never use built-in function names as variable names.",
        client,
        model="deepseek-chat"
    )

    log("=" * 60 + "\n")
    log("🎼 Multi-Agent Sonic Pi Music Generation Pipeline\n")
    log("=" * 60 + "\n")

    # Step 1: Translator - understand and structure the user's request
    translator_messages = [
        {
            "role": "system",
            "content": (
                    translator.role_desc + "\n\n"
                                           "You will receive a user prompt describing desired music. "
                                           "Output a detailed, structured specification for the music. "
                                           "Example sections:\n"
                                           "- Genre & style\n"
                                           "- Mood & atmosphere\n"
                                           "- Tempo & time signature\n"
                                           "- Instrumentation\n"
                                           "- Formal structure (intro, sections, outro)\n"
                                           "- Key, harmony, motifs\n"
                                           "- Rhythm & groove\n"
                                           "- Any special effects or transitions\n"
            )
        },
        {
            "role": "user",
            "content": prompt_text
        }
    ]

    log("🎧 Step 1: Translator is analyzing the user prompt...\n")
    translation = translator.chat(translator_messages)
    log("\n🎧 Translator output (music specification):\n")
    log(translation + "\n")

    # Step 2: Composer - write initial Sonic Pi code
    composer_system = (
            composer.role_desc + "\n\n"
                                 "You will receive a detailed music specification. "
                                 "Write Sonic Pi Ruby code implementing it. "
                                 "Constraints:\n"
                                 "1. Use idiomatic Sonic Pi: use_bpm, use_synth, play, sleep, live_loop, with_fx, etc.\n"
                                 "2. Structure your code with comments and logical sections.\n"
                                 "3. Avoid using the following as variable names (they are reserved or built-ins):\n"
                                 f"{naming_constraints}\n"
                                 "4. Use clear and descriptive variable names: melody_notes, bass_line, drum_pattern, lead_synth, etc.\n"
                                 "5. Ensure the code is runnable in Sonic Pi.\n"
                                 "6. Output ONLY Ruby code in a ```ruby ... ``` block."
    )
    if docs_content:
        composer_system += (
                "\n\nYou may also refer to this Sonic Pi documentation excerpt for correct syntax and functions:\n"
                + docs_content[:8000]
        )

    composer_messages = [
        {"role": "system", "content": composer_system},
        {"role": "user", "content": "Music specification:\n" + translation}
    ]

    log("🎹 Step 2: Composer is writing initial Sonic Pi code...\n")
    composer_output = composer.chat(composer_messages)
    log("\n🎹 Composer output:\n")
    log(composer_output + "\n")

    # Extract Ruby code from triple backticks
    code_match = re.search(r"```ruby(.*?)```", composer_output, re.DOTALL | re.IGNORECASE)
    if code_match:
        initial_code = code_match.group(1).strip()
    else:
        # Fallback: use entire output as code
        initial_code = composer_output.strip()

    # Step 3: Critic - review the code
    critic_prompt = (
            critic.role_desc + "\n\n"
                               "Here is the Sonic Pi code to review:\n\n"
                               "```ruby\n" + initial_code + "\n```\n\n"
                                                            "If there is user feedback or previous code version, incorporate that in your critique.\n"
    )

    if user_feedback:
        critic_prompt += f"\nUser feedback:\n{user_feedback}\n"

    if previous_code:
        critic_prompt += "\nPrevious version of the code:\n```ruby\n" + previous_code + "\n```\n"

    critic_messages = [
        {"role": "system", "content": critic.role_desc},
        {"role": "user", "content": critic_prompt}
    ]

    log("🧐 Step 3: Critic is reviewing the code...\n")
    critic_output = critic.chat(critic_messages)
    log("\n🧐 Critic feedback:\n")
    log(critic_output + "\n")

    # Step 4: Arranger - produce improved final code
    arranger_system = (
            arranger.role_desc + "\n\n"
                                 "You will receive:\n"
                                 "1) The initial Sonic Pi code\n"
                                 "2) The critic's feedback\n"
                                 "3) Optional user feedback and/or previous code\n"
                                 "Your task: produce a final improved Sonic Pi script that addresses all valid feedback.\n"
                                 "Constraints:\n"
                                 " - Keep code runnable in Sonic Pi.\n"
                                 " - Respect the variable naming constraints and never use built-in function names as variables.\n"
                                 " - Output ONLY Ruby code, within a ```ruby ... ``` block.\n"
    )
    if docs_content:
        arranger_system += (
                "\n\nYou can refer to this Sonic Pi documentation excerpt as needed:\n"
                + docs_content[:8000]
        )

    arranger_user_content = (
            "Initial Sonic Pi code:\n"
            "```ruby\n" + initial_code + "\n```\n\n"
                                         "Critic feedback:\n" + critic_output + "\n"
    )

    if user_feedback:
        arranger_user_content += f"\nUser feedback:\n{user_feedback}\n"

    if previous_code:
        arranger_user_content += "\nPrevious version of the code:\n```ruby\n" + previous_code + "\n```\n"

    arranger_messages = [
        {"role": "system", "content": arranger_system},
        {"role": "user", "content": arranger_user_content}
    ]

    log("🎛 Step 4: Arranger is integrating feedback and producing final code...\n")
    final_output = arranger.chat(arranger_messages)
    log("\n🎛 Arranger final output:\n")
    log(final_output + "\n")

    # Extract final Ruby code
    final_match = re.search(r"```ruby(.*?)```", final_output, re.DOTALL | re.IGNORECASE)
    if final_match:
        sonic_pi_code = final_match.group(1).strip()
    else:
        # Fallback: try any fenced code block
        any_code = re.search(r"```(.*?)```", final_output, re.DOTALL)
        if any_code:
            sonic_pi_code = any_code.group(1).strip()
        else:
            sonic_pi_code = final_output.strip()

    # Apply post-processing to fix reserved word variables (as a safety measure)
    # Note: This is a fallback - the AI should already avoid using reserved words
    original_code = sonic_pi_code
    sonic_pi_code = fix_reserved_word_variables(sonic_pi_code)
    if original_code != sonic_pi_code:
        log("⚠️ Post-processing: Fixed reserved word variable names in generated code\n")

    # 进一步后处理：限制过长的 sleep 间隔
    original_code2 = sonic_pi_code
    sonic_pi_code = limit_sleep_durations(sonic_pi_code)
    if original_code2 != sonic_pi_code:
        log(f"⚠️ Post-processing: Shortened long sleep durations (clamped to ≤ {MAX_SLEEP_BEATS} beats)\n")

    # Step 4: Compiler compiles code to MIDI
    midi_path = None

    if output_dir is None:
        output_dir = Path(".")
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True, parents=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    midi_filename = output_dir / f"sonic_pi_output_{timestamp}.mid"

    log("🔧 Step 4: Compiler - Compiling code to MIDI file...midi_filename\n")
    midi_path = sonic_pi_code_to_midi(sonic_pi_code, str(midi_filename), client, log_callback=log)

    if midi_path:
        log(f"\n✅ MIDI compilation completed: {midi_path}\n")
    else:
        log("\n⚠️ MIDI compilation failed, but code generation succeeded.\n")
    log("=" * 60 + "\n")

    return sonic_pi_code, midi_path


def summarize_midi_file(midi_path, max_events=128, log_callback=None):
    """
    将 MIDI 文件解析成一个紧凑、适合喂给 LLM 的文本摘要。
    返回摘要字符串；失败则返回 None。
    """

    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    try:
        import mido
    except ImportError:
        log("[❌] mido library not installed, cannot read MIDI file.\n")
        return None

    midi_path = str(midi_path)
    if not os.path.exists(midi_path):
        log(f"[❌] MIDI file not found: {midi_path}\n")
        return None

    try:
        mid = mido.MidiFile(midi_path)
    except Exception as e:
        log(f"[❌] Failed to read MIDI file: {e}\n")
        return None

    ticks_per_beat = mid.ticks_per_beat or 480
    # 默认 120 BPM
    tempo_us = 500000
    numerator, denominator = 4, 4

    # 尝试从 MetaMessage 中拿 tempo / 拍号（如果有的话）
    for track in mid.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                tempo_us = msg.tempo
            elif msg.type == "time_signature":
                numerator = getattr(msg, "numerator", numerator)
                denominator = getattr(msg, "denominator", denominator)

    bpm = 60_000_000 / tempo_us

    events = []
    for ti, track in enumerate(mid.tracks):
        tick_time = 0
        for msg in track:
            tick_time += msg.time
            if msg.type in ("note_on", "note_off"):
                beat_time = tick_time / ticks_per_beat
                note = getattr(msg, "note", 0)
                velocity = getattr(msg, "velocity", 0)
                events.append({
                    "track": ti,
                    "time_beats": beat_time,
                    "type": msg.type,
                    "note": note,
                    "velocity": velocity,
                })
                if len(events) >= max_events:
                    break
        if len(events) >= max_events:
            break

    if not events:
        log("[⚠️] No note_on/note_off events found in MIDI.\n")

    lines = []
    lines.append(f"MIDI summary for file: {Path(midi_path).name}")
    lines.append(f"Approx tempo: {bpm:.1f} BPM")
    lines.append(f"Time signature: {numerator}/{denominator}")
    lines.append(f"Total tracks: {len(mid.tracks)}")
    lines.append(f"First {len(events)} note events (time in beats):")
    for ev in events:
        lines.append(
            f"Track {ev['track']}, t={ev['time_beats']:.3f} beats, "
            f"{ev['type']}, note={ev['note']}, velocity={ev['velocity']}"
        )

    summary = "\n".join(lines)
    log(f"[📄] MIDI summary generated with {len(events)} events.\n")
    return summary


def music_file_to_sonic_pi(input_path, client, output_dir=None, log_callback=None):
    """
    从音乐文件（MIDI 或 音频）生成 Sonic Pi 代码。

    - 如果是 .mid / .midi：直接读取并摘要，再交给 MIDI Interpreter Agent。
    - 如果是音频（.wav / .mp3 / .flac / .ogg / .m4a 等）：
        1) 优先使用 Qwen-Omni 多模态模型，直接从音频生成 Sonic Pi 代码 + MIDI（通过现有 compiler）。
        2) 如果 Qwen 不可用或失败，则回退到 basic_pitch：audio → MIDI → MIDI Interpreter Agent。

    返回 (sonic_pi_code, midi_path)：
      - sonic_pi_code: 生成的 Sonic Pi Ruby 代码
      - midi_path: 对应的 MIDI 文件路径（如果 Qwen 路线成功，则是重新编译出来的 MIDI；否则是原始/转录 MIDI）
    """

    def log(message: str):
        if log_callback:
            log_callback(message)
        else:
            print(message)

    path = Path(input_path)
    if not path.exists():
        log(f"[❌] Music file not found: {path}\n")
        return None, None

    ext = path.suffix.lower()
    midi_path = None

    # 情况 1：用户直接给 MIDI
    if ext in (".mid", ".midi"):
        midi_path = path
        log(f"[🎵] Using existing MIDI file: {midi_path}\n")

    # 情况 2：音频文件（优先走 Qwen-Omni）
    elif ext in (".wav", ".mp3", ".flac", ".ogg", ".m4a"):
        # 2.1 尝试 Qwen-Omni 音频 → Sonic Pi
        if HAVE_QWEN_AUDIO:
            log("[🎧] Detected audio file, using Qwen-Omni audio → Sonic Pi pipeline...\n")
            try:
                # Qwen 模块返回：音乐描述文本 + Sonic Pi 代码
                music_desc, sonic_code = call_qwen_audio_to_code(str(path))

                if sonic_code and sonic_code.strip():
                    # 做一遍你原来用的保留字变量名修复，防止变量名撞 Sonic Pi 内建
                    original_code = sonic_code
                    sonic_code = fix_reserved_word_variables(sonic_code)
                    if original_code != sonic_code:
                        log("⚠️ Post-processing: Fixed reserved word variable names in Qwen-generated code.\n")

                    # 利用现有 compiler agent 把 Sonic Pi 代码再编译成 MIDI（保持和文本流程一致）
                    if output_dir is None:
                        out_dir = path.parent
                    else:
                        out_dir = Path(output_dir)
                    out_dir.mkdir(parents=True, exist_ok=True)

                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    midi_filename = out_dir / f"qwen_audio_import_{timestamp}.mid"

                    log("🔧 Compiling Qwen-Omni generated Sonic Pi code to MIDI...\n")
                    midi_path = sonic_pi_code_to_midi(
                        sonic_code,
                        str(midi_filename),
                        client,
                        log_callback=log,
                    )

                    if midi_path:
                        log(f"[✅] Qwen-Omni audio import compiled to MIDI: {midi_path}\n")
                    else:
                        log("[⚠️] MIDI compilation failed, but Sonic Pi code from Qwen-Omni is available.\n")

                    # 这里直接返回，不再走 basic_pitch + MIDI Interpreter 的 LLM 流程
                    return sonic_code, str(midi_path) if midi_path is not None else None

                else:
                    log("[⚠️] Qwen-Omni did not return valid Sonic Pi code, will fall back to audio → MIDI pipeline.\n")

            except Exception as e:
                log(f"[❌] Error when calling Qwen-Omni audio pipeline: {e}\n")
                import traceback
                log(traceback.format_exc())
                log("    Falling back to basic_pitch audio → MIDI pipeline (if available).\n")
        else:
            log("[ℹ️] Qwen-Omni audio module not available, using basic_pitch audio → MIDI pipeline.\n")

        # 2.2 回退：basic_pitch audio → MIDI（保留你原来的逻辑）
        try:
            from basic_pitch.inference import predict_and_save
        except Exception as e:
            # 这里不仅拦 ImportError，也拦 basic_pitch 内部自己的 NameError 等所有异常
            log("[❌] basic_pitch 无法使用，音频→MIDI 功能已自动禁用。\n")
            log(f"    详细错误信息：{e}\n")
            log("    你可以先使用外部工具把音频转成 MIDI 文件，再用『从音乐文件生成』重新导入。")
            return None, None

        if output_dir is None:
            midi_output_dir = path.parent
        else:
            midi_output_dir = Path(output_dir)
        midi_output_dir.mkdir(parents=True, exist_ok=True)

        before_mid_files = set(midi_output_dir.glob("*.mid"))
        log("[🎧] Transcribing audio to MIDI using basic_pitch...\n")

        try:
            # 让 basic_pitch 把 MIDI 保存在 midi_output_dir
            predict_and_save(
                [str(path)],
                str(midi_output_dir),
                save_midi=True,
                sonify_midi=False,
                save_model_outputs=False,
                save_notes=False,
            )
        except Exception as e:
            log(f"[❌] Error during audio transcription: {e}\n")
            import traceback
            log(traceback.format_exc())
            return None, None

        new_mid_files = set(midi_output_dir.glob("*.mid")) - before_mid_files
        if not new_mid_files:
            log("[❌] basic_pitch did not create any MIDI files.\n")
            return None, None

        # 尽量选文件名和原音频同 stem 的那个，否则取最新的一个
        target = None
        for f in new_mid_files:
            if f.stem.startswith(path.stem):
                target = f
                break
        if target is None:
            target = max(new_mid_files, key=lambda f: f.stat().st_mtime)

        midi_path = target
        log(f"[✅] Audio transcribed to MIDI: {midi_path}\n")

    # 情况 3：其他扩展名（既不是 MIDI 也不是常见音频）
    else:
        log(f"[❌] Unsupported music file extension: {ext}. "
            f"Please use .mid/.midi/.wav/.mp3/.flac/.ogg/.m4a\n")
        return None, None

    # 走到这里，说明：
    # - 要么是原始 MIDI
    # - 要么是音频经 basic_pitch 成功转出来的 MIDI
    if midi_path is None:
        log("[❌] No MIDI path available after processing.\n")
        return None, None

    summary = summarize_midi_file(midi_path, max_events=128, log_callback=log)
    if not summary:
        return None, None

    docs_content = load_docs_content()
    naming_constraints = get_sonic_pi_naming_constraints()

    midi_interpreter = MusicAgent(
        "MIDI Interpreter",
        "Responsible for converting MIDI note sequences into Sonic Pi Ruby code. "
        "Receives structured summaries of MIDI files and reconstructs them in Sonic Pi syntax. "
        "CRITICAL: Never use Sonic Pi built-in function names (chord, scale, play, sample, amp, pan, etc.) "
        "as variable names.",
        client,
        model="deepseek-chat"
    )

    system_prompt = midi_interpreter.role_desc
    if docs_content:
        system_prompt += "\n\nSonic Pi Documentation Reference (excerpt):\n" + docs_content[:8000]

    user_prompt = (
        "You are given a concise textual summary of a MIDI file.\n"
        "Your task is to write Sonic Pi Ruby code that approximates the same musical content.\n\n"
        "MIDI summary:\n"
        f"{summary}\n\n"
        "Requirements:\n"
        "1. Use Sonic Pi idiomatic constructs: use_synth, play, sleep, live_loop, with_fx, etc.\n"
        "2. Preserve relative rhythm and contour of the melody as much as possible.\n"
        "3. You may simplify chords or polyphony if the MIDI is complex, but keep the main musical idea.\n"
        "4. Make sure the code is runnable in Sonic Pi.\n"
        "5. Apply the following variable naming constraints and safety rules:\n"
        f"{naming_constraints}\n"
        "6. Output ONLY the complete Sonic Pi code wrapped in a ```ruby ... ``` block."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    log("🎼 Step: MIDI Interpreter - Converting MIDI summary to Sonic Pi code...\n")
    output = midi_interpreter.chat(messages)
    log("\n🎼 MIDI Interpreter finished.\n")
    log(f"MIDI Interpreter raw output:\n{output}\n")

    # 提取 Ruby 代码
    m = re.search(r"```ruby(.*?)```", output, re.DOTALL)
    if m:
        sonic_code = m.group(1).strip()
    else:
        m = re.search(r"```(.*?)```", output, re.DOTALL)
        if m:
            sonic_code = m.group(1).strip()
        else:
            sonic_code = output.strip()

    original_code = sonic_code
    sonic_code = fix_reserved_word_variables(sonic_code)
    if original_code != sonic_code:
        log("⚠️ Post-processing: Fixed reserved word variable names in imported code.\n")

    # 这里不强制再编译成新的 MIDI，直接返回 Sonic Pi 代码 + 原始/转录后的 MIDI 路径
    return sonic_code, str(midi_path) if midi_path is not None else None

