#!/usr/bin/env python3
"""MusicAgent browser-native API."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from flask import Flask, jsonify, request, send_file, send_from_directory
from werkzeug.utils import secure_filename

from music_engine import (
    composition_to_midi,
    generate_composition,
    midi_to_composition,
    save_composition,
    transform_style,
    validate_composition,
)

try:
    from openai import OpenAI
except ImportError:  # The built-in generator remains available without the SDK.
    OpenAI = None


BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIST = BASE_DIR.parent / "frontend" / "dist"
OUTPUT_DIR = BASE_DIR / "music_output"
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
TASK_TTL_SECONDS = int(os.getenv("MUSICAGENT_TASK_TTL", "3600"))
TASK_CAPACITY = int(os.getenv("MUSICAGENT_TASK_CAPACITY", "100"))

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES
executor = ThreadPoolExecutor(max_workers=int(os.getenv("MUSICAGENT_WORKERS", "4")))


def _is_allowed_origin(origin: str) -> bool:
    if not origin:
        return False
    parsed = urlparse(origin)
    return parsed.scheme in {"http", "https"} and parsed.hostname in {"localhost", "127.0.0.1", "::1"}


@app.after_request
def add_cors_headers(response):
    origin = request.headers.get("Origin", "")
    if _is_allowed_origin(origin):
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Vary"] = "Origin"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, DELETE, OPTIONS"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


def _create_client():
    key = os.getenv("DEEPSEEK_API_KEY", "").strip()
    if not key or OpenAI is None:
        return None
    return OpenAI(
        api_key=key,
        base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1"),
        timeout=float(os.getenv("DEEPSEEK_TIMEOUT", "90")),
        max_retries=2,
    )


client = _create_client()


class GenerationTask:
    def __init__(self, action: str):
        self.task_id = f"{action}_{uuid.uuid4().hex}"
        self.created_at = time.time()
        self.updated_at = self.created_at
        self.status = "pending"
        self.progress = "Queued"
        self.logs: list[str] = []
        self.result_composition: dict[str, Any] | None = None
        self.midi_filename: str | None = None
        self.composition_filename: str | None = None
        self.error_message: str | None = None
        self.action = action
        self._lock = threading.RLock()

    def update(self, **values: Any) -> None:
        with self._lock:
            for key, value in values.items():
                setattr(self, key, value)
            self.updated_at = time.time()

    def log(self, message: str) -> None:
        with self._lock:
            self.logs.append(str(message))
            self.logs = self.logs[-300:]
            self.updated_at = time.time()

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "task_id": self.task_id,
                "status": self.status,
                "progress": self.progress,
                "logs": list(self.logs),
                "result_composition": self.result_composition,
                "midi_filename": self.midi_filename,
                "composition_filename": self.composition_filename,
                "action": self.action,
                "error_message": self.error_message,
                "created_at": datetime.fromtimestamp(self.created_at, timezone.utc).isoformat(),
            }


class TaskStore:
    def __init__(self, capacity: int, ttl_seconds: int):
        self.capacity = max(10, capacity)
        self.ttl_seconds = max(60, ttl_seconds)
        self._tasks: OrderedDict[str, GenerationTask] = OrderedDict()
        self._lock = threading.RLock()

    def _cleanup(self) -> None:
        cutoff = time.time() - self.ttl_seconds
        expired = [key for key, value in self._tasks.items() if value.updated_at < cutoff]
        for key in expired:
            self._tasks.pop(key, None)
        while len(self._tasks) > self.capacity:
            self._tasks.popitem(last=False)

    def add(self, task: GenerationTask) -> None:
        with self._lock:
            self._cleanup()
            self._tasks[task.task_id] = task
            self._tasks.move_to_end(task.task_id)
            self._cleanup()

    def get(self, task_id: str) -> GenerationTask | None:
        with self._lock:
            self._cleanup()
            task = self._tasks.get(task_id)
            if task:
                self._tasks.move_to_end(task_id)
            return task


tasks = TaskStore(TASK_CAPACITY, TASK_TTL_SECONDS)


def _json_body() -> dict[str, Any]:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValueError("request body must be a JSON object")
    return data


def _unique_stem(prefix: str) -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S_%fZ")
    return f"{prefix}_{timestamp}_{uuid.uuid4().hex[:8]}"


def _persist(composition: dict[str, Any], prefix: str) -> tuple[str, str]:
    stem = _unique_stem(prefix)
    composition_path = OUTPUT_DIR / f"{stem}.json"
    midi_path = OUTPUT_DIR / f"{stem}.mid"
    save_composition(composition, composition_path)
    composition_to_midi(composition, midi_path)
    return composition_path.name, midi_path.name


def _run_task(task: GenerationTask, work: Callable[[], dict[str, Any]], prefix: str) -> None:
    try:
        task.update(status="running", progress="Building arrangement")
        composition = validate_composition(work())
        task.update(progress="Exporting MIDI")
        composition_filename, midi_filename = _persist(composition, prefix)
        task.log(f"Created {len(composition['tracks'])} tracks at {composition['tempo']} BPM.")
        task.update(
            status="completed",
            progress="Ready to play",
            result_composition=composition,
            composition_filename=composition_filename,
            midi_filename=midi_filename,
        )
    except Exception as exc:
        task.log(f"Generation failed: {exc}")
        task.update(status="error", progress="Generation failed", error_message=str(exc))


def _submit(action: str, prefix: str, work: Callable[[GenerationTask], dict[str, Any]]):
    task = GenerationTask(action)
    tasks.add(task)
    executor.submit(_run_task, task, lambda: work(task), prefix)
    return jsonify({"task_id": task.task_id}), 202


def _safe_output_file(filename: str, suffixes: set[str]) -> Path | None:
    safe_name = Path(filename).name
    if safe_name != filename or Path(safe_name).suffix.lower() not in suffixes:
        return None
    candidate = (OUTPUT_DIR / safe_name).resolve()
    try:
        candidate.relative_to(OUTPUT_DIR.resolve())
    except ValueError:
        return None
    return candidate


@app.errorhandler(413)
def too_large(_error):
    return jsonify({"error": "file exceeds the 50 MB upload limit"}), 413


@app.route("/api/health", methods=["GET"])
def health_check():
    return jsonify({"status": "ok", "engine": "browser-native", "ai_enabled": client is not None})


@app.route("/api/generate", methods=["POST"])
def generate_music():
    try:
        data = _json_body()
        prompt = str(data.get("prompt", "")).strip()
        feedback = str(data.get("feedback", "")).strip()
        previous_raw = data.get("previous_composition")
        previous = validate_composition(previous_raw) if previous_raw is not None else None
        if not prompt and not feedback:
            return jsonify({"error": "provide a music description or feedback"}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    def work(task: GenerationTask):
        task.log("Creating a structured, browser-playable composition.")
        return generate_composition(prompt, client, feedback, previous, task.log)

    return _submit("generate", "composition", work)


@app.route("/api/arrange", methods=["POST"])
@app.route("/api/style-transfer", methods=["POST"])
def arrange_music():
    try:
        data = _json_body()
        composition = validate_composition(data.get("composition") or data.get("original_composition"))
        style_request = str(data.get("style_request", "")).strip()
        if not style_request:
            return jsonify({"error": "provide an arrangement or style request"}), 400
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400

    def work(task: GenerationTask):
        task.log(f"Applying arrangement direction: {style_request}")
        return transform_style(composition, style_request, client, task.log)

    return _submit("arrange", "arrangement", work)


@app.route("/api/import-midi", methods=["POST"])
def import_midi():
    upload = request.files.get("midi_file")
    if upload is None or not upload.filename:
        return jsonify({"error": "select a MIDI file"}), 400
    filename = secure_filename(upload.filename)
    if Path(filename).suffix.lower() not in {".mid", ".midi"}:
        return jsonify({"error": "only .mid and .midi files are supported"}), 400
    temporary = UPLOAD_DIR / f"{uuid.uuid4().hex}_{filename}"
    upload.save(temporary)

    def work(task: GenerationTask):
        try:
            task.log(f"Importing {filename} into editable tracks.")
            return midi_to_composition(temporary)
        finally:
            temporary.unlink(missing_ok=True)

    return _submit("import", "import", work)


@app.route("/api/export-midi", methods=["POST"])
def export_midi():
    try:
        composition = validate_composition(_json_body().get("composition"))
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    path = OUTPUT_DIR / f"{_unique_stem('export')}.mid"
    composition_to_midi(composition, path)
    return send_file(path, as_attachment=True, download_name=f"{secure_filename(composition['title']) or 'composition'}.mid")


@app.route("/api/task/<task_id>", methods=["GET"])
def get_task_status(task_id: str):
    task = tasks.get(task_id)
    if task is None:
        return jsonify({"error": "task not found or expired"}), 404
    return jsonify(task.snapshot())


@app.route("/api/history", methods=["GET"])
def get_history_files():
    files = sorted(OUTPUT_DIR.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return jsonify(
        {
            "files": [
                {
                    "filename": path.name,
                    "display_name": path.stem,
                    "modified_time": datetime.fromtimestamp(path.stat().st_mtime, timezone.utc).isoformat(),
                    "size": path.stat().st_size,
                }
                for path in files
            ],
            "count": len(files),
        }
    )


@app.route("/api/history/<filename>", methods=["GET"])
def get_history_file(filename: str):
    path = _safe_output_file(filename, {".json"})
    if path is None:
        return jsonify({"error": "invalid composition filename"}), 400
    if not path.is_file():
        return jsonify({"error": "composition not found"}), 404
    try:
        composition = validate_composition(json.loads(path.read_text(encoding="utf-8")))
    except (ValueError, json.JSONDecodeError) as exc:
        return jsonify({"error": f"invalid composition file: {exc}"}), 422
    return jsonify({"filename": path.name, "composition": composition})


@app.route("/api/history/<filename>", methods=["DELETE"])
def delete_history_file(filename: str):
    path = _safe_output_file(filename, {".json"})
    if path is None:
        return jsonify({"error": "invalid composition filename"}), 400
    if not path.is_file():
        return jsonify({"error": "composition not found"}), 404
    path.unlink()
    matching_midi = path.with_suffix(".mid")
    if matching_midi.is_file():
        matching_midi.unlink()
    return jsonify({"success": True, "message": f"Deleted {path.name}"})


@app.route("/api/midi/<filename>", methods=["GET"])
def download_midi(filename: str):
    path = _safe_output_file(filename, {".mid"})
    if path is None:
        return jsonify({"error": "invalid MIDI filename"}), 400
    if not path.is_file():
        return jsonify({"error": "MIDI file not found"}), 404
    return send_file(path, as_attachment=True, download_name=path.name, mimetype="audio/midi")


@app.route("/api/composition/<filename>", methods=["GET"])
@app.route("/api/code/<filename>", methods=["GET"])
def download_composition(filename: str):
    path = _safe_output_file(filename, {".json"})
    if path is None:
        return jsonify({"error": "invalid composition filename"}), 400
    if not path.is_file():
        return jsonify({"error": "composition not found"}), 404
    return send_file(path, as_attachment=True, download_name=path.name, mimetype="application/json")


@app.route("/", defaults={"asset_path": ""})
@app.route("/<path:asset_path>")
def serve_frontend(asset_path: str):
    """Serve the built Vue app in production; Vite handles this during development."""
    if asset_path == "api" or asset_path.startswith("api/"):
        return jsonify({"error": "API endpoint not found"}), 404
    if not FRONTEND_DIST.is_dir():
        return jsonify(
            {
                "error": "frontend build not found",
                "hint": "run npm install && npm run build in the frontend directory",
            }
        ), 404
    requested = FRONTEND_DIST / asset_path
    if asset_path and requested.is_file():
        return send_from_directory(FRONTEND_DIST, asset_path)
    return send_from_directory(FRONTEND_DIST, "index.html")


if __name__ == "__main__":
    host = os.getenv("MUSICAGENT_HOST", "127.0.0.1")
    port = int(os.getenv("MUSICAGENT_PORT") or os.getenv("PORT", "5000"))
    debug = os.getenv("MUSICAGENT_DEBUG", "").lower() in {"1", "true", "yes"}
    print(f"MusicAgent API: http://{host}:{port}")
    print(f"Browser-native engine; DeepSeek enabled: {client is not None}")
    app.run(debug=debug, host=host, port=port, use_reloader=False)
