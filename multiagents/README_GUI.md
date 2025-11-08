# Sonic Pi 音乐生成器 GUI

这是一个基于PyQt5的图形界面应用，用于通过多智能体系统生成Sonic Pi音乐代码，并自动粘贴到Sonic Pi客户端。

## 功能特性

1. **PyQt5图形界面** - 友好的用户界面，输入音乐描述
2. **多智能体音乐生成** - 使用Composer、Critic、Arranger三个智能体协作生成Sonic Pi代码
3. **自动粘贴功能** - 使用OCR和窗口自动化技术，自动将生成的代码粘贴到Sonic Pi编辑器
4. **用户反馈收集** - 生成音乐后询问用户反馈，用于改进

## 安装依赖

```bash
pip install -r requirements.txt
```

### 额外要求

1. **Tesseract OCR** (用于OCR功能，可选)
   - Windows: 下载安装 [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki)
   - 安装后需要配置环境变量或设置pytesseract路径

2. **Sonic Pi客户端**
   - 下载并安装 [Sonic Pi](https://sonic-pi.net/)
   - 确保Sonic Pi已安装并可以正常运行

## 配置

在使用前，需要配置API密钥。编辑 `gui_app.py` 中的 `init_client` 方法：

```python
def init_client(self):
    api_key = 'YOUR_API_KEY'  # 替换为你的API密钥
    base_url = "https://api.deepseek.com"
    self.client = OpenAI(api_key=api_key, base_url=base_url)
```

或者从环境变量读取：

```python
import os
api_key = os.getenv('DEEPSEEK_API_KEY', 'API_KEY')
```

## 使用方法

1. **启动应用**
   ```bash
   python gui_app.py
   ```

2. **输入音乐描述**
   - 在文本框中输入音乐描述，例如：
     - "一首平静的钢琴独奏，C大调，慢速，梦幻风格"
     - "快节奏的电子音乐，使用鼓点和合成器"
     - "爵士风格的贝斯线，配合钢琴和弦"

3. **生成代码**
   - 点击"生成音乐代码"按钮
   - 等待多智能体系统生成代码（可能需要一些时间）

4. **粘贴到Sonic Pi**
   - 确保Sonic Pi客户端已打开
   - 点击"粘贴到Sonic Pi"按钮
   - 应用会自动找到Sonic Pi窗口并将代码粘贴到编辑器

5. **提供反馈**
   - 粘贴完成后，会弹出反馈对话框
   - 可以输入对生成音乐的反馈意见
   - 反馈可用于改进后续生成

## 工作流程

```
用户输入描述 
    ↓
多智能体生成 (Composer → Critic → Arranger)
    ↓
显示生成的代码
    ↓
自动粘贴到Sonic Pi
    ↓
询问用户反馈
```

## 注意事项

1. **OCR功能**：如果OCR相关库未安装，粘贴功能可能无法正常工作，需要手动复制代码
2. **窗口识别**：应用通过窗口标题"Sonic Pi"来识别客户端，确保Sonic Pi窗口标题包含该字符串
3. **编辑器位置**：代码假设编辑器在窗口上方1/3处，如果Sonic Pi界面布局不同，可能需要调整坐标
4. **API密钥**：需要有效的DeepSeek API密钥才能使用

## 故障排除

### 找不到Sonic Pi窗口
- 确保Sonic Pi已打开
- 检查窗口标题是否包含"Sonic Pi"
- 尝试手动将Sonic Pi窗口置于前台

### OCR功能未启用
- 安装缺失的库：`pip install pyautogui pytesseract pywin32 pyperclip`
- 安装Tesseract OCR并配置路径

### 粘贴失败
- 检查Sonic Pi是否在前台
- 尝试手动点击Sonic Pi编辑器后再点击粘贴按钮
- 检查是否有其他程序占用剪贴板

## 文件说明

- `gui_app.py` - 主GUI应用
- `v2.py` - 多智能体生成逻辑（包含`multi_agent_generate_sonic_pi`函数）
- `requirements.txt` - Python依赖列表

## 开发说明

代码使用PyQt5的信号-槽机制确保线程安全，所有UI操作都在主线程中执行。

