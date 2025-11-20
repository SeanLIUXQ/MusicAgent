#!/usr/bin/env python3
"""
Flask Backend for Sonic Pi Music Generator
音频导入功能基于 gui_app.py 的 AudioImportThread 实现
"""

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from pathlib import Path
from werkzeug.utils import secure_filename
import v3
import style_transfer
import intent_dispatcher
from openai import OpenAI
import traceback
import threading
import time
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

# 配置
MIDI_OUTPUT_DIR = Path("./midi_output")
MIDI_OUTPUT_DIR.mkdir(exist_ok=True)

# 音频上传配置
UPLOAD_FOLDER = Path("./uploads")
UPLOAD_FOLDER.mkdir(exist_ok=True)
ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg'}
MAX_AUDIO_FILE_SIZE = 50 * 1024 * 1024  # 50MB

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
        self.status = "pending"
        self.progress = ""
        self.logs = []
        self.result_code = None
        self.midi_path = None
        self.code_file_path = None
        self.error_message = None
        self.action = None
        self.music_prompt = None  # 用于音频导入时存储 Qwen 生成的音乐描述

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
            "music_prompt": self.music_prompt,
            "error_message": self.error_message
        }


def log_callback(task, message):
    """日志回调函数"""
    task.log(message)


def allowed_audio_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_AUDIO_EXTENSIONS


def save_code_file(code, midi_path=None, prefix="sonic_pi_code"):
    """保存代码文件到 midi_output 目录"""
    try:
        if midi_path:
            base_name = Path(midi_path).stem
        else:
            base_name = f"{prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        code_file = MIDI_OUTPUT_DIR / f"{base_name}.rb"

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
    user_feedback = data.get('feedback', '').strip()
    previous_code = data.get('previous_code')

    if not prompt_text and not user_feedback:
        return jsonify({"error": "请提供音乐描述"}), 400

    task_id = f"task_{int(time.time() * 1000)}"
    task = GenerationTask(task_id)
    generation_tasks[task_id] = task

    def generate():
        try:
            task.status = "running"
            task.progress = "🎯 正在通过意图理解调度器处理请求..."
            task.log(f"📝 Original User Prompt:\n{prompt_text}\n")
            task.log("=" * 60)

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

            code = dispatch_result.get('code')
            midi_path = dispatch_result.get('midi_path')
            action = dispatch_result.get('action', 'unknown')

            task.action = action
            task.log(f"\n✅ 调度完成\n执行动作: {action}\n")

            if code:
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


@app.route('/api/import-audio', methods=['POST'])
def import_audio():
    """
    从音频文件生成 Sonic Pi 代码
    完全基于 gui_app.py 的 AudioImportThread 实现
    """
    # 检查文件上传
    if 'audio_file' not in request.files:
        return jsonify({"error": "未找到音频文件"}), 400

    file = request.files['audio_file']

    if file.filename == '':
        return jsonify({"error": "未选择文件"}), 400

    if not allowed_audio_file(file.filename):
        return jsonify({
            "error": f"不支持的文件格式。支持的格式: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}"
        }), 400

    try:
        # 保存上传的文件
        filename = secure_filename(file.filename)
        timestamp = int(time.time() * 1000)
        unique_filename = f"{timestamp}_{filename}"
        file_path = UPLOAD_FOLDER / unique_filename

        # 检查文件大小
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)

        if file_size > MAX_AUDIO_FILE_SIZE:
            return jsonify({"error": f"文件大小超过限制 ({MAX_AUDIO_FILE_SIZE / 1024 / 1024:.1f}MB)"}), 400

        file.save(str(file_path))

        # 创建任务
        task_id = f"audio_{timestamp}"
        task = GenerationTask(task_id)
        task.action = "audio_import"
        generation_tasks[task_id] = task

        # 后台线程处理音频 - 完全遵循 AudioImportThread 的流程
        def process_audio():
            try:
                # === 步骤1: 使用 Qwen-Omni 分析音频 ===
                task.status = "running"
                task.progress = "🎧 正在使用 Qwen-Omni 分析音频..."
                task.log(f"[AudioImport] Input file: {file_path.name}")
                task.log(f"[AudioImport] File size: {file_size / 1024:.1f} KB")

                # 导入 Qwen-Omni 模块（与 AudioImportThread 一致）
                from qwen_omni_audio_to_sonicpi import call_qwen_audio_to_code

                # 1) 使用 Qwen-Omni 从音频生成描述和 Sonic Pi 代码
                music_prompt, sonic_code = call_qwen_audio_to_code(str(file_path))

                if not sonic_code or not sonic_code.strip():
                    task.status = "error"
                    task.error_message = "Qwen-Omni 未返回有效的 Sonic Pi 代码"
                    task.progress = "❌ 生成失败"
                    return

                # === 步骤2: 将 Sonic Pi 代码编译为 MIDI（与文本流程保持一致）===
                out_dir = MIDI_OUTPUT_DIR
                out_dir.mkdir(parents=True, exist_ok=True)
                midi_output = out_dir / f"audio_import_{timestamp}.mid"

                task.progress = "🔧 正在将 Sonic Pi 代码编译为 MIDI..."

                # 使用 v3.sonic_pi_code_to_midi（与 AudioImportThread 完全一致）
                midi_path = v3.sonic_pi_code_to_midi(
                    sonic_code,
                    str(midi_output),
                    client,
                    log_callback=lambda msg: log_callback(task, msg),
                )

                if not midi_path:
                    task.log("[AudioImport] MIDI 编译失败，将只返回 Sonic Pi 代码。")
                    midi_path_str = None
                else:
                    midi_path_str = str(midi_path)

                # === 步骤3: 记录 Qwen 生成的描述（方便后续反馈使用）===
                task.log(f"[AudioImport] Qwen 描述: {music_prompt}")

                # === 步骤4: 保存代码文件（添加注释说明来源）===
                code_with_comments = (
                    f"# Generated from audio file: {filename}\n"
                    f"# Music Description: {music_prompt}\n\n"
                    f"{sonic_code}"
                )

                code_file_path = save_code_file(
                    code_with_comments,
                    midi_path_str,
                    prefix="audio_import"
                )

                # === 完成：设置任务状态 ===
                task.status = "completed"
                task.result_code = sonic_code
                task.midi_path = midi_path_str
                task.code_file_path = code_file_path
                task.music_prompt = music_prompt  # 保存音乐描述供前端使用
                task.progress = "✅ 音频导入完成"
                task.log("\n✅ Audio import completed!")

                if code_file_path:
                    task.log(f"💾 代码已保存: {Path(code_file_path).name}")

            except ImportError as e:
                task.status = "error"
                task.error_message = "Qwen-Omni 模块未安装或导入失败"
                task.progress = "❌ 模块错误"
                task.log(f"\n❌ Import Error: {str(e)}")
                task.log("请确保 qwen_omni_audio_to_sonicpi.py 文件存在且依赖已安装")
                task.log(f"Traceback:\n{traceback.format_exc()}")

            except Exception as e:
                task.status = "error"
                task.error_message = f"音频导入失败: {str(e)}"
                task.progress = f"❌ 错误: {str(e)}"
                task.log(f"\n❌ Error: {str(e)}")
                task.log(f"Traceback:\n{traceback.format_exc()}")

            finally:
                # 删除临时上传的文件（与 AudioImportThread 异常处理一致）
                try:
                    if file_path.exists():
                        file_path.unlink()
                        task.log(f"[AudioImport] 临时文件已删除: {unique_filename}")
                except Exception as e:
                    task.log(f"[AudioImport] 删除临时文件失败: {str(e)}")

        thread = threading.Thread(target=process_audio)
        thread.daemon = True
        thread.start()

        return jsonify({
            "task_id": task_id,
            "message": "音频文件上传成功，正在处理..."
        }), 202

    except Exception as e:
        # 清理可能已保存的文件
        try:
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
        except:
            pass

        return jsonify({"error": f"文件上传失败: {str(e)}"}), 500


