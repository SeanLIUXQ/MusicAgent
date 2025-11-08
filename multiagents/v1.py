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
        {"role": "user", "content": f"请根据以下描述创作一段 ABC 音乐：\n{prompt_text}\n要求输出完整 ABC 代码块，用 ```abc ... ``` 包裹。"}
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

    client = OpenAI(api_key='API_KEY', base_url="https://api.deepseek.com")

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
