
# V3版本图形化界面：
<img width="1102" height="966" alt="image" src="https://github.com/user-attachments/assets/31207576-7070-4d33-9d2e-cea637cb31d4" />  


# V3版本避免在生成 Sonic Pi 代码时使用内置函数名（如 chord）作为变量名：  
## 主要修改  
1. 创建保留字列表 (v3.py)  
(1) 添加 SONIC_PI_RESERVED_WORDS 集合，包含常见内置函数和保留字  
(2) 包含 chord、scale、play、sample、amp、pan、rate 等  
2. 添加命名约束函数 (v3.py)  
get_sonic_pi_naming_constraints() 生成命名约束说明  
提供常见保留字的替代方案（如 chord -> chord_notes 或 chord_progression）  
3. 添加后处理函数 (v3.py)  
fix_reserved_word_variables() 检测并修复变量名冲突  
仅处理明显的变量赋值，避免误替换函数调用  
4. 更新代码生成提示 (v3.py)  
Composer：在提示中加入命名约束  
Critic：增加变量名冲突检查  
Arranger：确保最终代码遵循命名规则  
5. 在代码提取后应用后处理   
更新风格转换模块 (style_transfer.py)  
在风格转换的智能体中应用相同的命名约束  
6. 添加后处理步骤    
工作原理  
预防：在生成阶段，通过提示引导模型避免使用保留字作为变量名
检查：Critic 阶段检查变量名冲突
修复：Arranger 阶段替换冲突变量名
后处理：代码提取后进行最后检查与修复  
## 变量名替换规则  
### 常见替换示例：  
'''  
chord → chord_notes 或 chord_progression  
scale → scale_pattern 或 scale_notes  
amp → amplitude 或 my_amp  
pan → panning 或 my_pan  
rate → playback_rate 或 sample_rate  
'''  
### 使用效果
生成 Sonic Pi 代码时：  
1. 避免使用 chord 等保留字作为变量名  
2. 自动使用安全的替代名称  
3. 如有遗漏，后处理会修复  
