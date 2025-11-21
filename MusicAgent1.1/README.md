# MusicAgent 1.1 版本存档
## 前端+后端  
这个版本目前可以稳定运行，较少bug，能实现text->music code的基本功能以及上传音频(.mp3、.wav等)->MID文件。  
### 实现功能
1. 输入对音乐的描述，经过Agent(意图理解+multi_agent)处理之后，返回一段可以直接在Sonic PI中运行的音乐代码；  
2. 上传一段音频文件，经过千问Omni理解之后，将音频返回为.json后，经过处理转换为音乐代码；  
3. 对于音乐代码，可以实现：
   （1）风格转换：在原有音色的基础上，经过agent的处理，增加/改变/删减音乐代码中的特征/乐器/频率/声调，贴近用户想要的风格；  
   （2）反馈修改：如果对生成的音乐代码效果不满意，可以使用反馈功能对原本的音乐代码进行微调，不改变该音乐代码原本的风格；  
   （3）保存为.mid文件，方便下次直接使用这个代码进行处理；  
4. 载入MIDI文件功能，可以使用历史生成的.mid文件进行处理，无须重复生成。
5. *new: 使用AutoHotkey程序，实现自动把生成的代码发送到Sonic PI并播放
6. *new: 优化前端页面
<img width="2159" height="1388" alt="95d5cb3bf58bd57b62d71158568c7f5f" src="https://github.com/user-attachments/assets/f8dafffa-5a95-480b-b91d-747e01e14bde" />


## 目前1.1版本存在的问题：  
1. 后端功能模块的运行过程还是中文（log），需要修改成英文；  
2. 后端`反馈优化模块`和`风格迁移模块`反应时间较长，并且生成的Sonic PI代码有时候会无法播放，或者有杂音，需要改进。  
     
*注：后续如有改进请另外创建不同版本（如MusicAgent 1.x），避免覆盖造成难以定位问题*  

## 环境配置方法：  
1. IDE中新建项目，创建虚拟环境；  
2. 使用requirements.txt安装package，安装时注意路径；    
3. 在app.py,gui_app.py中设置好DeepSeek的api_key，在qwen_omni_audio_to_sonicpi.py中设置千问多模态大模型——Omni声音识别的api_key（已经内置，无须再设置）；如遇到网络问题，请检查API Key是否正确设置。  

## 前端运行方法 ：
1. cd进入frontend\music-agent\dist目录  
2. 使用python的命令： python -m http.server 5173  
3. 浏览器打开端口 http://localhost:5173/  
4. python运行app.py文件  
 ## 自动化播放  
 windows需要安装AutoHotkey v2（目前在@SeanLIUXQ的Windows端无法使用，在@oDQ03o的MacOS端可以正常使用）  
 Windows11路径配置指南：  
如何把 AutoHotkey 加入 PATH，让你的系统可以在任何地方执行 AutoHotkey.exe 或 ahk.exe。  
✅ 第一步：确认 AutoHotkey 的安装目录  
C:\Program Files\AutoHotkey\v2  
里面应该有：  
AutoHotkey.exe  
AutoHotkey64.exe  
AutoHotkey32_UIA.exe等文件。  
这个路径，就是需要加到 PATH 的目录。  
  
✅ 第二步：打开 Windows 11 的 PATH 设置  
按 Win + S 打开搜索  
输入：环境变量   
点击：编辑系统环境变量  
在弹出的窗口底部，点击：环境变量…  
  
✅ 第三步：把 AutoHotkey 加入 PATH  
你现在会看到两个区域：  
上面是“用户变量”  
下面是“系统变量”   
建议放在 系统变量 的 PATH 中，让全局都能用。  

具体操作：  
在“系统变量”中找到 Path  
选中后点击右下角 编辑  
点击右侧 新建  
粘贴 AutoHotkey v2 路径：  
C:\Program Files\AutoHotkey\v2  
保存 → 保存 → 保存  

✅ 第四步：验证 AutoHotkey 是否生效  
重新打开一个新的 CMD 或 PowerShell：  
输入：  
autohotkey.exe或者AutoHotkey.exe  
如果安装正确，你会看到自动启动 AutoHotkey 或错误提示发生变化 。  
也可以测试：where autohotkey  
如果输出类似： 
C:\Program Files\AutoHotkey\v2\AutoHotkey.exe  
✔️ PATH 设置成功。  
