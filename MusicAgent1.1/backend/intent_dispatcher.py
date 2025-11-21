#!/usr/bin/env python3
"""
意图理解调度器 - 使用通义千问意图理解模型作为调度中心
根据用户意图和工具调用信息，直接调用相应的功能模块

适配版本：v4\backend
修改内容：将v2模块调用改为v3模块调用
"""

import os
import re
import json
from typing import Dict, List, Optional, Tuple, Any
from openai import OpenAI

# 默认API Key（直接嵌入代码中）
DEFAULT_DASHSCOPE_API_KEY = "sk-8ca89d814baa4ff689199c0f6e41571e"


def parse_intent_response(text: str) -> Dict:
    """
    解析意图理解模型的响应
    
    Args:
        text: 模型返回的文本
    
    Returns:
        包含tags、tool_call和content的字典
    """
    # 定义正则表达式模式来匹配 <tags>, <tool_call>, <content> 及其内容
    tags_pattern = r'<tags>(.*?)</tags>'
    tool_call_pattern = r'<tool_call>(.*?)</tool_call>'
    content_pattern = r'<content>(.*?)</content>'
    
    # 使用正则表达式查找匹配的内容
    tags_match = re.search(tags_pattern, text, re.DOTALL)
    tool_call_match = re.search(tool_call_pattern, text, re.DOTALL)
    content_match = re.search(content_pattern, text, re.DOTALL)
    
    # 提取匹配的内容，如果没有匹配到则返回空字符串
    tags = tags_match.group(1).strip() if tags_match else ""
    tool_call_str = tool_call_match.group(1).strip() if tool_call_match else ""
    content = content_match.group(1).strip() if content_match else ""
    
    # 解析tool_call JSON
    tool_calls = []
    if tool_call_str:
        try:
            tool_call_list = json.loads(tool_call_str)
            if isinstance(tool_call_list, list):
                tool_calls = tool_call_list
            else:
                tool_calls = [tool_call_list]
        except json.JSONDecodeError:
            # 如果解析失败，尝试解析为单个对象
            try:
                tool_calls = [json.loads(tool_call_str)]
            except:
                tool_calls = []
    
    # 将提取的内容存储在字典中
    result = {
        "tags": tags,
        "tool_call": tool_calls,
        "content": content
    }
    
    return result


def get_music_tools() -> List[Dict]:
    """
    定义音乐生成相关的工具列表
    
    Returns:
        工具列表
    """
    tools = [
        {
            "name": "generate_music",
            "description": "当用户想要生成新的音乐时使用此工具。包括创建新的音乐作品、生成Sonic Pi代码等。这是最常用的功能。",
            "parameters": {
                "type": "object",
                "properties": {
                    "description": {
                        "type": "string",
                        "description": "音乐描述，包含风格、节奏、调性、情绪等信息。这是用户输入的原始描述或提取的关键信息。",
                        "default": ""
                    },
                    "style": {
                        "type": "string",
                        "description": "音乐风格，如：钢琴独奏、电子音乐、爵士乐、摇滚、古典、流行等。",
                        "default": ""
                    },
                    "tempo": {
                        "type": "string",
                        "description": "节奏速度，如：慢速、中速、快速，或具体的BPM值。",
                        "default": ""
                    },
                    "key": {
                        "type": "string",
                        "description": "调性，如：C大调、A小调等。",
                        "default": ""
                    },
                    "mood": {
                        "type": "string",
                        "description": "情绪或氛围，如：平静、梦幻、欢快、悲伤、激昂等。",
                        "default": ""
                    },
                    "instruments": {
                        "type": "string",
                        "description": "乐器描述，如：钢琴、吉他、鼓、合成器等。",
                        "default": ""
                    }
                },
                "required": ["description"]
            }
        },
        {
            "name": "style_transfer",
            "description": "当用户想要转换已有音乐的风格时使用此工具。如将现有音乐转换为摇滚风格、爵士风格等。注意：这需要已经生成过音乐代码。",
            "parameters": {
                "type": "object",
                "properties": {
                    "target_style": {
                        "type": "string",
                        "description": "目标风格，如：摇滚、爵士、轻柔、电子、古典等。",
                        "default": ""
                    },
                    "original_style": {
                        "type": "string",
                        "description": "原始风格描述（如果有）。",
                        "default": ""
                    },
                    "style_request": {
                        "type": "string",
                        "description": "完整的风格转换请求，包含目标风格和任何特殊要求。",
                        "default": ""
                    }
                },
                "required": ["target_style"]
            }
        },
        {
            "name": "modify_music",
            "description": "当用户想要修改已有音乐时使用此工具。包括调整速度、音调、音量、添加反馈等。注意：这通常需要结合generate_music工具，使用user_feedback参数。",
            "parameters": {
                "type": "object",
                "properties": {
                    "modification_type": {
                        "type": "string",
                        "description": "修改类型，如：调整速度、改变音调、修改音量、添加反馈等。",
                        "default": ""
                    },
                    "feedback": {
                        "type": "string",
                        "description": "修改的详细反馈描述。",
                        "default": ""
                    },
                    "details": {
                        "type": "string",
                        "description": "修改的详细描述。",
                        "default": ""
                    }
                },
                "required": ["modification_type"]
            }
        }
    ]
    return tools


