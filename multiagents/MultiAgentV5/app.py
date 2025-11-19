#!/usr/bin/env python3
"""
Flask Backend for Sonic Pi Music Generator
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import v3
import style_transfer
from openai import OpenAI
import traceback
import threading
import queue
import time

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
MIDI_OUTPUT_DIR = Path("./midi_output")
MIDI_OUTPUT_DIR.mkdir(exist_ok=True)

# OpenAI 客户端
client = OpenAI(
    api_key='sk-7416236c6b924c9e9343c642572ed969',
    base_url="https://api.deepseek.com/v1"
)

# 存储生成任务的状态
generation_tasks = {}


class GenerationTask:
    """代表一个生成任务"""

    def __init__(self, task_id):
        self.task_id = task_id
        self.status = "pending"  # pending, running, completed, error
        self.progress = ""
        self.logs = []
        self.result_code = None
        self.midi_path = None
        self.error_message = None

    def log(self, message):
        """添加日志"""
        self.logs.append(message)

    def to_dict(self):
        """转换为字典格式"""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "progress": self.progress,
            "logs": self.logs,
            "result_code": self.result_code,
            "midi_path": self.midi_path,
            "error_message": self.error_message
        }


def log_callback(task, message):
    """日志回调函数"""
    task.log(message)


@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({"status": "ok"})


@app.route('/api/generate', methods=['POST'])
def generate_music():
    """生成音乐代码"""
    data = request.json
    prompt_text = data.get('prompt', '').strip()
    user_feedback = data.get('feedback')
    previous_code = data.get('previous_code')

    if not prompt_text:
        return jsonify({"error": "请提供音乐描述"}), 400

    # 创建任务
    task_id = f"task_{int(time.time() * 1000)}"
    task = GenerationTask(task_id)
    generation_tasks[task_id] = task

    # 在后台线程中执行生成
    def generate():
        try:
            task.status = "running"
            task.progress = "🌐 正在翻译需求..."
            task.log(f"📝 Original User Prompt:\n{prompt_text}\n")
            task.log("=" * 60)

            # 调用生成函数
            code, midi_path = v3.multi_agent_generate_sonic_pi(
                prompt_text,
                client,
                user_feedback=user_feedback,
                previous_code=previous_code,
                output_dir=str(MIDI_OUTPUT_DIR),
                log_callback=lambda msg: log_callback(task, msg)
            )

            if code:
                task.status = "completed"
                task.result_code = code
                task.midi_path = midi_path
                task.progress = "✅ 生成完成"
                task.log("\n✅ Generation completed!")
            else:
                task.status = "error"
                task.error_message = "生成失败，未获取到代码"
                task.progress = "❌ 生成失败"

        except Exception as e:
            task.status = "error"
            task.error_message = str(e)
            task.progress = f"❌ 错误: {str(e)}"
            task.log(f"\n❌ Error: {str(e)}")
            task.log(f"Traceback:\n{traceback.format_exc()}")

    thread = threading.Thread(target=generate)
    thread.daemon = True
    thread.start()

    return jsonify({"task_id": task_id}), 202


@app.route('/api/style-transfer', methods=['POST'])
def style_transfer_music():
    """风格转换"""
    data = request.json
    original_code = data.get('original_code', '').strip()
    style_request = data.get('style_request', '').strip()

    if not original_code or not style_request:
        return jsonify({"error": "请提供原始代码和风格请求"}), 400

    # 创建任务
    task_id = f"style_{int(time.time() * 1000)}"
    task = GenerationTask(task_id)
    generation_tasks[task_id] = task

    # 在后台线程中执行风格转换
    def transfer():
        try:
            task.status = "running"
            task.progress = "🎨 正在转换风格..."
            task.log(f"🎨 Starting style transfer:\nStyle Request: {style_request}\n")
            task.log("=" * 60)

            # 调用风格转换函数
            transformed_code = style_transfer.style_transfer_sonic_pi(
                original_code,
                style_request,
                client,
                log_callback=lambda msg: log_callback(task, msg)
            )

            if transformed_code:
                task.status = "completed"
                task.result_code = transformed_code
                task.progress = "✅ 风格转换完成"
                task.log("\n✅ Style transfer completed!")
            else:
                task.status = "error"
                task.error_message = "风格转换失败"
                task.progress = "❌ 风格转换失败"

        except Exception as e:
            task.status = "error"
            task.error_message = str(e)
            task.progress = f"❌ 错误: {str(e)}"
            task.log(f"\n❌ Error: {str(e)}")
            task.log(f"Traceback:\n{traceback.format_exc()}")

    thread = threading.Thread(target=transfer)
    thread.daemon = True
    thread.start()

    return jsonify({"task_id": task_id}), 202


@app.route('/api/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """获取任务状态"""
    task = generation_tasks.get(task_id)
    if not task:
        return jsonify({"error": "任务不存在"}), 404

    return jsonify(task.to_dict())


@app.route('/api/midi/<path:filename>', methods=['GET'])
def download_midi(filename):
    """下载 MIDI 文件"""
    file_path = MIDI_OUTPUT_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404

    return send_file(file_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)