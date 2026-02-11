# 🎵 MusicAgent 1.0 - AI音乐生成系统

> 用自然语言描述你想要的音乐，AI帮你生成可播放的音乐代码和MIDI文件！

[![GitHub stars](https://img.shields.io/github/stars/SeanLIUXQ/MusicAgent?style=social)](https://github.com/SeanLIUXQ/MusicAgent/stargazers)
[![Python 81.4%](https://img.shields.io/badge/Python-81.4%25-blue)](https://github.com/SeanLIUXQ/MusicAgent)
[![Vue 16.6%](https://img.shields.io/badge/Vue-16.6%25-green)](https://github.com/SeanLIUXQ/MusicAgent)

---

## 📖 项目简介

MusicAgent是一个基于AI的智能音乐生成系统。通过调用大语言模型(LLM)，结合用户的提示词，实现：
- 文字描述转换为Sonic Pi音乐代码
- 音频文件风格转换
- MIDI文件生成和导出

**核心特性：**
- ✅ **稳定运行** - Bug较少，核心功能完善
- ✅ **Text→Code** - 自然语言生成音乐代码
- ✅ **Audio→MIDI** - 音频文件转换为MIDI
- ✅ **双界面支持** - 桌面GUI + Web前后端

---

## 🚀 快速开始

### 环境要求

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Python | ≥ 3.8 | 核心运行环境 |
| Sonic Pi | 最新版 | 音乐播放软件 |
| DeepSeek API Key | - | 必需配置 |

### 克隆仓库

```bash
git clone https://github.com/SeanLIUXQ/MusicAgent.git
cd MusicAgent
```

### 安装依赖

**进入backend目录：**
```bash
cd backend
```

**方法A - Windows自动安装（推荐）：**
```bash
# 双击运行
安装依赖.bat
```

**方法B - 手动安装：**
```bash
pip install -r requirements.txt
```

**核心依赖包：**
- `openai` - DeepSeek API调用
- `PyQt5` - 桌面GUI界面
- `music21` - 音乐理论处理
- `mido` - MIDI文件操作
- `flask` - Web后端服务

### 配置API密钥

**DeepSeek API（必需）：**

1. 访问 [platform.deepseek.com](https://platform.deepseek.com/) 获取API Key
2. 配置方式（二选一）：

**方式1 - 环境变量（推荐）：**
```bash
# Windows PowerShell
$env:DEEPSEEK_API_KEY="sk-your-api-key-here"

# Mac/Linux
export DEEPSEEK_API_KEY="sk-your-api-key-here"
```

**方式2 - 修改代码：**
```python
# 在 backend/gui_app.py 和 backend/app.py 中
# 找到 init_client 方法，替换API密钥
api_key = 'sk-your-api-key-here'
```

**千问Omni API（音频功能）：**
- API Key已内置在 `backend/qwen_omni_audio_to_sonicpi.py`
- **无需额外配置**

---

## 💻 运行应用

### 方式A：桌面GUI应用（推荐）

```bash
cd backend

# Windows - 双击运行
启动应用.bat

# 或手动运行
python gui_app.py
```

**功能：**
- ✅ 文字生成音乐代码
- ✅ 音频文件上传转换
- ✅ 风格转换
- ✅ 反馈优化
- ✅ MIDI导出

### 方式B：Web应用（前后端分离）

**终端1 - 启动后端：**
```bash
cd backend
python app.py
```

**终端2 - 启动前端：**
```bash
cd frontend/music-agent/dist
python -m http.server 5173
```

**访问：** http://localhost:5173

**前端界面预览：**

![MusicAgent前端](https://private-user-images.githubusercontent.com/205925075/517274752-f8dafffa-5a95-480b-b91d-747e01e14bde.png?jwt=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJnaXRodWIuY29tIiwiYXVkIjoicmF3LmdpdGh1YnVzZXJjb250ZW50LmNvbSIsImtleSI6ImtleTUiLCJleHAiOjE3NzA3ODQ1NjksIm5iZiI6MTc3MDc4NDI2OSwicGF0aCI6Ii8yMDU5MjUwNzUvNTE3Mjc0NzUyLWY4ZGFmZmZhLTVhOTUtNDgwYi1iOTFkLTc0N2UwMWUxNGJkZS5wbmc_WC1BbXotQWxnb3JpdGhtPUFXUzQtSE1BQy1TSEEyNTYmWC1BbXotQ3JlZGVudGlhbD1BS0lBVkNPRFlMU0E1M1BRSzRaQSUyRjIwMjYwMjExJTJGdXMtZWFzdC0xJTJGczMlMkZhd3M0X3JlcXVlc3QmWC1BbXotRGF0ZT0yMDI2MDIxMVQwNDMxMDlaJlgtQW16LUV4cGlyZXM9MzAwJlgtQW16LVNpZ25hdHVyZT0xNDc0ZWEyODU5NWRhMzVlMWVkMWE4MmIwYjgxZDk0NjNiZjliMzg3YTE5OTRmNTVjOGY5NWIwZTc5MmIzZjRiJlgtQW16LVNpZ25lZEhlYWRlcnM9aG9zdCJ9.Z5qnuec4g8i9NYZJ4iKjrnyRdCZi4xs3og5FBNcFMlo)

---

## 📋 使用指南

### 1. 文字生成音乐

**示例输入：**
```
一首平静的钢琴独奏，C大调，60 BPM，梦幻风格，适合冥想
```

**流程：**
1. 在界面输入音乐描述
2. 点击"生成音乐代码"
3. 等待3-5分钟（AI智能体协作创作）
4. 复制生成的Sonic Pi代码
5. 粘贴到Sonic Pi并运行

**生成内容：**
- Sonic Pi代码（可直接运行）
- MIDI文件（保存在`backend/midi_output/`）

### 2. 音频转代码

**支持格式：** MP3, WAV

**流程：**
1. 点击"上传音频"
2. 选择音频文件
3. 系统自动分析并生成代码
4. 复制到Sonic Pi运行

### 3. 风格转换

**前提：** 已生成音乐代码

**示例：**
```
转换为爵士风格
改成轻柔的风格
变成摇滚风格
```

### 4. 反馈优化

**示例反馈：**
```
速度太慢了，再快一点
音调太高，降低一些
缺少节奏感，加入鼓点
```

**建议：** 迭代2-3次达到最佳效果

---

## 🏗️ 项目结构

```
MusicAgent/
├── backend/                    # 后端代码
│   ├── app.py                  # Flask Web API
│   ├── gui_app.py              # PyQt5桌面应用
│   ├── v3.py                   # 多智能体核心逻辑
│   ├── intent_dispatcher.py    # 意图理解模块
│   ├── style_transfer.py       # 风格转换模块
│   ├── qwen_omni_audio_to_sonicpi.py  # 音频转代码
│   ├── requirements.txt        # Python依赖
│   ├── 安装依赖.bat            # Windows安装脚本
│   ├── 启动应用.bat            # Windows启动脚本
│   └── midi_output/           # MIDI输出目录
│
├── frontend/                   # 前端代码 (Vue.js)
│   └── music-agent/
│       └── dist/              # 构建文件
│
└── README.md                  # 项目文档
```

---

## 🎯 核心技术

### 多智能体协作

```
用户输入
    ↓
意图理解 (Intent Detector)
    ↓
翻译官 (Translator) → 专业音乐术语
    ↓
作曲家 (Composer) → 创作代码
    ↓
评论家 (Critic) → 评价质量
    ↓
编曲师 (Arranger) → 优化完善
    ↓
编译器 (Compiler) → 生成MIDI
    ↓
输出：Sonic Pi代码 + MIDI文件
```

### AI模型

| 模型 | 用途 | 配置 |
|------|------|------|
| DeepSeek | 音乐代码生成 | 需要API Key |
| 通义千问 | 意图理解 | 可选 |
| 千问Omni | 音频分析 | 需配置 API KEY |

---

## ⚠️ 已知问题

| 问题 | 说明 | 解决方案 |
|------|------|---------|
| 代码生成时间长 | 3-5分钟 | 正常现象，请耐心等待 |
| 反馈模块偶尔无响应 | 稳定性问题 | 等待30秒或重试 |
| 需手动复制代码 | 未实现自动化 | 手动复制到Sonic Pi |
| 日志为中文 | 待优化 | 后续版本改进 |

---

## ❓ 常见问题

<details>
<summary><b>Q1: 为什么生成需要3-5分钟？</b></summary>

AI需要经过多个智能体协作：理解描述 → 翻译术语 → 创作初稿 → 评价改进 → 编译MIDI

这是正常现象，请耐心等待，不要重复点击。
</details>

<details>
<summary><b>Q2: 代码在Sonic Pi中无法播放？</b></summary>

可能原因：
1. **语法错误** - 使用反馈功能告诉AI错误信息
2. **音色不支持** - 尝试反馈修改乐器
3. **代码不完整** - 确保完整复制所有代码

建议：使用反馈功能2-3次通常能解决
</details>

<details>
<summary><b>Q3: API认证失败（Error 401）？</b></summary>

检查项：
1. `DEEPSEEK_API_KEY`环境变量是否正确设置
2. API密钥是否有效且有余额
3. 参考配置章节重新设置
</details>

<details>
<summary><b>Q4: MIDI文件保存在哪里？</b></summary>

位置：`backend/midi_output/`
格式：`music_YYYYMMDD_HHMMSS.mid`
</details>

<details>
<summary><b>Q5: 反馈/风格转换无响应？</b></summary>

临时解决：
1. 等待30秒-1分钟
2. 重新提交或重启应用
3. 每次只提一个具体要求

这是已知问题，后续版本会优化
</details>

---

## 💡 使用技巧

### 描述要点

**✅ 好的描述：**
```
一首轻柔的钢琴独奏，C大调，60 BPM，梦幻风格，适合冥想
```

**❌ 不好的描述：**
```
一首好听的音乐
```

### 音乐术语参考

| 类型 | 示例 |
|------|------|
| 调性 | C大调、A小调、G大调 |
| 节奏 | 慢速(60-80 BPM)、中速(90-120 BPM)、快速(130+ BPM) |
| 风格 | 古典、爵士、摇滚、电子、民谣 |
| 乐器 | 钢琴、吉他、鼓、贝斯、合成器 |

### 最佳实践

1. **分步调整**
   - 第1次：生成基础框架
   - 第2次：调整节奏速度
   - 第3次：优化音色层次

2. **保存版本**
   - 及时保存满意的MIDI文件
   - 避免过度修改丢失好版本

3. **巧用风格转换**
   - 先生成满意的结构
   - 再尝试不同风格
   - 快速对比效果

---

## 🔧 故障排除

### 依赖问题

**检查依赖：**
```bash
cd backend
python 检查依赖.py
```

**常见错误修复：**
```bash
# ModuleNotFoundError
pip install <模块名>

# MIDI编译失败
pip install mido music21

# GUI无法启动
pip install PyQt5
```

### 网络问题

- 检查网络连接
- 确认能访问DeepSeek API
- 必要时使用代理

---

## 📚 技术文档

### API服务

| 服务 | 用途 | 链接 |
|------|------|------|
| DeepSeek | 音乐生成 | https://platform.deepseek.com |
| 通义千问 | 意图理解 | https://dashscope.aliyun.com |
| Sonic Pi | 音乐播放 | https://sonic-pi.net |

### 开发文档

- `README_INTENT.md` - 意图理解详解
- `INTENT_INTEGRATION_SUMMARY.md` - 系统集成
- `README_GUI.md` - GUI应用开发

---

## 📝 版本信息

**当前版本：** v1.0 (稳定版)  
**发布时间：** 2025  
**状态：** ✅ 稳定运行，Bug较少

**功能清单：**
- [x] 文字转音乐代码
- [x] 音频转代码（MP3/WAV）
- [x] 风格转换
- [x] 反馈优化
- [x] MIDI导出/加载
- [x] 意图理解
- [x] 桌面GUI
- [x] Web界面

---

## 🤝 参与贡献

欢迎提交Issue和Pull Request！

**贡献方向：**
- 🐛 Bug修复
- ✨ 新功能
- 📝 文档改进
- 🎨 界面优化

---

## 📜 许可证

本项目用于研究和学习目的。

---

## 🎉 开始创作

```bash
# 1. 克隆项目
git clone https://github.com/SeanLIUXQ/MusicAgent.git

# 2. 安装依赖
cd MusicAgent/backend
pip install -r requirements.txt

# 3. 配置API Key
export DEEPSEEK_API_KEY="sk-your-key"

# 4. 启动应用
python gui_app.py
```

🎵 **祝你音乐创作愉快！**

---

<div align="center">

**Star ⭐ 本项目如果觉得有帮助！**

[项目主页](https://github.com/SeanLIUXQ/MusicAgent) · [问题反馈](https://github.com/SeanLIUXQ/MusicAgent/issues) · [参与贡献](https://github.com/SeanLIUXQ/MusicAgent/pulls)

</div>