def call_intent_model(user_input: str, api_key: Optional[str] = None, log_callback=None) -> Dict:
    """
    调用通义千问意图理解模型进行意图检测
    
    Args:
        user_input: 用户输入的文本
        api_key: DashScope API Key，如果为None则使用默认值
        log_callback: 可选的日志回调函数
    
    Returns:
        包含意图和工具调用信息的字典
    """
    def log(message):
        """日志输出"""
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    # 获取API Key
    if api_key is None:
        api_key = os.getenv("DASHSCOPE_API_KEY", DEFAULT_DASHSCOPE_API_KEY)
    
    try:
        # 初始化DashScope客户端
        client = OpenAI(
            api_key=api_key,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 获取工具定义
        tools = get_music_tools()
        tools_string = json.dumps(tools, ensure_ascii=False)
        
        # 构建System Message
        system_prompt = f"""You are Qwen, created by Alibaba Cloud. You are a helpful assistant. You may call one or more tools to assist with the user query. The tools you can use are as follows:

{tools_string}

Response in INTENT_MODE."""
        
        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': user_input}
        ]
        
        log("🔍 正在调用意图理解模型...")
        
        # 调用意图理解模型
        response = client.chat.completions.create(
            model="tongyi-intent-detect-v3",
            messages=messages
        )
        
        response_text = response.choices[0].message.content
        
        # 解析响应
        parsed_result = parse_intent_response(response_text)
        
        log(f"✅ 意图理解完成\n意图标签: {parsed_result['tags']}\n工具调用: {json.dumps(parsed_result['tool_call'], ensure_ascii=False, indent=2)}\n内容: {parsed_result['content']}\n")
        
        return parsed_result
        
    except Exception as e:
        log(f"❌ 意图理解失败: {str(e)}\n将尝试根据输入内容推断意图。\n")
        # 出错时返回空结果，让调度器根据输入推断
        return {
            "tags": "[intent detection failed]",
            "tool_call": [],
            "content": ""
        }


