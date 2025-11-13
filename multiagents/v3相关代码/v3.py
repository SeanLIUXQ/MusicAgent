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
  python multi_agent_music_system.py -p "一首平静的钢琴独奏，C大调，慢速，梦幻风格" -o outputs --soundfont /path/to/FluidR3_GM.sf2
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

from music21 import converter, midi
try:
    from midi2audio import FluidSynth
    HAVE_MIDI2AUDIO = True
except ImportError:
    HAVE_MIDI2AUDIO = False

# ------------------------------
# Sonic Pi 保留字和内置函数列表
# ------------------------------

SONIC_PI_RESERVED_WORDS = {
    # 核心函数
    'play', 'sample', 'sleep', 'live_loop', 'use_synth', 'use_bpm',
    'with_fx', 'with_fx_slice', 'with_fx_reverb', 'with_fx_echo',
    'with_fx_distortion', 'with_fx_lpf', 'with_fx_hpf', 'with_fx_bpf',
    'with_fx_compressor', 'with_fx_tanh', 'with_fx_pan', 'with_fx_ring_mod',
    'with_fx_vowel', 'with_fx_whammy', 'with_fx_wobble', 'with_fx_ixi_techno',
    'with_fx_bitcrusher', 'with_fx_pitch_shift', 'with_fx_autotune',
    
    # 音乐理论函数
    'chord', 'scale', 'degree', 'note', 'midi', 'midi_note_on', 'midi_note_off',
    'midi_pc', 'midi_cc', 'midi_sysex', 'midi_clock_beat', 'midi_clock_tick',
    
    # 参数和控制
    'amp', 'pan', 'rate', 'attack', 'decay', 'sustain', 'release',
    'cutoff', 'res', 'cut', 'resonance', 'lpf', 'hpf', 'bpf',
    'room', 'mix', 'phase', 'feedback', 'delay', 'delay_time',
    'beat_stretch', 'pitch', 'velocity', 'bpm', 'tempo',
    
    # 数据结构
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
    'all?', 'any?', 'none?', 'empty?', 'include?', 'has_key?',
    'keys', 'values', 'merge', 'update', 'delete', 'clear',
}

def get_sonic_pi_naming_constraints():
    """获取 Sonic Pi 变量命名约束说明"""
    reserved_list = sorted(list(SONIC_PI_RESERVED_WORDS))
    return f"""
CRITICAL VARIABLE NAMING RULES FOR SONIC PI:
1. NEVER use Sonic Pi built-in function names as variable names
2. Common reserved words to avoid: {', '.join(reserved_list[:30])}... (and many more)
3. Instead of using reserved words, use descriptive alternatives:
   - Instead of 'chord', use 'chord_notes', 'chord_progression', 'chord_seq', 'my_chord'
   - Instead of 'scale', use 'scale_notes', 'scale_pattern', 'my_scale'
   - Instead of 'play', use 'note_to_play', 'play_note' (but 'play' is a function, not a variable)
   - Instead of 'sample', use 'sample_name', 'sample_path', 'my_sample'
   - Instead of 'amp', use 'amplitude', 'volume', 'my_amp'
   - Instead of 'pan', use 'panning', 'pan_position', 'my_pan'
   - Instead of 'rate', use 'playback_rate', 'sample_rate', 'my_rate'
4. Use descriptive variable names with prefixes/suffixes:
   - Add '_notes', '_seq', '_pattern', '_progression' for chord/scale variables
   - Add '_value', '_param', '_setting' for parameter variables
   - Use 'my_', 'current_', 'selected_' prefixes when needed
5. Always check that variable names don't conflict with built-in functions before using them
"""


