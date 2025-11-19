# 🎵 MusicAgent v4 Backend

智能音乐生成系统 - 使用多智能体协作生成 Sonic Pi 音乐代码和 MIDI 文件

---

## 🚀 快速开始

### 1️⃣ 安装依赖

**方法 A：使用脚本（推荐）**
```
双击运行：安装依赖.bat
```

**方法 B：手动安装**
```powershell
pip install openai PyQt5 music21 mido
```

### 2️⃣ 配置 API Key

```powershell
# 设置环境变量
$env:DEEPSEEK_API_KEY="sk-your-api-key-here"
```

或修改 `gui_app.py` 第 598 行

### 3️⃣ 启动应用

```
双击运行：启动应用.bat
```

或手动启动：
```powershell
python gui_app.py
```

---

## 📁 文件说明

### 核心文件

| 文件 | 说明 |
|------|------|
| `gui_app.py` | 桌面应用主程序（PyQt5 GUI） |
| `v3.py` | 多智能体音乐生成核心逻辑 |
| `intent_dispatcher.py` | 意图理解调度器 |
| `style_transfer.py` | 风格转换模块 |
| `app.py` | Flask Web 后端（可选） |

### 工具脚本

| 文件 | 说明 |
|------|------|
| `启动应用.bat` | 一键启动脚本（带依赖检查） |
| `安装依赖.bat` | 一键安装所有依赖 |
| `检查依赖.py` | 依赖检查工具 |

### 文档

| 文件 | 说明 |
|------|------|
| `README.md` | 本文件（快速参考） |
| `快速开始.md` | 详细使用指南 |
| `API_KEY_配置指南.md` | API Key 配置教程 |
| `README_INTENT.md` | 意图理解功能说明 |
| `INTENT_INTEGRATION_SUMMARY.md` | 集成总结文档 |

### 配置文件

| 文件 | 说明 |
|------|------|
| `requirements.txt` | Python 依赖列表 |
| `midi_output/` | MIDI 文件输出目录 |

---

## ⚙️ 核心功能

### 🎵 音乐生成
- 根据文字描述生成 Sonic Pi 代码
- 自动编译为 MIDI 文件
- 支持多种音乐风格和乐器

### 🎯 意图理解
- 智能识别用户意图（生成/转换/修改）
- 自动提取音乐参数（风格、节奏、调性等）
- 通义千问模型支持

### 🎨 风格转换
- 转换已生成音乐的风格
- 保持原有结构，改变表现形式

### 🔄 反馈迭代
- 根据用户反馈改进音乐
- 支持多次迭代优化

### 💾 MIDI 导出
- 自动编译为标准 MIDI 文件
- 支持 Sonic Pi 播放和其他音乐软件导入

---

## 🛠️ 常用命令

### 检查依赖
```powershell
python 检查依赖.py
```

### 安装依赖
```powershell
pip install -r requirements.txt
```

### 安装单个包
```powershell
# 修复 MIDI 编译失败
pip install mido

# 其他核心依赖
pip install openai PyQt5 music21
```

### 启动应用
```powershell
# 桌面应用
python gui_app.py

# Web 应用（需要额外安装 flask）
python app.py
```

---

## ⚠️ 常见问题

### ❌ 401 认证错误
```
Error code: 401 - Authentication Fails
```
**解决**：配置有效的 DeepSeek API Key  
**查看**：`API_KEY_配置指南.md`

### ⚠️ MIDI 编译失败
```
Warning: mido library required for MIDI compilation
```
**解决**：`pip install mido`

### ❌ 模块导入错误
```
ModuleNotFoundError: No module named 'xxx'
```
**解决**：`pip install -r requirements.txt`

### ⚠️ 自动化功能不可用
```
[⚠️] pyautogui not installed
```
**说明**：可选功能，不影响音乐生成

---

## 📊 系统架构

### 多智能体协作

```
用户输入
    ↓
意图理解（Intent Dispatcher）
    ↓
┌─────────────────────────┐
│  1. Translator - 翻译   │ → 专业音乐术语
│  2. Composer - 作曲     │ → 初稿创作
│  3. Critic - 评论       │ → 改进建议
│  4. Arranger - 编曲     │ → 最终版本
│  5. Compiler - 编译     │ → MIDI 文件
└─────────────────────────┘
    ↓
Sonic Pi 代码 + MIDI 文件
```

### 技术栈

- **GUI**: PyQt5
- **音乐处理**: music21, mido
- **AI 模型**: DeepSeek / OpenAI
- **意图理解**: 通义千问 (tongyi-intent-detect-v3)
- **Web 后端**: Flask (可选)

---

## 📚 详细文档

- **新手入门**：查看 `快速开始.md`
- **API 配置**：查看 `API_KEY_配置指南.md`
- **意图理解**：查看 `README_INTENT.md`
- **功能总结**：查看 `INTENT_INTEGRATION_SUMMARY.md`

---

## 🔗 相关链接

- **DeepSeek 平台**: https://platform.deepseek.com/
- **通义千问**: https://dashscope.aliyun.com/
- **Sonic Pi**: https://sonic-pi.net/

---

## 📝 使用示例

### 基础生成
```
输入：生成一首慢速的钢琴独奏，C大调，梦幻风格
输出：Sonic Pi 代码 + MIDI 文件
```

### 风格转换
```
输入：转换为爵士风格
输出：爵士风格的 Sonic Pi 代码
```

### 反馈修改
```
输入：速度再快一点，音调高一些
输出：改进后的音乐
```

---

## 🎯 系统要求

- **Python**: 3.8 或更高版本
- **操作系统**: Windows / Linux / macOS
- **网络**: 需要访问 AI API（DeepSeek / OpenAI）
- **内存**: 建议 4GB+

---

## 📄 许可证

本项目用于研究和学习目的。

---

## 🆘 获取帮助

1. 查看相关文档
2. 运行 `python 检查依赖.py` 诊断问题
3. 查看应用日志输出
4. 检查 API 配置和网络连接

---

**版本**: v4  
**更新时间**: 2025-11-17  
**状态**: ✅ 已集成意图理解功能

🎵 享受智能音乐创作！