def dispatch_to_generate_music(arguments: Dict, client, output_dir: str, log_callback=None) -> Tuple[Optional[str], Optional[str]]:
    """
    调度到音乐生成功能
    
    Args:
        arguments: 工具调用参数
        client: OpenAI客户端
        output_dir: 输出目录
        log_callback: 日志回调
    
    Returns:
        (code, midi_path) 元组
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    try:
        # 构建音乐描述
        description = arguments.get('description', '')
        style = arguments.get('style', '')
        tempo = arguments.get('tempo', '')
        key = arguments.get('key', '')
        mood = arguments.get('mood', '')
        instruments = arguments.get('instruments', '')
        
        # 如果没有description但有其他参数，构建描述
        if not description and any([style, tempo, key, mood, instruments]):
            parts = []
            if style:
                parts.append(f"风格: {style}")
            if tempo:
                parts.append(f"节奏: {tempo}")
            if key:
                parts.append(f"调性: {key}")
            if mood:
                parts.append(f"情绪: {mood}")
            if instruments:
                parts.append(f"乐器: {instruments}")
            description = "，".join(parts)
        
        # 如果仍然没有描述，返回错误
        if not description:
            log("❌ 错误: 缺少音乐描述，无法生成音乐")
            return None, None
        
        log(f"🎵 调用音乐生成功能\n描述: {description}\n")
        log(f"📁 输出目录: {output_dir}\n")
        
        # 导入v3模块 (v4\backend使用v3)
        import v3
        
        # 调用音乐生成函数
        log("🔄 开始调用 v3.multi_agent_generate_sonic_pi...\n")
        code, midi_path = v3.multi_agent_generate_sonic_pi(
            description,
            client,
            user_feedback=None,
            previous_code=None,
            output_dir=output_dir,
            log_callback=log_callback
        )
        log(f"✅ v3.multi_agent_generate_sonic_pi 返回: code={'已生成' if code else 'None'}, midi_path={midi_path or 'None'}\n")
        # 自动把生成的 Sonic Pi 代码发给 Sonic Pi 播放
        if code:
            log("📡 尝试将生成的 Sonic Pi 代码发送到 Sonic Pi...\n")
            try:
                from sonic_pi_sender import send_code_to_sonic_pi
                send_code_to_sonic_pi(code, log_callback=log_callback)
            except Exception as e:
                log(f"⚠️ 发送到 Sonic Pi 时出现异常（不影响 MIDI 生成）: {e}\n")
        
        return code, midi_path
        
    except Exception as e:
        log(f"❌ 音乐生成失败: {str(e)}\n")
        import traceback
        log(f"Traceback:\n{traceback.format_exc()}\n")
        return None, None


def dispatch_to_style_transfer(arguments: Dict, original_code: str, client, log_callback=None) -> Optional[str]:
    """
    调度到风格转换功能
    
    Args:
        arguments: 工具调用参数
        original_code: 原始代码
        client: OpenAI客户端
        log_callback: 日志回调
    
    Returns:
        转换后的代码
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    try:
        target_style = arguments.get('target_style', '')
        style_request = arguments.get('style_request', '')
        
        # 如果没有style_request但有target_style，构建请求
        if not style_request and target_style:
            style_request = f"转换为{target_style}风格"
        
        if not style_request:
            log("❌ 错误: 缺少风格转换请求，无法转换")
            return None
        
        if not original_code:
            log("❌ 错误: 缺少原始代码，无法进行风格转换")
            return None
        
        log(f"🎨 调用风格转换功能\n目标风格: {target_style}\n请求: {style_request}\n")
        
        # 导入style_transfer模块
        import style_transfer
        
        # 调用风格转换函数
        transformed_code = style_transfer.style_transfer_sonic_pi(
            original_code,
            style_request,
            client,
            log_callback=log_callback
        )
        
        return transformed_code
        
    except Exception as e:
        log(f"❌ 风格转换失败: {str(e)}\n")
        import traceback
        log(f"Traceback:\n{traceback.format_exc()}\n")
        return None