def fix_reserved_word_variables(code):
    """
    后处理函数：检查并修复代码中使用保留字作为变量名的问题
    
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
    
    import re
    
    # 只处理明确的变量赋值情况
    # 模式：变量名 = 值（变量名是单独的标识符，后面直接跟 =）
    fixed_code = code
    variable_map = {}  # 记录已替换的变量名映射
    
    for reserved_word, replacement in variable_replacements.items():
        # 查找变量赋值：word = 或 word, = 或 word, other = 
        # 但不包括函数调用：word(...) 或 word:...
        assignment_pattern = r'\b(' + re.escape(reserved_word) + r')\s*='
        matches = list(re.finditer(assignment_pattern, fixed_code))
        
        if matches:
            # 从后往前替换，避免位置偏移问题
            for match in reversed(matches):
                start_pos = match.start()
                var_name = match.group(1)
                
                # 检查前面是否有函数调用符号（如 .chord 或 chord(）
                before_context = fixed_code[max(0, start_pos-10):start_pos]
                # 如果前面有 . 或 (，可能是方法调用，跳过
                if '.' in before_context[-2:] or before_context[-1] in '([':
                    continue
                
                # 记录变量名映射
                if var_name not in variable_map:
                    variable_map[var_name] = replacement
                
                # 替换变量赋值
                fixed_code = fixed_code[:match.start()] + replacement + fixed_code[match.end()-len(var_name):]
    
    # 替换所有使用该变量的地方（但不在函数调用中）
    for old_name, new_name in variable_map.items():
        # 替换变量使用，但要排除函数调用
        # 模式：变量名后面不跟 ( 或 : 或 .
        pattern = r'\b' + re.escape(old_name) + r'\b(?!\s*[(:.])'
        fixed_code = re.sub(pattern, new_name, fixed_code)
    
    return fixed_code


# ------------------------------
# 多智能体定义
# ------------------------------

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
        return resp.choices[0].message.content.strip()


# ------------------------------
# 生成 ABC 音乐的多智能体逻辑
# ------------------------------

def multi_agent_generate_abc(prompt_text, client):
    """
    多智能体协作生成 ABC 格式音乐
    包含三个角色：
      1. Composer: 负责初稿
      2. Critic: 审核并给出修改建议
      3. Arranger: 结合修改意见，输出最终 ABC
    """

    composer = MusicAgent("Composer", "负责根据描述创作 ABC 音乐初稿", client)
    critic = MusicAgent("Critic", "负责审阅音乐并提出改进意见", client)
    arranger = MusicAgent("Arranger", "负责将修改意见整合成最终 ABC 乐谱", client)

    # Step 1: Composer 初稿
    composer_prompt = [
        {"role": "system", "content": composer.role_desc},
        {"role": "user", "content": f"Compose ABC music with following requirements: \n{prompt_text}\nOnly output the ABC code without any other words."}
    ]
    draft = composer.chat(composer_prompt)
    print("\n🎼 Composer 初稿完成。\n")

    # Step 2: Critic 审核
    critic_prompt = [
        {"role": "system", "content": critic.role_desc},
        {"role": "user", "content": f"以下是 Composer 的作品，请评论并提出改进建议：\n{draft}"}
    ]
    feedback = critic.chat(critic_prompt)
    print("\n🧐 Critic 反馈完成。\n")

    # Step 3: Arranger 整合修改
    arranger_prompt = [
        {"role": "system", "content": arranger.role_desc},
        {"role": "user", "content": f"以下是原作与修改意见，请输出最终 ABC 乐谱：\n原作:\n{draft}\n\n修改意见:\n{feedback}\n请直接输出完整 ABC，用 ```abc ... ``` 包裹。"}
    ]
    final_output = arranger.chat(arranger_prompt)
    print("\n🎵 Arranger 最终乐谱完成。\n")

    # 提取 ABC
    m = re.search(r"```abc(.*?)```", final_output, re.DOTALL)
    if m:
        abc_code = m.group(1).strip()
    else:
        # fallback: 寻找 X: 标记
        m = re.search(r"(X:\s*1[\s\S]+)", final_output)
        abc_code = m.group(1).strip() if m else final_output

    return abc_code


def load_docs_content():
    """Load Sonic Pi documentation content"""
    try:
        docs_path = Path(__file__).parent / "docs.txt"
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
    
    try:
        import mido
        from datetime import datetime
    except ImportError:
        log("Warning: mido library required for MIDI compilation")
        return None
    
    compiler = MusicAgent(
        "Compiler",
        "Responsible for analyzing Sonic Pi Ruby code and extracting musical information to generate MIDI format. "
        "You should identify all play, midi, midi_note_on, midi_note_off calls, extract notes, durations, velocities, "
        "and timing information. Output a structured MIDI event list in JSON format with tempo, time signature, and note events.",
        client
    )
    
    compiler_prompt = [
        {"role": "system", "content": compiler.role_desc},
        {"role": "user", "content": f"Analyze the following Sonic Pi code and extract all musical information to generate MIDI format:\n\nSonic Pi Code:\n{sonic_pi_code}\n\n"
         "Please output a JSON structure with the following format:\n"
         "{{\n"
         "  \"tempo\": 120,  // BPM\n"
         "  \"time_signature\": [4, 4],  // [numerator, denominator]\n"
         "  \"events\": [\n"
         "    {{\"time\": 0.0, \"type\": \"note_on\", \"note\": 60, \"velocity\": 80, \"channel\": 0}},\n"
         "    {{\"time\": 0.5, \"type\": \"note_off\", \"note\": 60, \"channel\": 0}},\n"
         "    // ... more events\n"
         "  ]\n"
         "}}\n\n"
         "Notes:\n"
         "- Convert Sonic Pi note names (like :C4, :E4) to MIDI note numbers (60 = C4)\n"
         "- Extract sleep durations to calculate timing\n"
         "- Default tempo is 60 BPM if not specified\n"
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
        
        # Set tempo (default 120 BPM)
        tempo = mido.bpm2tempo(midi_data.get('tempo', 120))
        track.append(mido.MetaMessage('set_tempo', tempo=tempo))
        
        # Set time signature (default 4/4)
        time_sig = midi_data.get('time_signature', [4, 4])
        track.append(mido.MetaMessage('time_signature', numerator=time_sig[0], denominator=time_sig[1]))
        
        # Add note events
        events = midi_data.get('events', [])
        if not events:
            log("Warning: No MIDI events found in compiler output\n")
            return None
        
        log(f"Creating MIDI file with {len(events)} events...\n")
        
        # Sort events by time
        events.sort(key=lambda x: x.get('time', 0))
        
        # Convert to MIDI messages with delta times
        ticks_per_beat = 480
        last_time = 0
        
        for event in events:
            event_time = event.get('time', 0)
            delta_ticks = int((event_time - last_time) * ticks_per_beat * (midi_data.get('tempo', 120) / 60.0))
            
            event_type = event.get('type', '')
            if event_type == 'note_on':
                note = event.get('note', 60)
                velocity = event.get('velocity', 80)
                channel = event.get('channel', 0)
                track.append(mido.Message('note_on', note=note, velocity=velocity, channel=channel, time=delta_ticks))
            elif event_type == 'note_off':
                note = event.get('note', 60)
                velocity = event.get('velocity', 0)
                channel = event.get('channel', 0)
                track.append(mido.Message('note_off', note=note, velocity=velocity, channel=channel, time=delta_ticks))
            
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


def multi_agent_generate_sonic_pi(prompt_text, client, user_feedback=None, previous_code=None, output_dir=None, log_callback=None):
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
        log_callback: Optional callback function for logging (function(message: str))
    
    Returns:
        Tuple of (sonic_pi_code, midi_path) where midi_path may be None if compilation failed
    """
    
    def log(message):
        """Log message to callback or print to console"""
        if log_callback:
            log_callback(message)
        else:
            print(message)

    # Log original prompt before translation
    log(f"📝 Original User Prompt:\n{prompt_text}\n")
    log("=" * 60 + "\n")
    
    # Load docs.txt content
    docs_content = load_docs_content()
    
    translator = MusicAgent("Translator", "Responsible for translating user's natural language music requirements into professional music generation terminology. Should identify key musical elements such as tempo, key signature, time signature, instruments, musical style, dynamics, and other technical specifications.", client, model="deepseek-chat")
    composer = MusicAgent("Composer", "Responsible for creating initial Sonic Pi music code draft. Sonic Pi uses Ruby syntax, common commands include: play, sample, live_loop, sleep, use_synth, with_fx, etc. CRITICAL: Never use Sonic Pi built-in function names (like chord, scale, play, sample, amp, pan, etc.) as variable names. Use descriptive alternatives like chord_notes, chord_progression, scale_pattern, my_amp, etc.", client, model="deepseek-chat")
    critic = MusicAgent("Critic", "Responsible for reviewing Sonic Pi code and providing improvement suggestions, ensuring code syntax is correct and conforms to Sonic Pi specifications. CRITICAL: Check for variable naming conflicts with Sonic Pi built-in functions (chord, scale, play, sample, amp, pan, rate, etc.) and suggest alternatives if found.", client, model="deepseek-chat")
    arranger = MusicAgent("Arranger", "Responsible for integrating feedback into final runnable Sonic Pi code. CRITICAL: Ensure all variable names do not conflict with Sonic Pi built-in functions. Replace any reserved word variables with descriptive alternatives (e.g., 'chord' -> 'chord_notes' or 'chord_progression', 'scale' -> 'scale_pattern' or 'scale_notes').", client, model="deepseek-chat")

    # Step 0: Translator converts user requirements to professional terminology
    log("🌐 Step 0: Translator - Converting user requirements to professional terminology...\n")
    translator_prompt = [
        {"role": "system", "content": translator.role_desc},
        {"role": "user", "content": f"Translate the following user music requirement into professional music generation terminology:\n\nUser Requirement:\n{prompt_text}\n\nPlease provide a detailed, professional music specification that includes:\n1. Tempo (BPM)\n2. Key signature\n3. Time signature\n4. Musical style/genre\n5. Instrumentation\n6. Dynamics and expression\n7. Any other relevant technical specifications\n\nOutput the professional specification in a clear, structured format."}
    ]
    professional_spec = translator.chat(translator_prompt)
    log("\n🌐 Translator conversion completed.\n")
    log(f"Professional Specification:\n{professional_spec}\n")
    log("=" * 60 + "\n")

    # Step 1: Composer initial draft using professional specification
    composer_system_prompt = composer.role_desc
    if docs_content:
        composer_system_prompt += f"\n\nSonic Pi Documentation Reference:\n{docs_content[:8000]}"  # Limit to avoid token limits
    
    # Add naming constraints to composer prompt
    naming_constraints = get_sonic_pi_naming_constraints()
    
    composer_prompt = [
        {"role": "system", "content": composer_system_prompt},
        {"role": "user", "content": f"Please create a Sonic Pi music code based on the following professional music specification:\n\nProfessional Specification:\n{professional_spec}\n\nOriginal User Requirement (for reference):\n{prompt_text}\n\n{naming_constraints}\n\nRequirements:\n1. Use Sonic Pi's Ruby syntax\n2. You can use commands like live_loop, play, sample, sleep, use_synth, with_fx, etc.\n3. Output complete runnable code\n4. Wrap the code with ```ruby ... ```\n5. Use `midi` function to allow midi output\n6. CRITICAL: Never use built-in function names (chord, scale, play, sample, amp, pan, rate, etc.) as variable names. Use alternatives like chord_notes, chord_progression, scale_pattern, my_amp, panning, etc."}
    ]
    log("🎼 Step 1: Composer - Creating initial draft...\n")
    draft = composer.chat(composer_prompt)
    log("\n🎼 Composer draft completed.\n")
    log(f"Composer Draft:\n{draft}\n")
    log("=" * 60 + "\n")

    # Step 2: Critic review
    naming_constraints = get_sonic_pi_naming_constraints()
    critic_user_content = f"The following is the Sonic Pi code created by Composer, please review and provide improvement suggestions:\n{draft}\n\n{naming_constraints}\n\nCRITICAL CHECKLIST:\n1. Check if any variables use Sonic Pi built-in function names (chord, scale, play, sample, amp, pan, rate, etc.)\n2. If found, suggest specific alternative variable names (e.g., 'chord' -> 'chord_notes' or 'chord_progression')\n3. Verify code syntax is correct\n4. Ensure all Sonic Pi functions are used correctly"
    
    # Add user feedback if provided
    if user_feedback:
        critic_user_content += f"\n\nUser Feedback:\n{user_feedback}\n\nPlease consider this feedback when reviewing the code."
    
    # Add previous code if provided for comparison
    if previous_code:
        critic_user_content += f"\n\nPrevious Version:\n{previous_code}\n\nPlease compare with the previous version and provide suggestions."
    
    critic_prompt = [
        {"role": "system", "content": critic.role_desc},
        {"role": "user", "content": critic_user_content}
    ]
    log("🧐 Step 2: Critic - Reviewing code and providing feedback...\n")
    feedback = critic.chat(critic_prompt)
    log("\n🧐 Critic feedback completed.\n")
    log(f"Critic Feedback:\n{feedback}\n")
    log("=" * 60 + "\n")

    # Step 3: Arranger integrates modifications
    naming_constraints = get_sonic_pi_naming_constraints()
    arranger_prompt = [
        {"role": "system", "content": arranger.role_desc},
        {"role": "user", "content": f"The following is the original work and modification suggestions, please output the final runnable Sonic Pi code:\nOriginal:\n{draft}\n\nModification Suggestions:\n{feedback}\n\n{naming_constraints}\n\nCRITICAL FINAL CHECK:\n1. Replace ALL variables that conflict with Sonic Pi built-in functions with safe alternatives\n2. Common replacements: 'chord' -> 'chord_notes' or 'chord_progression', 'scale' -> 'scale_pattern' or 'scale_notes', 'amp' -> 'amplitude' or 'my_amp', 'pan' -> 'panning' or 'my_pan'\n3. Ensure the code is runnable and follows all Sonic Pi syntax rules\n4. Output the complete code directly, wrapped with ```ruby ... ```"}
    ]
    log("🎵 Step 3: Arranger - Integrating feedback into final code...\n")
    final_output = arranger.chat(arranger_prompt)
    log("\n🎵 Arranger final code completed.\n")
    log("=" * 60 + "\n")

    # Extract Ruby code
    m = re.search(r"```ruby(.*?)```", final_output, re.DOTALL)
    if m:
        sonic_pi_code = m.group(1).strip()
    else:
        # fallback: if no code block, try to extract the entire output
        m = re.search(r"```(.*?)```", final_output, re.DOTALL)
        if m:
            sonic_pi_code = m.group(1).strip()
        else:
            sonic_pi_code = final_output.strip()
    
    # Apply post-processing to fix reserved word variables (as a safety measure)
    # Note: This is a fallback - the AI should already avoid using reserved words
    original_code = sonic_pi_code
    sonic_pi_code = fix_reserved_word_variables(sonic_pi_code)
    if original_code != sonic_pi_code:
        log("⚠️ Post-processing: Fixed reserved word variable names in generated code\n")

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


