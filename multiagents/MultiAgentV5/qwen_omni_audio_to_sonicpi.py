#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
qwen_omni_audio_to_sonicpi.py  (Qwen-Omni 音频 → Sonic Pi 辅助模块)

独立模块：把本地音频文件 (wav/mp3/flac/m4a/ogg) 丢给 Qwen3-Omni-Flash，
让模型听完之后：
1) 给出一段简短的英文描述 music_prompt（可接入你现有的文本工作流）
2) 给出一段 Sonic Pi 代码（Ruby DSL），可直接在 Sonic Pi 中运行。

使用方式（命令行）：
    python qwen_omni_audio_to_sonicpi.py path/to/audio.wav

在项目里：
    from qwen_omni_audio_to_sonicpi import call_qwen_audio_to_code
    music_prompt, code = call_qwen_audio_to_code("xxx.wav")
"""

import os
import sys
import re
import json
import base64
from typing import Tuple, Optional

from openai import OpenAI

# ------------------------------
# 配置区
# ------------------------------

# 支持的音频格式（可按需增减）
SUPPORTED_AUDIO_EXTS = {
    ".wav": "audio/wav",
    ".mp3": "audio/mpeg",
    ".flac": "audio/flac",
    ".m4a": "audio/m4a",
    ".ogg": "audio/ogg",
}
qwen_api_key = 'sk-e960c6602f8c4f858104d1778fcad1c5'
# 默认使用的模型名称（可通过环境变量覆盖）
DEFAULT_MODEL = os.getenv("QWEN_OMNI_MODEL") or "qwen3-omni-flash"


def encode_audio_to_data_url(path: str) -> Tuple[str, str]:
    """
    把本地音频文件读入并转成 data URL 形式的 Base64 字符串，
    返回 (data_url, format_str)：
        data_url: "data:audio/wav;base64,...."
        format_str: "wav" / "mp3" / ...
    """
    if not os.path.exists(path):
        raise FileNotFoundError(f"音频文件不存在: {path}")

    ext = os.path.splitext(path)[1].lower()
    if ext not in SUPPORTED_AUDIO_EXTS:
        raise ValueError(
            f"不支持的音频后缀 {ext}，目前支持: {', '.join(sorted(SUPPORTED_AUDIO_EXTS.keys()))}"
        )

    mime = SUPPORTED_AUDIO_EXTS[ext]
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")

    data_url = f"data:{mime};base64,{b64}"
    fmt = ext.lstrip(".")
    return data_url, fmt


def get_qwen_client() -> OpenAI:
    """
    初始化 Qwen OpenAI-兼容客户端。

    需要环境变量：
        DASHSCOPE_API_KEY
        （可选）DASHSCOPE_BASE_URL

    例如（Beijing）：
        setx DASHSCOPE_API_KEY "sk-xxx"
        setx DASHSCOPE_BASE_URL "https://dashscope.aliyuncs.com/compatible-mode/v1"
    """
    api_key = os.getenv("DASHSCOPE_API_KEY", qwen_api_key)  #设置qwen3-omni-flash的API KEY
    if not api_key:
        raise RuntimeError("请先设置环境变量 DASHSCOPE_API_KEY")

    base_url = os.getenv("DASHSCOPE_BASE_URL") or \
        "https://dashscope.aliyuncs.com/compatible-mode/v1"

    print(f"[QWEN] Using base_url={base_url}", file=sys.stderr)
    return OpenAI(
        api_key=api_key,
        base_url=base_url,
    )


# 提示词：不再要求 JSON，改为「一行描述 + ```ruby``` 代码块」
SYSTEM_PROMPT = (
    "You are a music-transcription assistant that listens to short monophonic "
    "or mildly polyphonic music audio and converts it into Sonic Pi code.\n\n"
    "Your PRIMARY goal is to approximate the actual note sequence, intervals, "
    "and rhythms you hear in the audio, not to invent a generic C-major scale.\n\n"
    "Output format:\n"
    "1. First, output ONE short English sentence describing tempo, mood, "
    "   and instrumentation.\n"
    "2. Then a blank line.\n"
    "3. Then a Sonic Pi Ruby code block:\n"
    "   ```ruby\n"
    "   ... Sonic Pi code only ...\n"
    "   ```\n\n"
    "Transcription rules:\n"
    "- Try to match the contour (up/down movement) and repeated motifs you hear.\n"
    "- Use at least 16–32 notes if the audio is longer than 4 seconds.\n"
    "- Use `sleep` values that reflect the actual rhythm (long vs short notes).\n"
    "- Avoid simple ascending or descending scales unless the audio truly is a scale.\n"
)



USER_INSTRUCTION_TEXT = (
    "Listen to this audio and extract the main melody suitable for Sonic Pi.\n"
    "- Assume 4/4 time unless the rhythm clearly suggests otherwise.\n"
    "- If there are chords, approximate them with simple patterns.\n"
    "- Focus on making the Sonic Pi code executable and musically plausible.\n"
    "Now follow the required output format exactly."
)


def _debug_print_chunks_header():
    print("[QWEN] --- Streaming response from Qwen-Omni ---", file=sys.stderr)


def _debug_print_chunk(idx: int, delta) -> None:
    """
    打印每个 chunk 的关键信息，方便 debug。
    """
    # 有些 SDK 会把 content 放在 delta.content (str)，也有可能是 list
    content = getattr(delta, "content", None)
    audio = getattr(delta, "audio", None)

    prefix = f"[QWEN][chunk {idx}] "
    if isinstance(content, str):
        snippet = content.replace("\n", "\\n")[:80]
        print(prefix + f"content(str)='{snippet}...'", file=sys.stderr)
    elif isinstance(content, list):
        # Qwen 部分实现可能会把文本拆成 list[{'type': 'output_text', 'text': '...'}]
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") in ("output_text", "text"):
                texts.append(item.get("text", ""))
        joined = " ".join(texts).replace("\n", "\\n")[:80]
        print(prefix + f"content(list texts)='{joined}...'", file=sys.stderr)
    else:
        print(prefix + f"content(type={type(content).__name__})", file=sys.stderr)

    if audio:
        print(prefix + f"has audio chunk (len={len(audio.get('data',''))})", file=sys.stderr)


def _accumulate_text_from_stream(completion) -> str:
    """
    从 streaming completion 里把所有文本内容拼接起来，带详细日志。
    """
    full_text = ""
    _debug_print_chunks_header()
    for idx, chunk in enumerate(completion):
        if not getattr(chunk, "choices", None):
            continue
        delta = chunk.choices[0].delta
        _debug_print_chunk(idx, delta)

        content = getattr(delta, "content", None)
        if isinstance(content, str):
            full_text += content
        elif isinstance(content, list):
            # 兼容 list 形式
            for item in content:
                if isinstance(item, dict) and item.get("type") in ("output_text", "text"):
                    full_text += item.get("text", "")
    return full_text


def _parse_text_to_prompt_and_code(full_text: str) -> Tuple[str, str]:
    """
    从模型完整输出里解析：
        music_prompt: 代码块前的那一段文本
        sonic_pi_code: ```ruby ... ``` 里的代码

    如果没有找到 ```ruby```，则尝试普通 ```...```；再不行，直接把全文当作代码返回。
    """
    stripped = full_text.strip()
    print("[QWEN] --- Full raw model output (first 400 chars) ---", file=sys.stderr)
    print(stripped[:400].replace("\n", "\\n") + ("..." if len(stripped) > 400 else ""), file=sys.stderr)

    # 先找 ```ruby
    m = re.search(r"```ruby(.*?)```", stripped, re.DOTALL | re.IGNORECASE)
    if not m:
        # 再找任意 ```...```
        m = re.search(r"```(.*?)```", stripped, re.DOTALL)
    if m:
        code = m.group(1).strip()
        # prompt = 代码块之前的内容
        prompt = stripped[:m.start()].strip()
        # 把开头的 ```json 那种废话去掉
        if prompt.lower().startswith("```json"):
            # 去掉第一行 ```json
            prompt = "\n".join(prompt.splitlines()[1:]).strip()
        if not prompt:
            prompt = "A melody transcribed from the provided audio."
        return prompt, code

    # 如果连 ``` 都没找到，那就认为整个输出就是代码
    print("[QWEN][WARN] 未检测到 ```ruby``` 代码块，直接将全部输出视为 Sonic Pi 代码。", file=sys.stderr)
    return "A melody transcribed from the provided audio.", stripped


def call_qwen_audio_to_code(
    audio_path: str,
    model: Optional[str] = None,
) -> Tuple[str, str]:
    """
    主逻辑：给 Qwen3-Omni-Flash 发请求，把音频转成 (music_prompt, sonic_pi_code)。

    :param audio_path: 本地音频路径
    :param model: 模型名，默认使用环境变量 QWEN_OMNI_MODEL 或 "qwen3-omni-flash"
    :return: (music_prompt, sonic_pi_code)
    """
    print(f"[QWEN] call_qwen_audio_to_code(audio_path={audio_path})", file=sys.stderr)
    data_url, fmt = encode_audio_to_data_url(audio_path)
    print(f"[QWEN] Encoded audio as data URL, format={fmt}", file=sys.stderr)

    client = get_qwen_client()
    model_name = model or DEFAULT_MODEL
    print(f"[QWEN] Using model={model_name}", file=sys.stderr)

    # Qwen-Omni 要求 stream=True；这里只需要文本，不需要语音输出，所以 modalities=["text"]
    completion = client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_audio",
                        "input_audio": {
                            "data": data_url,
                            "format": fmt,
                        },
                    },
                    {
                        "type": "text",
                        "text": USER_INSTRUCTION_TEXT,
                    },
                ],
            },
        ],
        modalities=["text"],          # 只要文本输出
        stream=True,                  # Qwen-Omni 必须 stream=True
        stream_options={"include_usage": True},
        temperature=0.2,      # 降低创造性
        max_tokens=1024,      # 允许多一点音符
    )

    # 累积流式文本内容
    full_text = _accumulate_text_from_stream(completion)
    if not full_text.strip():
        raise RuntimeError("Qwen-Omni 未返回任何文本内容。")

    music_prompt, sonic_pi_code = _parse_text_to_prompt_and_code(full_text)

    if not sonic_pi_code.strip():
        raise RuntimeError("Qwen-Omni 返回的 Sonic Pi 代码为空。")

    print("[QWEN] Parsed music_prompt:", music_prompt, file=sys.stderr)
    print("[QWEN] Sonic Pi code length:", len(sonic_pi_code), file=sys.stderr)

    return music_prompt, sonic_pi_code


def main(argv=None):
    argv = argv or sys.argv[1:]
    if not argv:
        print(
            "用法：python qwen_omni_audio_to_sonicpi.py path/to/audio.wav",
            file=sys.stderr,
        )
        sys.exit(1)

    audio_path = argv[0]
    model_name = os.getenv("QWEN_OMNI_MODEL") or DEFAULT_MODEL

    try:
        music_prompt, sonic_pi_code = call_qwen_audio_to_code(
            audio_path, model=model_name
        )
    except Exception as e:
        print(f"[❌] Qwen-Omni 音频转码失败：{e}", file=sys.stderr)
        raise

    print("===== Music prompt (可接入你原来的文本工作流) =====")
    print(music_prompt)
    print("\n===== Sonic Pi code （可直接粘贴进 Sonic Pi） =====")
    print(sonic_pi_code)


if __name__ == "__main__":
    main()
