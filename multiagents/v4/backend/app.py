#!/usr/bin/env python3
"""
Flask Backend for Sonic Pi Music Generator
Updated with history file management features
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
import v3
import style_transfer
import intent_dispatcher
from openai import OpenAI
import traceback
import threading
import time
from datetime import datetime

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 配置
MIDI_OUTPUT_DIR = Path("./midi_output")
MIDI_OUTPUT_DIR.mkdir(exist_ok=True)

# OpenAI 客户端
client = OpenAI(
    api_key='sk-78ac4fe101aa495091ff83198ac47c3a',
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
        self.code_file_path = None
        self.error_message = None
        self.action = None

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
            "code_file_path": self.code_file_path,
            "action": self.action,
            "error_message": self.error_message
        }


def log_callback(task, message):
    """日志回调函数"""
    task.log(message)


def save_code_file(code, midi_path=None):
    """保存代码文件到 midi_output 目录"""
    try:
        # 生成文件名(与 MIDI 文件同名或使用时间戳)
        if midi_path:
            base_name = Path(midi_path).stem
        else:
            base_name = f"sonic_pi_code_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        code_file = MIDI_OUTPUT_DIR / f"{base_name}.rb"

        # 保存代码
        with open(code_file, "w", encoding="utf-8") as f:
            f.write(code)

        return str(code_file)
    except Exception as e:
        print(f"保存代码文件失败: {str(e)}")
        return None


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
            task.progress = "🎯 正在通过意图理解调度器处理请求..."
            task.log(f"📝 Original User Prompt:\n{prompt_text}\n")
            task.log("=" * 60)

            # 使用意图理解调度器
            dispatch_result = intent_dispatcher.dispatch_intent(
                user_input=prompt_text,
                client=client,
                original_code=previous_code,
                user_feedback=user_feedback,
                previous_code=previous_code,
                output_dir=str(MIDI_OUTPUT_DIR),
                api_key=None,
                log_callback=lambda msg: log_callback(task, msg)
            )

            # 获取调度结果
            code = dispatch_result.get('code')
            midi_path = dispatch_result.get('midi_path')
            action = dispatch_result.get('action', 'unknown')

            task.action = action
            task.log(f"\n✅ 调度完成\n执行动作: {action}\n")

            if code:
                # 保存代码文件
                code_file_path = save_code_file(code, midi_path)

                task.status = "completed"
                task.result_code = code
                task.midi_path = midi_path
                task.code_file_path = code_file_path
                task.progress = "✅ 生成完成"

                if code_file_path:
                    task.log(f"\n💾 代码已保存: {Path(code_file_path).name}")

                if midi_path:
                    task.log(f"\n✅ Generation completed! MIDI file: {midi_path}")
                else:
                    task.log("\n⚠️ Generation completed but MIDI compilation failed.")
            else:
                task.status = "error"
                task.error_message = "生成失败,未获取到代码"
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
                # 保存转换后的代码文件
                code_file_path = save_code_file(transformed_code)

                task.status = "completed"
                task.result_code = transformed_code
                task.code_file_path = code_file_path
                task.action = "style_transfer"
                task.progress = "✅ 风格转换完成"
                task.log("\n✅ Style transfer completed!")

                if code_file_path:
                    task.log(f"💾 代码已保存: {Path(code_file_path).name}")
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


@app.route('/api/history', methods=['GET'])
def get_history_files():
    """获取历史文件列表"""
    try:
        # 获取所有 .rb 文件
        rb_files = sorted(
            MIDI_OUTPUT_DIR.glob("*.rb"),
            key=lambda x: x.stat().st_mtime,
            reverse=True  # 最新的在前面
        )

        history_list = []
        for rb_file in rb_files:
            mtime = datetime.fromtimestamp(rb_file.stat().st_mtime)
            history_list.append({
                "filename": rb_file.name,
                "display_name": f"{rb_file.stem} ({mtime.strftime('%Y-%m-%d %H:%M')})",
                "modified_time": mtime.isoformat(),
                "size": rb_file.stat().st_size
            })

        return jsonify({
            "files": history_list,
            "count": len(history_list)
        })

    except Exception as e:
        return jsonify({"error": f"获取历史文件失败: {str(e)}"}), 500


@app.route('/api/history/<filename>', methods=['GET'])
def get_history_file(filename):
    """获取指定历史文件的内容"""
    try:
        file_path = MIDI_OUTPUT_DIR / filename

        # 安全检查:确保文件在 MIDI_OUTPUT_DIR 内
        if not file_path.resolve().is_relative_to(MIDI_OUTPUT_DIR.resolve()):
            return jsonify({"error": "非法的文件路径"}), 400

        if not file_path.exists() or not file_path.suffix == '.rb':
            return jsonify({"error": "文件不存在或不是 .rb 文件"}), 404

        # 读取文件内容
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        return jsonify({
            "filename": filename,
            "code": code,
            "modified_time": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
        })

    except Exception as e:
        return jsonify({"error": f"读取文件失败: {str(e)}"}), 500


@app.route('/api/history/<filename>', methods=['DELETE'])
def delete_history_file(filename):
    """删除指定的历史文件"""
    try:
        file_path = MIDI_OUTPUT_DIR / filename

        # 安全检查:确保文件在 MIDI_OUTPUT_DIR 内
        if not file_path.resolve().is_relative_to(MIDI_OUTPUT_DIR.resolve()):
            return jsonify({"error": "非法的文件路径"}), 400

        if not file_path.exists() or not file_path.suffix == '.rb':
            return jsonify({"error": "文件不存在或不是 .rb 文件"}), 404

        # 删除文件
        file_path.unlink()

        return jsonify({
            "success": True,
            "message": f"文件 {filename} 已删除"
        })

    except Exception as e:
        return jsonify({"error": f"删除文件失败: {str(e)}"}), 500


@app.route('/api/midi/<path:filename>', methods=['GET'])
def download_midi(filename):
    """下载 MIDI 文件"""
    file_path = MIDI_OUTPUT_DIR / filename
    if not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404

    return send_file(file_path, as_attachment=True)


@app.route('/api/code/<path:filename>', methods=['GET'])
def download_code(filename):
    """下载代码文件"""
    file_path = MIDI_OUTPUT_DIR / filename

    # 安全检查
    if not file_path.resolve().is_relative_to(MIDI_OUTPUT_DIR.resolve()):
        return jsonify({"error": "非法的文件路径"}), 400

    if not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404

    return send_file(file_path, as_attachment=True, mimetype='text/plain')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)