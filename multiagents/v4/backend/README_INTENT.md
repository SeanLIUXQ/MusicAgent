# 意图理解功能说明 (v4\backend)

本项目已集成通义千问的意图理解模型 (`tongyi-intent-detect-v3`)，可以在生成音乐代码前先理解用户意图，并将意图理解结果作为增强输入传递给后续的大模型处理。

## 功能说明

1. **用户输入文字** → 调用意图理解模型
2. **意图理解结果** → 作为增强输入传递给 `v3.multi_agent_generate_sonic_pi`

意图理解模型会：
- 识别用户的意图（如生成音乐、风格转换、修改音乐等）
- 提取关键参数（如音乐风格、节奏、调性等）
- 将意图和参数信息附加到原始输入中，形成增强的输入文本

## 配置方法

### 1. 设置环境变量

在使用前，需要配置 DashScope API Key：

**Windows (PowerShell):**
```powershell
$env:DASHSCOPE_API_KEY="your_api_key_here"
```

**Windows (CMD):**
```cmd
set DASHSCOPE_API_KEY=your_api_key_here
```

**Linux/Mac:**
```bash
export DASHSCOPE_API_KEY="your_api_key_here"
```

或者创建 `.env` 文件（如果项目支持）：
```
DASHSCOPE_API_KEY=your_api_key_here
```

### 2. 获取 API Key

1. 访问 [阿里云百炼平台](https://dashscope.aliyun.com/)
2. 注册/登录账号
3. 开通服务并获取 API Key
4. 将 API Key 配置到环境变量中

**注意**：代码中已内置默认 API Key，如果未设置环境变量，将使用默认 Key。

## 工作流程

```
用户输入: "我想生成一首慢速的钢琴独奏，C大调，梦幻风格"
        ↓
意图理解模型分析
        ↓
识别意图: 生成音乐
提取参数: style="钢琴独奏", tempo="慢速", key="C大调", mood="梦幻风格"
        ↓
增强输入: "我想生成一首慢速的钢琴独奏，C大调，梦幻风格

[意图理解结果]
意图: [music generation]
调用工具: generate_music, 参数: {"style": "钢琴独奏", "tempo": "慢速", "key": "C大调", "mood": "梦幻风格"}"
        ↓
传递给 v3.multi_agent_generate_sonic_pi
```

## 支持的工具

意图理解模型支持以下音乐相关工具：

1. **generate_music** - 生成新音乐
   - 参数: style, tempo, key, mood, instruments

2. **style_transfer** - 风格转换
   - 参数: target_style, original_style

3. **modify_music** - 修改音乐
   - 参数: modification_type, details

## 容错处理

如果未配置 API Key 或意图理解失败：
- 系统会自动使用原始输入继续处理
- 不会中断音乐生成流程
- 会在日志中显示警告信息

## 使用示例

运行 GUI 应用：
```bash
cd multiagents/v4/backend
python gui_app.py
```

在界面中输入音乐描述，系统会自动：
1. 先调用意图理解模型分析输入
2. 将意图理解结果作为增强输入
3. 使用增强输入生成音乐代码

## 注意事项

1. **API Key 配置**：确保正确配置 `DASHSCOPE_API_KEY` 环境变量，或使用默认内置的 Key
2. **网络连接**：需要能够访问阿里云 DashScope API
3. **API 费用**：意图理解模型有免费额度（100万Token，90天有效），超出后按量计费
4. **响应速度**：意图理解模型响应速度快（百毫秒级），不会显著影响整体流程

## 查看日志

在 GUI 界面的日志区域可以查看：
- 原始用户输入
- 意图理解阶段的输出
- 增强后的输入文本
- 后续音乐生成的详细日志

## 技术实现

### 核心文件

1. **intent_dispatcher.py** - 意图理解调度器
   - `call_intent_model()` - 调用意图理解模型
   - `dispatch_intent()` - 根据意图调度到相应功能
   - `dispatch_to_generate_music()` - 调度到音乐生成
   - `dispatch_to_style_transfer()` - 调度到风格转换

2. **gui_app.py** - GUI应用主文件
   - `GenerateThread.run()` - 集成了意图理解调度器
   - 自动调用 `intent_dispatcher.dispatch_intent()`

### 与 v3 模块的集成

意图理解调度器会根据识别的意图调用：
- `v3.multi_agent_generate_sonic_pi()` - 生成或修改音乐
- `style_transfer.style_transfer_sonic_pi()` - 风格转换

## 与原版的区别

本版本基于 multiagents 目录下的意图理解代码适配到 v4\backend：

1. **模块调用改变**：从 v2 改为 v3 模块
2. **目录结构**：适配 v4\backend 的目录结构
3. **兼容性**：保持与 v3.multi_agent_generate_sonic_pi 的完全兼容

## 故障排除

### 问题：意图理解失败

**解决方法**：
1. 检查网络连接
2. 确认 API Key 是否正确
3. 查看日志中的错误信息
4. 系统会自动降级使用原始输入，不影响基本功能

### 问题：工具调用未识别

**解决方法**：
1. 查看日志中的意图理解结果
2. 调度器会根据关键词推断意图
3. 支持的关键词：
   - 风格转换：'转换', '改成', '变成', '改为', '风格'
   - 修改音乐：'修改', '调整', '改进', '反馈', '更快', '更慢'