# ------------------------------
# 音乐文件生成
# ------------------------------

def abc_to_midi(abc_text, midi_path):
    try:
        s = converter.parse(abc_text, format='abc')
        mf = midi.translate.streamToMidiFile(s)
        mf.open(midi_path, 'wb')
        mf.write()
        mf.close()
        print(f"[✅] 已生成 MIDI: {midi_path}")
        return midi_path
    except Exception as e:
        print(f"[❌] ABC 转 MIDI 失败: {e}")
        return None


def midi_to_wav(mid_path, wav_path, soundfont_path=None):
    """
    使用 fluidsynth 或 timidity 渲染 WAV
    """
    if HAVE_MIDI2AUDIO and soundfont_path:
        try:
            fs = FluidSynth(sound_font=soundfont_path)
            fs.midi_to_audio(mid_path, wav_path)
            print(f"[✅] 使用 midi2audio 渲染 WAV 成功: {wav_path}")
            return wav_path
        except Exception as e:
            print(f"[⚠️] midi2audio 渲染失败: {e}")

    if soundfont_path and shutil.which("fluidsynth"):
        try:
            subprocess.run(["fluidsynth", "-ni", soundfont_path, mid_path, "-F", wav_path, "-r", "44100"], check=True)
            print(f"[✅] 使用系统 fluidsynth 渲染 WAV 成功: {wav_path}")
            return wav_path
        except Exception as e:
            print(f"[⚠️] fluidsynth 渲染失败: {e}")

    if shutil.which("timidity"):
        try:
            subprocess.run(["timidity", mid_path, "-Ow", "-o", wav_path], check=True)
            print(f"[✅] 使用 timidity 渲染 WAV 成功: {wav_path}")
            return wav_path
        except Exception as e:
            print(f"[⚠️] timidity 渲染失败: {e}")

    print("[❌] 未找到可用的音频渲染工具，请手动转换。")
    return None


