# MusicAgent  
### Project 版本更新说明：  

### 赵明泽：v2已更新，最新代码在`multiagents`文件夹下。  
### Sean：更新v3版本，对v2版本的API调用以及提示词约束进行改动，最新代码在`./multiagents./v3相关代码`文件夹中；优化GUI界面显示
### 李睿恒：v4已经更新，最新代码在`multiagents`的v4文件夹下，包含前端vue和后端flask，优化了GUI，并在v4文件夹的v3代码中删除不使用的内容
### Sean：更新v5版本 2025-11-19：
1、使用千问的omni模型，增加了代码模块qwen_omni_audio_to_sonicpi.py  (Qwen-Omni 音频 → Sonic Pi 辅助模块)，实现上传音频转码，并且可以聚合到风格迁移获得反馈的流程中。  
2、还是用的gui_app.py来配置的，可能后续还得和前端对接修改，配置环境、API Key之后直接启动gui_app.py即可。  
3、V5版本代码已经上传仓库：MusicAgent/multiagents/MultiAgentV5。  
### 李睿恒：对v5版本进行前后端的设计，并实现前端打包，现在可以不配置环境打开网页：
    1. cd进\MusicAgent\multiagents\v4\frontend\music-agent\dist目录
    2. 使用python的命令： python -m http.server 5173
    3. 浏览器打开端口 http://localhost:5173/
    4. python运行v5版本文件夹下的app.py文件
### 邹黛青：更新v5 sonic_pi_sender.py 可支持复制代码进sonic pi并自动播放功能
windows需要安装AutoHotkey v2 
### 相关说明：
**1. 在midi2music文件夹内，有midi转音频的相关代码环境**

**2. music_llm_dialogue.py是与LLM对话的demo脚本，可以完成上传音频、音频=>MIDI文件、解析JSON、输入自然语言与LLM交互、获取修改音乐风格后的JSON、MIDI=>音频，可以循环对话**  
a) 注意需要使用自己的API-Key，默认使用Deepseek模型，可以自行选择模型  
b) 需要激活虚拟环境使用  
c) 优先使用music_llm_dialogue_V2.py,V1是早期版本   

**3. multiagents文件夹为目前主要demo脚本**  
a) 使用时需要参考文件夹中的README.md以及README_GUI.md文件；  
