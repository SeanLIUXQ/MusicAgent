# MusicAgent  
### Project 版本更新说明：  
## 赵明泽：v2已更新，最新代码在`multiagents`文件夹下。  
## Sean：更新v3版本，对v2版本的API调用以及提示词约束进行改动，最新代码在`./multiagents./v3相关代码`文件夹中；优化GUI界面显示

### 相关说明：
**1. 在midi2music文件夹内，有midi转音频的相关代码环境**

**2. music_llm_dialogue.py是与LLM对话的demo脚本，可以完成上传音频、音频=>MIDI文件、解析JSON、输入自然语言与LLM交互、获取修改音乐风格后的JSON、MIDI=>音频，可以循环对话**  
1. 注意需要使用自己的API-Key，默认使用Qwen3-Max模型，可以自行选择模型  
2. 需要激活虚拟环境使用  
3. 优先使用music_llm_dialogue_V2.py,V1是早期版本  
**3. multiagents文件夹为目前主要demo脚本**