# ------------------------------
# 主流程
# ------------------------------

def main():
    parser = argparse.ArgumentParser(description="多智能体音乐生成系统")
    parser.add_argument("--prompt", "-p", type=str, required=True, help="音乐描述文本")
    parser.add_argument("--output_dir", "-o", type=str, default="outputs", help="输出文件夹")
    parser.add_argument("--soundfont", type=str, default="", help="可选 SoundFont 文件 (.sf2)")
    parser.add_argument("--model", type=str, default="gpt-4o-mini", help="OpenAI 模型名称")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True, parents=True)

    client = OpenAI(api_key='API_KEY', base_url="https://api.deepseek.com/v1")

    print("\n🎹 正在生成音乐...\n")

    abc_code = multi_agent_generate_abc(args.prompt, client)
    if not abc_code:
        print("[❌] 生成失败，未获取到 ABC 内容。")
        return

    # 保存 ABC 文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    abc_path = output_dir / f"music_{timestamp}.abc"
    midi_path = output_dir / f"music_{timestamp}.mid"
    wav_path = output_dir / f"music_{timestamp}.wav"

    with open(abc_path, "w", encoding="utf-8") as f:
        f.write(abc_code)
    print(f"[✅] 已保存 ABC 文件: {abc_path}")

    # 转换
    if abc_to_midi(abc_code, str(midi_path)):
        midi_to_wav(str(midi_path), str(wav_path), args.soundfont)

    print("\n🎉 全流程结束！")
    print(f"输出文件：\n  ABC:  {abc_path}\n  MIDI: {midi_path}\n  WAV:  {wav_path if wav_path.exists() else '未生成'}")


if __name__ == "__main__":
    main()