@app.route('/api/style-transfer', methods=['POST'])
def style_transfer_music():
    """风格转换"""
    data = request.json
    original_code = data.get('original_code', '').strip()
    style_request = data.get('style_request', '').strip()

    if not original_code or not style_request:
        return jsonify({"error": "请提供原始代码和风格请求"}), 400

    task_id = f"style_{int(time.time() * 1000)}"
    task = GenerationTask(task_id)
    generation_tasks[task_id] = task

    def transfer():
        try:
            task.status = "running"
            task.progress = "🎨 正在转换风格..."
            task.log(f"🎨 Starting style transfer:\nStyle Request: {style_request}\n")
            task.log("=" * 60)

            transformed_code = style_transfer.style_transfer_sonic_pi(
                original_code,
                style_request,
                client,
                log_callback=lambda msg: log_callback(task, msg)
            )

            if transformed_code:
                code_file_path = save_code_file(transformed_code, prefix="style_transfer")

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
        rb_files = sorted(
            MIDI_OUTPUT_DIR.glob("*.rb"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
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

        if not file_path.resolve().is_relative_to(MIDI_OUTPUT_DIR.resolve()):
            return jsonify({"error": "非法的文件路径"}), 400

        if not file_path.exists() or not file_path.suffix == '.rb':
            return jsonify({"error": "文件不存在或不是 .rb 文件"}), 404

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

        if not file_path.resolve().is_relative_to(MIDI_OUTPUT_DIR.resolve()):
            return jsonify({"error": "非法的文件路径"}), 400

        if not file_path.exists() or not file_path.suffix == '.rb':
            return jsonify({"error": "文件不存在或不是 .rb 文件"}), 404

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

    if not file_path.resolve().is_relative_to(MIDI_OUTPUT_DIR.resolve()):
        return jsonify({"error": "非法的文件路径"}), 400

    if not file_path.exists():
        return jsonify({"error": "文件不存在"}), 404

    return send_file(file_path, as_attachment=True, mimetype='text/plain')


if __name__ == '__main__':
    print("🎵 Sonic Pi Music Generator Backend")
    print(f"📁 MIDI Output Directory: {MIDI_OUTPUT_DIR.absolute()}")
    print(f"📁 Upload Directory: {UPLOAD_FOLDER.absolute()}")
    print(f"🎧 Supported Audio Formats: {', '.join(ALLOWED_AUDIO_EXTENSIONS)}")
    print(f"📏 Max Audio File Size: {MAX_AUDIO_FILE_SIZE / 1024 / 1024:.1f}MB")
    print("=" * 60)
    print("Audio Import Flow (based on AudioImportThread):")
    print("1. Upload audio file")
    print("2. Call Qwen-Omni: call_qwen_audio_to_code()")
    print("3. Compile to MIDI: v3.sonic_pi_code_to_midi()")
    print("4. Save code file with comments")
    print("5. Return: music_prompt, code, midi_path")
    print("=" * 60)
    print("🚀 Starting server on http://0.0.0.0:5001")
    app.run(debug=True, host='0.0.0.0', port=5001)