def dispatch_intent(user_input: str, client, original_code: Optional[str] = None, 
                   user_feedback: Optional[str] = None, previous_code: Optional[str] = None,
                   output_dir: str = ".", api_key: Optional[str] = None, log_callback=None) -> Dict[str, Any]:
    """
    意图理解调度器 - 根据用户输入调用相应的功能模块
    
    Args:
        user_input: 用户输入的文本
        client: OpenAI客户端（用于后续功能调用）
        original_code: 已有的代码（用于风格转换或修改）
        user_feedback: 用户反馈（用于修改音乐）
        previous_code: 之前的代码（用于迭代改进）
        output_dir: 输出目录
        api_key: DashScope API Key（用于意图理解模型）
        log_callback: 日志回调函数
    
    Returns:
        包含执行结果的字典:
        {
            "action": "generate_music" | "style_transfer" | "modify_music" | "unknown",
            "code": 生成的代码（如果有）,
            "midi_path": MIDI文件路径（如果有）,
            "intent_result": 意图理解结果
        }
    """
    def log(message):
        if log_callback:
            log_callback(message)
        else:
            print(message)
    
    log("\n" + "=" * 60 + "\n")
    log("🎯 意图理解调度器启动\n")
    log(f"用户输入: {user_input}\n")
    log("=" * 60 + "\n")
    
    # Step 1: 调用意图理解模型
    intent_result = call_intent_model(user_input, api_key=api_key, log_callback=log_callback)
    
    # Step 2: 根据工具调用调度到相应功能
    tool_calls = intent_result.get('tool_call', [])
    
    if not tool_calls:
        # 如果没有工具调用，尝试根据输入推断意图
        log("⚠️ 未检测到工具调用，尝试根据输入内容推断意图...\n")
        
        # 检查是否是风格转换请求
        style_keywords = ['转换', '改成', '变成', '改为', '风格', '转换为']
        if any(keyword in user_input for keyword in style_keywords) and original_code:
            log("🔍 推断为风格转换请求\n")
            return {
                "action": "style_transfer",
                "code": dispatch_to_style_transfer(
                    {"target_style": user_input, "style_request": user_input},
                    original_code,
                    client,
                    log_callback
                ),
                "midi_path": None,
                "intent_result": intent_result
            }
        
        # 检查是否是修改/反馈请求
        feedback_keywords = ['修改', '调整', '改进', '反馈', '更快', '更慢', '更高', '更低']
        if any(keyword in user_input for keyword in feedback_keywords) and previous_code:
            log("🔍 推断为修改/反馈请求\n")
            # 使用反馈机制重新生成 (使用v3模块)
            import v3
            code, midi_path = v3.multi_agent_generate_sonic_pi(
                user_input,
                client,
                user_feedback=user_feedback or user_input,
                previous_code=previous_code,
                output_dir=output_dir,
                log_callback=log_callback
            )
            return {
                "action": "modify_music",
                "code": code,
                "midi_path": midi_path,
                "intent_result": intent_result
            }
        
        # 默认推断为生成新音乐
        log("🔍 推断为生成新音乐请求\n")
        code, midi_path = dispatch_to_generate_music(
            {"description": user_input},
            client,
            output_dir,
            log_callback
        )
        return {
            "action": "generate_music",
            "code": code,
            "midi_path": midi_path,
            "intent_result": intent_result
        }
    
    # 处理工具调用
    result_code = None
    result_midi_path = None
    actions = []
    
    for tool_call in tool_calls:
        tool_name = tool_call.get('name', '')
        arguments = tool_call.get('arguments', {})
        
        log(f"\n🔧 执行工具调用: {tool_name}\n参数: {json.dumps(arguments, ensure_ascii=False, indent=2)}\n")
        
        if tool_name == "generate_music":
            actions.append("generate_music")
            # 如果没有description但有其他参数，从user_input中提取
            if 'description' not in arguments or not arguments['description']:
                arguments['description'] = user_input
            
            code, midi_path = dispatch_to_generate_music(
                arguments,
                client,
                output_dir,
                log_callback
            )
            result_code = code or result_code
            result_midi_path = midi_path or result_midi_path
            
        elif tool_name == "style_transfer":
            actions.append("style_transfer")
            if not original_code:
                log("⚠️ 警告: 风格转换需要已有代码，但未提供original_code\n")
                continue
            
            # 如果没有style_request，从target_style构建
            if 'style_request' not in arguments or not arguments['style_request']:
                target_style = arguments.get('target_style', user_input)
                arguments['style_request'] = f"转换为{target_style}风格" if target_style else user_input
            
            code = dispatch_to_style_transfer(
                arguments,
                original_code,
                client,
                log_callback
            )
            result_code = code or result_code
            
        elif tool_name == "modify_music":
            actions.append("modify_music")
            # 使用反馈机制重新生成 (使用v3模块)
            feedback = arguments.get('feedback') or arguments.get('details') or user_input
            import v3
            code, midi_path = v3.multi_agent_generate_sonic_pi(
                user_input,
                client,
                user_feedback=feedback,
                previous_code=previous_code,
                output_dir=output_dir,
                log_callback=log_callback
            )
            result_code = code or result_code
            result_midi_path = midi_path or result_midi_path
            
        else:
            log(f"⚠️ 警告: 未知的工具调用: {tool_name}\n")
    
    # 确定主要动作
    if actions:
        main_action = actions[0]  # 使用第一个动作作为主要动作
    else:
        main_action = "unknown"
    
    log("\n" + "=" * 60 + "\n")
    log(f"✅ 调度完成\n主要动作: {main_action}\n")
    log("=" * 60 + "\n")
    
    return {
        "action": main_action,
        "code": result_code,
        "midi_path": result_midi_path,
        "intent_result": intent_result
    }
