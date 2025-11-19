
# 🎵 MusicAgent v5

多智能体 Sonic Pi 音乐 Agent 系统 — 支持：

- 文本描述 ➜ 生成 Sonic Pi 代码 + MIDI  
- 结合用户反馈进行二次修改（Refinement）  
- 对现有 Sonic Pi 代码做风格迁移（Style Transfer）  
- **从音频文件（wav/mp3 等）直接导入，通过 Qwen3-Omni / DeepSeek 多模态生成 Sonic Pi 代码**  
- 提供桌面 GUI（PyQt5）和 Web API（Flask）两种使用方式  

> 本版本是在 v4 基础上加入了 **音频导入 + Qwen/DeepSeek 全模态能力** 的升级版。

---

## ✨ 功能概览

### 1. 文本 ➜ 音乐代码

- 在 GUI 中输入自然语言描述（中/英皆可），例如：

  > “一个 90 BPM 的 Lo-fi hiphop，主旋律是钢琴，背景有柔和鼓点和贝斯循环”

- 系统通过多智能体（策划 / 作曲 / 编译）协作：

  1. 意图理解 + 需求拆解（阿里云 DashScope / DeepSeek 等 OpenAI-兼容模型）
  2. 生成 Sonic Pi 代码
  3. 编译为 MIDI 文件（可选）

### 2. 用户反馈迭代（Refinement）

- 生成结果后可以点击 **“Provide Feedback”**，输入类似：

  > “鼓点再密一点，贝斯音量小一点，旋律结尾加一个上行”

- 系统会带着：

  - 原始描述 `original_prompt`
  - 当前 Sonic Pi 代码
  - 你的反馈

- 再走一轮生成，输出改进版本的代码。

### 3. 风格迁移（Style Transfer）

- 对现有 Sonic Pi 代码提出风格请求，例如：

  > “把这段改成 130 BPM 摇滚风格，增加电吉他和鼓 Fill”

- `style_transfer.py` 会在保持主题结构的前提下替换乐器 / 篇章结构 / 节奏，输出新的 Sonic Pi 代码。

### 4. 音频文件 ➜ 文本描述 + Sonic Pi 代码

- 支持直接导入音频：
  - `wav / mp3 / flac / m4a / ogg`
- 调用 `qwen_omni_audio_to_sonicpi.py`：
  1. 让 Qwen3-Omni-Flash / 其他 OpenAI-兼容多模态模型“听”音频  
  2. 生成一段英文 `music_prompt`（可直接接入文本工作流）  
  3. 生成一段可在 Sonic Pi 中直接跑的 Sonic Pi 代码  

- 在 GUI 中，这一功能对应按钮：**“🎧 Import from Audio File”**  
- 导入成功后，代码会被当作一次“正式生成结果”，可以继续：
  - 做反馈修改  
  - 做风格迁移  
  - 导出 MIDI  

### 5. Web API

- `app.py` 提供后端接口，适合和前端 / 其他服务对接：
  - `GET /api/health` — 健康检查  
  - `POST /api/generate` — 文本 ➜ Sonic Pi + MIDI  
  - `POST /api/style-transfer` — 风格迁移  
  - `GET /api/task/<task_id>` — 查询异步任务状态  
  - `GET /api/midi/<filename>` — 下载生成的 MIDI 文件  

---

## 🧩 项目结构

核心文件一览：

- `gui_app.py`  
  PyQt5 GUI 主程序：文本生成、反馈、风格迁移、音频导入、代码展示、日志面板。

- `v3.py`  
  多智能体音乐生成核心逻辑：
  - 管理策划 / 作曲 / 编译 agent  
  - 负责 Sonic Pi 代码生成 & 编译为 MIDI (`sonic_pi_code_to_midi`)  

- `style_transfer.py`  
  风格迁移逻辑，对现有 Sonic Pi 代码进行“再编曲”。

- `intent_dispatcher.py`  
  意图理解 & 工具调用调度器：
  - 使用阿里云 DashScope（OpenAI 兼容模式）  
  - 根据意图决定是生成新音乐、改写现有代码还是风格迁移等。

- `qwen_omni_audio_to_sonicpi.py`  
  音频 ➜ 文本 + Sonic Pi 模块：
  - 封装对 Qwen3-Omni-Flash 的调用  
  - 暴露 `call_qwen_audio_to_code(audio_path)` 接口  

- `record_midi.py`  
  调用本地 Sonic Pi + MIDI 端口，录制并保存 MIDI 文件。

- `app.py`  
  Flask 后端 API（适合前后端分离使用）。

---

## 💻 环境与安装

### 1. 前置条件

- Python 3.9+（推荐 3.10/3.11）  
- 操作系统：推荐 Windows 10/11（GUI + Sonic Pi 自动化在 Windows 下测试较多）  
- 已安装 [Sonic Pi]（需要手动安装，可从官网获取）  
- 如需 MIDI ➜ 音频：
  - 系统中安装 Fluidsynth + SoundFont（`midi2audio` 依赖）

### 2. 创建虚拟环境

```bash
cd MusicAgentV5

# 创建并激活虚拟环境（示例为 Windows PowerShell）
python -m venv venv
.\venv\Scripts\activate
```
