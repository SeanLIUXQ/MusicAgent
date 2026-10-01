# MusicAgent

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https%3A%2F%2Fgithub.com%2FSeanLIUXQ%2FMusicAgent)

MusicAgent 是一个浏览器原生的 AI 音乐工作台。输入音乐描述后，可以直接试听、查看实时波形、调整编曲与音符，并导出 JSON、MIDI 和 WAV。播放和渲染全部由 Web Audio API 完成，不需要安装 Sonic Pi 或其他播放软件。

## 核心能力

- 自然语言生成结构化多轨音乐
- 浏览器内播放、暂停、停止和播放位置控制
- 实时波形与频谱能量显示
- 轨道静音、音量、声像和波形音色调整
- 音符音高、起点、时值和力度编辑
- 基于当前编曲的反馈修改和风格重编
- MIDI 导入与 JSON、MIDI、WAV 导出
- 无 API Key 时使用内置确定性生成器
- 配置 DeepSeek 后使用 AI 生成与重编

## 环境要求

- Python 3.10+
- Node.js 20.19+ 或 22.12+
- 支持 Web Audio API 的现代浏览器

## 快速启动

Windows 用户可以运行：

```bat
backend\install_deps.bat
backend\start_app.bat
```

启动脚本会构建前端、启动本地服务，并打开 `http://127.0.0.1:5000`。

手动启动：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt

cd frontend
npm install
npm run build
cd ..

.\.venv\Scripts\python.exe backend\app.py
```

## DeepSeek 配置

AI 功能为可选项。未设置 Key 时，系统仍能用本地引擎生成可播放音乐。

```powershell
$env:DEEPSEEK_API_KEY="your-key"
```

可选配置：

```powershell
$env:DEEPSEEK_MODEL="deepseek-chat"
$env:DEEPSEEK_BASE_URL="https://api.deepseek.com/v1"
$env:DEEPSEEK_TIMEOUT="90"
```

## 在线部署

仓库包含 `Dockerfile` 与 `render.yaml`。在 Render 中连接此 GitHub 仓库并应用 Blueprint，即可部署完整的 Flask + Vue Demo。未配置 `DEEPSEEK_API_KEY` 时，在线版本仍会使用内置生成器正常生成、试听、编辑和导出音乐。

## 开发模式

终端一：

```powershell
.\.venv\Scripts\python.exe backend\app.py
```

终端二：

```powershell
cd frontend
npm install
npm run dev
```

访问 `http://127.0.0.1:5173`。Vite 会把 `/api` 代理到本地 Flask 服务。

## 数据格式

生成结果使用统一的 `Composition` JSON：

```json
{
  "title": "Example",
  "tempo": 120,
  "time_signature": [4, 4],
  "duration_beats": 32,
  "tracks": [
    {
      "name": "Lead",
      "waveform": "triangle",
      "gain": 0.7,
      "pan": 0,
      "notes": [
        { "pitch": 60, "start": 0, "duration": 0.5, "velocity": 90 }
      ]
    }
  ]
}
```

这份数据同时驱动播放、可视化、编辑和导出，避免不同输出之间产生偏差。

## 测试

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest backend\tests -q

cd frontend
npm run type-check
npm run lint
npm run build
```

## 安全默认值

- 服务默认只监听 `127.0.0.1`
- 调试模式默认关闭
- CORS 仅允许本机浏览器来源
- 下载路径和扩展名都经过验证
- 后台任务有 TTL、容量上限和并发上限
