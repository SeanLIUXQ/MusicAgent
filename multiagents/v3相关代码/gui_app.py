#!/usr/bin/env python3
"""
Sonic Pi Music Generator GUI Application
--------------------------------------
Features:
1. PyQt window for music description input
2. Execute multi-agent logic to generate Sonic Pi code
3. Use OCR to read Sonic Pi client interface
4. Automatically paste code to Sonic Pi text box
5. Ask for user feedback
"""

import sys
import re
import time
import threading
from pathlib import Path
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QTextEdit, QPushButton, QLabel, 
                             QMessageBox, QProgressBar, QDialog, QLineEdit,
                             QFrame, QScrollArea, QGroupBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QPropertyAnimation, QEasingCurve, QRect
from PyQt5.QtGui import QFont, QPalette, QColor, QIcon

try:
    import pyautogui
    HAVE_PYAUTOGUI = True
except ImportError:
    HAVE_PYAUTOGUI = False
    print("[⚠️] pyautogui not installed, some automation features may be unavailable")

try:
    import pytesseract
    from PIL import Image
    HAVE_OCR = True
except ImportError:
    HAVE_OCR = False
    print("[⚠️] OCR libraries not installed, OCR functionality unavailable")

try:
    import win32gui
    import win32con
    import win32clipboard
    HAVE_WIN32 = True
except ImportError:
    HAVE_WIN32 = False
    print("[⚠️] pywin32 not installed, window finding functionality may be unavailable")

# Comprehensive check for automation capability
HAVE_AUTOMATION = HAVE_PYAUTOGUI and HAVE_WIN32

from openai import OpenAI
import v3
import style_transfer
from pathlib import Path


class GenerateThread(QThread):
    """Thread for generating code"""
    finished = pyqtSignal(str, str)  # Generation completed, pass (code, midi_path)
    error = pyqtSignal(str)  # Error signal
    progress = pyqtSignal(str)  # Progress update
    log_message = pyqtSignal(str)  # Log message signal

    def __init__(self, prompt_text, client, user_feedback=None, previous_code=None, output_dir=None):
        super().__init__()
        self.prompt_text = prompt_text
        self.client = client
        self.user_feedback = user_feedback
        self.previous_code = previous_code
        self.output_dir = output_dir

    def log_callback(self, message):
        """Callback function for logging from v3 module"""
        self.log_message.emit(message)

    def run(self):
        try:
            # Show original prompt in code display before translation
            self.progress.emit("📝 Displaying original prompt...")
            self.log_message.emit(f"📝 Original User Prompt:\n{self.prompt_text}\n")
            self.log_message.emit("=" * 60 + "\n")
            
            self.progress.emit("🌐 Translating user requirements to professional terminology...")
            code, midi_path = v3.multi_agent_generate_sonic_pi(
                self.prompt_text, 
                self.client, 
                user_feedback=self.user_feedback,
                previous_code=self.previous_code,
                output_dir=self.output_dir,
                log_callback=self.log_callback
            )
            if code:
                self.finished.emit(code, midi_path or "")
            else:
                self.error.emit("Generation failed, no code retrieved")
        except Exception as e:
            self.error.emit(f"Error during generation: {str(e)}")
            import traceback
            self.log_message.emit(f"\n❌ Error: {str(e)}\n")
            self.log_message.emit(f"Traceback:\n{traceback.format_exc()}\n")


class StyleTransferThread(QThread):
    """Thread for style transfer"""
    finished = pyqtSignal(str)  # Style transfer completed, pass transformed code
    error = pyqtSignal(str)  # Error signal
    progress = pyqtSignal(str)  # Progress update
    log_message = pyqtSignal(str)  # Log message signal

    def __init__(self, original_code, style_request, client):
        super().__init__()
        self.original_code = original_code
        self.style_request = style_request
        self.client = client

    def log_callback(self, message):
        """Callback function for logging from style_transfer module"""
        self.log_message.emit(message)

    def run(self):
        try:
            self.progress.emit("🎨 Starting style transfer...")
            transformed_code = style_transfer.style_transfer_sonic_pi(
                self.original_code,
                self.style_request,
                self.client,
                log_callback=self.log_callback
            )
            if transformed_code:
                self.finished.emit(transformed_code)
            else:
                self.error.emit("Style transfer failed, no code retrieved")
        except Exception as e:
            self.error.emit(f"Error during style transfer: {str(e)}")
            import traceback
            self.log_message.emit(f"\n❌ Error: {str(e)}\n")
            self.log_message.emit(f"Traceback:\n{traceback.format_exc()}\n")


class FeedbackDialog(QDialog):
    """Feedback dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("💬 Music Feedback")
        self.setModal(True)
        self.resize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                padding: 10px;
            }
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-size: 11pt;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #4a90e2;
            }
            QPushButton {
                background-color: #4a90e2;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #357abd;
            }
            QPushButton:pressed {
                background-color: #2a5f8f;
            }
            QPushButton#skipBtn {
                background-color: #95a5a6;
            }
            QPushButton#skipBtn:hover {
                background-color: #7f8c8d;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("💬 Please provide your feedback on the generated music:")
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(label)
        
        self.feedback_text = QTextEdit()
        self.feedback_text.setPlaceholderText("例如：节奏太快、音调太高、需要更多低音、增加和声层次等...")
        self.feedback_text.setMinimumHeight(150)
        layout.addWidget(self.feedback_text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.skip_btn = QPushButton("跳过")
        self.skip_btn.setObjectName("skipBtn")
        self.skip_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.skip_btn)
        
        self.submit_btn = QPushButton("提交反馈")
        self.submit_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.submit_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_feedback(self):
        return self.feedback_text.toPlainText()


class StyleTransferDialog(QDialog):
    """Style transfer dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎨 Style Transfer")
        self.setModal(True)
        self.resize(600, 400)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333;
                padding: 5px;
            }
            QTextEdit {
                border: 2px solid #ddd;
                border-radius: 8px;
                padding: 10px;
                font-size: 11pt;
                background-color: white;
            }
            QTextEdit:focus {
                border: 2px solid #9b59b6;
            }
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
            QPushButton#cancelBtn {
                background-color: #95a5a6;
            }
            QPushButton#cancelBtn:hover {
                background-color: #7f8c8d;
            }
        """)
        
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        label = QLabel("🎨 Please enter your style transfer request:")
        label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        layout.addWidget(label)
        
        help_label = QLabel("💡 示例：\n• 转换为摇滚风格\n• 改为爵士风格\n• 转换为柔和/安静风格\n• 改为电子音乐风格")
        help_label.setFont(QFont("Segoe UI", 10))
        help_label.setStyleSheet("color: #7f8c8d; background-color: #ecf0f1; padding: 10px; border-radius: 6px;")
        layout.addWidget(help_label)
        
        self.style_text = QTextEdit()
        self.style_text.setPlaceholderText("例如：转换为摇滚风格、改为爵士风格、转换为柔和安静风格...")
        self.style_text.setMinimumHeight(120)
        layout.addWidget(self.style_text)
        
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.setObjectName("cancelBtn")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.submit_btn = QPushButton("转换风格")
        self.submit_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.submit_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def get_style_request(self):
        return self.style_text.toPlainText()


class MusicGeneratorGUI(QMainWindow):
    # Define signals
    generation_complete = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.generated_code = ""
        self.original_prompt = ""
        self.midi_path = None
        self.midi_output_dir = Path(".") / "midi_output"
        self.midi_output_dir.mkdir(exist_ok=True)
        self.init_ui()
        self.init_client()
        
        # Connect signals
        self.generation_complete.connect(self.on_generation_complete)
        
    def init_ui(self):
        self.setWindowTitle("🎵 Sonic Pi Music Generator")
        self.setGeometry(100, 100, 1100, 900)
        
        # Apply modern style sheet
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                font-family: 'Segoe UI', 'Microsoft YaHei', Arial, sans-serif;
            }
            QLabel {
                color: #2c3e50;
            }
            QTextEdit {
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                padding: 10px;
                background-color: white;
                selection-background-color: #4a90e2;
            }
            QTextEdit:focus {
                border: 2px solid #4a90e2;
            }
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 12px 24px;
                font-size: 11pt;
                font-weight: bold;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
            QPushButton:disabled {
                background-color: #bdc3c7;
                color: #7f8c8d;
            }
            QPushButton#generateBtn {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #3498db, stop:1 #2980b9);
                font-size: 12pt;
                padding: 14px 28px;
            }
            QPushButton#generateBtn:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                    stop:0 #2980b9, stop:1 #21618c);
            }
            QPushButton#feedbackBtn {
                background-color: #2ecc71;
            }
            QPushButton#feedbackBtn:hover {
                background-color: #27ae60;
            }
            QPushButton#midiBtn {
                background-color: #e67e22;
            }
            QPushButton#midiBtn:hover {
                background-color: #d35400;
            }
            QPushButton#styleBtn {
                background-color: #9b59b6;
            }
            QPushButton#styleBtn:hover {
                background-color: #8e44ad;
            }
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 8px;
                text-align: center;
                background-color: #ecf0f1;
                height: 25px;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3498db, stop:1 #2980b9);
                border-radius: 6px;
            }
            QGroupBox {
                font-weight: bold;
                border: 2px solid #e1e8ed;
                border-radius: 8px;
                margin-top: 10px;
                padding-top: 15px;
                background-color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 5px;
                color: #2c3e50;
            }
        """)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        central_widget.setLayout(layout)
        
        # Header with title
        header_frame = QFrame()
        header_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                    stop:0 #3498db, stop:1 #9b59b6);
                border-radius: 10px;
                padding: 20px;
            }
        """)
        header_layout = QVBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        title = QLabel("🎵 Sonic Pi Music Generator")
        title.setFont(QFont("Segoe UI", 24, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: white;")
        header_layout.addWidget(title)
        
        subtitle = QLabel("AI-Powered Music Code Generation")
        subtitle.setFont(QFont("Segoe UI", 11))
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.9);")
        header_layout.addWidget(subtitle)
        
        header_frame.setLayout(header_layout)
        layout.addWidget(header_frame)
        
        # Input area with group box
        input_group = QGroupBox("📝 Music Description")
        input_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        input_layout = QVBoxLayout()
        input_layout.setSpacing(10)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("例如：一段适合午后咖啡厅的舒缓优雅的音乐，C大调，慢速，梦幻风格...")
        self.prompt_input.setMaximumHeight(100)
        self.prompt_input.setFont(QFont("Segoe UI", 10))
        input_layout.addWidget(self.prompt_input)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Button area with improved styling
        button_group = QGroupBox("⚡ Actions")
        button_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        button_layout = QHBoxLayout()
        button_layout.setSpacing(12)
        
        self.generate_btn = QPushButton("🎼 Generate Music Code")
        self.generate_btn.setObjectName("generateBtn")
        self.generate_btn.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        button_layout.addWidget(self.generate_btn)
        
        self.feedback_btn = QPushButton("💬 Provide Feedback")
        self.feedback_btn.setObjectName("feedbackBtn")
        self.feedback_btn.setFont(QFont("Segoe UI", 10))
        self.feedback_btn.clicked.connect(self.on_feedback_clicked)
        self.feedback_btn.setEnabled(False)
        button_layout.addWidget(self.feedback_btn)
        
        self.save_midi_btn = QPushButton("💾 Save as MIDI")
        self.save_midi_btn.setObjectName("midiBtn")
        self.save_midi_btn.setFont(QFont("Segoe UI", 10))
        self.save_midi_btn.clicked.connect(self.on_save_midi_clicked)
        self.save_midi_btn.setEnabled(False)
        button_layout.addWidget(self.save_midi_btn)
        
        self.style_transfer_btn = QPushButton("🎨 Style Transfer")
        self.style_transfer_btn.setObjectName("styleBtn")
        self.style_transfer_btn.setFont(QFont("Segoe UI", 10))
        self.style_transfer_btn.clicked.connect(self.on_style_transfer_clicked)
        self.style_transfer_btn.setEnabled(False)
        button_layout.addWidget(self.style_transfer_btn)
        
        button_group.setLayout(button_layout)
        layout.addWidget(button_group)
        
        # Progress bar with status
        progress_frame = QFrame()
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setFont(QFont("Segoe UI", 9))
        progress_layout.addWidget(self.progress_bar)
        
        self.status_label = QLabel("✨ Ready to generate music...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 10))
        self.status_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                padding: 8px;
                background-color: #d5f4e6;
                border-radius: 6px;
            }
        """)
        progress_layout.addWidget(self.status_label)
        
        progress_frame.setLayout(progress_layout)
        layout.addWidget(progress_frame)
        
        # Generated code display area with group box
        code_group = QGroupBox("📄 Generated Code")
        code_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        code_layout = QVBoxLayout()
        code_layout.setSpacing(5)
        
        self.code_display = QTextEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setFont(QFont("Consolas", 10))
        self.code_display.setStyleSheet("""
            QTextEdit {
                background-color: #2c3e50;
                color: #ecf0f1;
                border: 2px solid #34495e;
                font-family: 'Consolas', 'Courier New', monospace;
            }
        """)
        code_layout.addWidget(self.code_display)
        
        code_group.setLayout(code_layout)
        layout.addWidget(code_group)
        
        # Log output area with group box
        log_group = QGroupBox("📋 Generation Log")
        log_group.setFont(QFont("Segoe UI", 11, QFont.Bold))
        log_layout = QVBoxLayout()
        log_layout.setSpacing(5)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Consolas", 9))
        self.log_display.setMaximumHeight(200)
        self.log_display.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                color: #2c3e50;
                border: 2px solid #e1e8ed;
            }
        """)
        log_layout.addWidget(self.log_display)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
    def init_client(self):
        """Initialize OpenAI client"""
        # Note: User needs to configure API key here
        api_key = 'sk-6712722a83a74cad9f73294f42495d5c'  # Can be read from config file or environment variable
        base_url = "https://api.deepseek.com/v1"
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def on_generate_clicked(self):
        """Generate button click event"""
        prompt_text = self.prompt_input.toPlainText().strip()
        if not prompt_text:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("⚠️ Warning")
            msg.setText("请输入音乐描述！")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #2c3e50;
                }
            """)
            msg.exec_()
            return
        
        # Store original prompt
        self.original_prompt = prompt_text
        
        # Clear previous outputs
        self.code_display.clear()
        self.log_display.clear()
        
        # Show original prompt in code display before translation
        self.code_display.setPlainText(f"Original Prompt:\n{prompt_text}\n\n⏳ Waiting for translation...")
        
        # Disable buttons
        self.generate_btn.setEnabled(False)
        self.feedback_btn.setEnabled(False)
        self.save_midi_btn.setEnabled(False)
        self.style_transfer_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("🌐 正在生成音乐代码...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #3498db;
                padding: 8px;
                background-color: #d6eaf8;
                border-radius: 6px;
            }
        """)
        
        # Start generation thread
        self.generate_thread = GenerateThread(prompt_text, self.client, output_dir=str(self.midi_output_dir))
        self.generate_thread.finished.connect(self.on_generation_finished)
        self.generate_thread.error.connect(self.on_generation_error)
        self.generate_thread.progress.connect(self.on_progress_update)
        self.generate_thread.log_message.connect(self.on_log_message)
        self.generate_thread.start()
    
    def on_progress_update(self, message):
        """Update progress information"""
        self.status_label.setText(message)
        # Update status label style based on message type
        if "Error" in message or "Failed" in message or "❌" in message:
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #e74c3c;
                    padding: 8px;
                    background-color: #fadbd8;
                    border-radius: 6px;
                }
            """)
        elif "completed" in message.lower() or "✅" in message:
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    padding: 8px;
                    background-color: #d5f4e6;
                    border-radius: 6px;
                }
            """)
        elif "Generating" in message or "正在" in message or "🌐" in message or "🎼" in message:
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #3498db;
                    padding: 8px;
                    background-color: #d6eaf8;
                    border-radius: 6px;
                }
            """)
        else:
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    padding: 8px;
                    background-color: #ecf0f1;
                    border-radius: 6px;
                }
            """)
    
    def on_log_message(self, message):
        """Handle log messages from generation thread"""
        self.log_display.append(message)
        # Auto-scroll to bottom
        scrollbar = self.log_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def on_generation_finished(self, code, midi_path):
        """Generation completed"""
        self.generated_code = code
        self.midi_path = midi_path if midi_path else None
        self.code_display.setPlainText(code)
        self.generate_btn.setEnabled(True)
        self.feedback_btn.setEnabled(True)
        self.save_midi_btn.setEnabled(True)
        self.style_transfer_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        
        if self.midi_path:
            self.status_label.setText(f"✅ 生成完成！MIDI 文件已保存: {Path(midi_path).name}")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #27ae60;
                    padding: 8px;
                    background-color: #d5f4e6;
                    border-radius: 6px;
                }
            """)
            self.log_display.append(f"\n✅ Generation completed! MIDI file: {self.midi_path}\n")
        else:
            self.status_label.setText("⚠️ 生成完成！(MIDI 编译失败)")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #f39c12;
                    padding: 8px;
                    background-color: #fef5e7;
                    border-radius: 6px;
                }
            """)
            self.log_display.append("\n⚠️ Generation completed but MIDI compilation failed.\n")
        
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("✅ Success")
        msg.setText("音乐代码生成完成！")
        if self.midi_path:
            msg.setInformativeText(f"MIDI 文件已保存：\n{self.midi_path}")
        else:
            msg.setInformativeText("注意：MIDI 编译失败，但代码生成成功。")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
            }
        """)
        msg.exec_()
    
    def on_generation_error(self, error_msg):
        """Generation error"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ 生成失败")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                padding: 8px;
                background-color: #fadbd8;
                border-radius: 6px;
            }
        """)
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("❌ Error")
        msg.setText("生成失败")
        msg.setInformativeText(error_msg)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
            }
        """)
        msg.exec_()
    
    def on_generation_complete(self):
        """Called when generation with feedback is complete"""
        self.feedback_btn.setEnabled(True)
        self.generate_btn.setEnabled(True)
    
    def find_sonic_pi_window(self):
        """Find Sonic Pi window"""
        if not HAVE_WIN32:
            return None
        
        def enum_handler(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                window_title = win32gui.GetWindowText(hwnd)
                if "Sonic Pi" in window_title:
                    windows.append((hwnd, window_title))
        
        windows = []
        try:
            win32gui.EnumWindows(enum_handler, windows)
        except Exception as e:
            print(f"Failed to enumerate windows: {e}")
            return None
        
        if windows:
            return windows[0][0]  # Return first found window handle
        return None
    
    def capture_sonic_pi_editor(self, hwnd):
        """Capture Sonic Pi editor area"""
        if not HAVE_OCR:
            return None
        
        try:
            # Get window position and size
            rect = win32gui.GetWindowRect(hwnd)
            left, top, right, bottom = rect
            
            # Screenshot
            screenshot = pyautogui.screenshot(region=(left, top, right - left, bottom - top))
            return screenshot
        except Exception as e:
            print(f"Screenshot failed: {e}")
            return None
    
    def find_text_box_with_ocr(self, screenshot):
        """Use OCR to find text box position"""
        if not HAVE_OCR:
            return None
        
        try:
            # Use OCR to recognize text
            # Note: This may need adjustment based on actual Sonic Pi interface
            # Can try to identify specific text or buttons to locate editor
            
            # Simple method: assume editor is in specific area of window
            # In practice, may need more complex OCR logic
            return True
        except Exception as e:
            print(f"OCR recognition failed: {e}")
            return None
    
    def on_feedback_clicked(self):
        """Feedback button click event"""
        if not self.generated_code:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("⚠️ Warning")
            msg.setText("没有生成的代码可用。请先生成代码。")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #2c3e50;
                }
            """)
            msg.exec_()
            return
        
        # Show feedback dialog
        feedback_dialog = FeedbackDialog(self)
        if feedback_dialog.exec_() == QDialog.Accepted:
            feedback = feedback_dialog.get_feedback()
            if feedback.strip():
                # Use feedback to regenerate code
                self.status_label.setText("🔄 正在根据反馈重新生成...")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #3498db;
                        padding: 8px;
                        background-color: #d6eaf8;
                        border-radius: 6px;
                    }
                """)
                self.generate_btn.setEnabled(False)
                self.feedback_btn.setEnabled(False)
                self.save_midi_btn.setEnabled(False)
                self.style_transfer_btn.setEnabled(False)
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
                
                # Clear log and show feedback
                self.log_display.append("\n" + "=" * 60 + "\n")
                self.log_display.append(f"🔄 Regenerating with user feedback:\n{feedback}\n")
                self.log_display.append("=" * 60 + "\n")
                
                # Store previous code for comparison
                previous_code = self.generated_code
                
                # Start generation thread with feedback
                self.generate_thread = GenerateThread(
                    self.original_prompt, 
                    self.client,
                    user_feedback=feedback,
                    previous_code=previous_code,
                    output_dir=str(self.midi_output_dir)
                )
                self.generate_thread.finished.connect(self.on_generation_finished)
                self.generate_thread.error.connect(self.on_generation_error)
                self.generate_thread.progress.connect(self.on_progress_update)
                self.generate_thread.log_message.connect(self.on_log_message)
                self.generate_thread.start()
            else:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("ℹ️ Info")
                msg.setText("未提供反馈。代码保持不变。")
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: white;
                    }
                    QMessageBox QLabel {
                        color: #2c3e50;
                    }
                """)
                msg.exec_()
        else:
            self.status_label.setText("反馈已取消")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #95a5a6;
                    padding: 8px;
                    background-color: #ecf0f1;
                    border-radius: 6px;
                }
            """)
    
    def on_save_midi_clicked(self):
        """Save as MIDI button click event"""
        if not self.generated_code:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("⚠️ Warning")
            msg.setText("没有生成的代码可用。请先生成代码。")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #2c3e50;
                }
            """)
            msg.exec_()
            return
        
        # Show instructions dialog
        reply = QMessageBox.question(
            self,
            "Save as MIDI",
            "To save as MIDI, you need to:\n\n"
            "1. Make sure Sonic Pi is running\n"
            "2. The generated code should use 'midi' function for MIDI output\n"
            "3. Run the code in Sonic Pi\n"
            "4. This will record the MIDI output\n\n"
            "Do you want to start recording now?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        )
        
        if reply == QMessageBox.No:
            return
        
        # Disable button during recording
        self.save_midi_btn.setEnabled(False)
        self.status_label.setText("🎙️ 正在开始 MIDI 录制...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e67e22;
                padding: 8px;
                background-color: #fdebd0;
                border-radius: 6px;
            }
        """)
        self.log_display.append("\n🎙️ Starting MIDI recording from Sonic Pi...\n")
        
        # Start recording in a separate thread
        def record_midi():
            try:
                from record_midi import SonicPiMidiRecorder
                recorder = SonicPiMidiRecorder(output_dir=str(self.midi_output_dir))
                saved_file = recorder.record_once(silence_timeout=3.0, max_duration=120.0)
                
                if saved_file:
                    # Show success message in main thread
                    from PyQt5.QtCore import QTimer
                    QTimer.singleShot(0, lambda: self.on_midi_saved(saved_file))
                else:
                    QTimer.singleShot(0, lambda: self.on_midi_save_failed())
            except Exception as e:
                QTimer.singleShot(0, lambda: self.on_midi_save_error(str(e)))
        
        import threading
        thread = threading.Thread(target=record_midi)
        thread.daemon = True
        thread.start()
    
    def on_midi_saved(self, filepath):
        """Called when MIDI is successfully saved"""
        self.save_midi_btn.setEnabled(True)
        self.status_label.setText(f"✅ MIDI 已保存: {Path(filepath).name}")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                padding: 8px;
                background-color: #d5f4e6;
                border-radius: 6px;
            }
        """)
        self.log_display.append(f"✅ MIDI file saved: {filepath}\n")
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("✅ Success")
        msg.setText("MIDI 文件保存成功！")
        msg.setInformativeText(f"文件: {filepath}\n\n您现在可以在其他音乐软件中使用此 MIDI 文件。")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
            }
        """)
        msg.exec_()
    
    def on_midi_save_failed(self):
        """Called when MIDI save failed"""
        self.save_midi_btn.setEnabled(True)
        self.status_label.setText("❌ MIDI 录制失败")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                padding: 8px;
                background-color: #fadbd8;
                border-radius: 6px;
            }
        """)
        self.log_display.append("❌ MIDI recording failed\n")
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("⚠️ Warning")
        msg.setText("MIDI 录制失败")
        msg.setInformativeText(
            "可能的原因：\n"
            "1. 未检测到 Sonic Pi 的 MIDI 输出\n"
            "2. Sonic Pi 代码未使用 'midi' 函数\n"
            "3. 未找到 MIDI 端口\n\n"
            "请确保您的代码包含 MIDI 输出命令，例如：\n"
            "  midi :C4\n"
            "  midi_note_on :E4, 80"
        )
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
            }
        """)
        msg.exec_()
    
    def on_midi_save_error(self, error_msg):
        """Called when MIDI save encounters an error"""
        self.save_midi_btn.setEnabled(True)
        self.status_label.setText("❌ MIDI 录制错误")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                padding: 8px;
                background-color: #fadbd8;
                border-radius: 6px;
            }
        """)
        self.log_display.append(f"❌ MIDI recording error: {error_msg}\n")
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("❌ Error")
        msg.setText("MIDI 录制过程中发生错误")
        msg.setInformativeText(error_msg)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
            }
        """)
        msg.exec_()
    
    def on_style_transfer_clicked(self):
        """Style transfer button click event"""
        if not self.generated_code:
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("⚠️ Warning")
            msg.setText("没有生成的代码可用。请先生成代码。")
            msg.setStyleSheet("""
                QMessageBox {
                    background-color: white;
                }
                QMessageBox QLabel {
                    color: #2c3e50;
                }
            """)
            msg.exec_()
            return
        
        # Show style transfer dialog
        style_dialog = StyleTransferDialog(self)
        if style_dialog.exec_() == QDialog.Accepted:
            style_request = style_dialog.get_style_request()
            if style_request.strip():
                # Start style transfer
                self.status_label.setText("🎨 正在转换风格...")
                self.status_label.setStyleSheet("""
                    QLabel {
                        color: #9b59b6;
                        padding: 8px;
                        background-color: #ebdef0;
                        border-radius: 6px;
                    }
                """)
                self.generate_btn.setEnabled(False)
                self.feedback_btn.setEnabled(False)
                self.save_midi_btn.setEnabled(False)
                self.style_transfer_btn.setEnabled(False)
                self.progress_bar.setVisible(True)
                self.progress_bar.setRange(0, 0)
                
                # Clear log and show style transfer info
                self.log_display.append("\n" + "=" * 60 + "\n")
                self.log_display.append(f"🎨 Starting style transfer:\nStyle Request: {style_request}\n")
                self.log_display.append("=" * 60 + "\n")
                
                # Store original code
                original_code = self.generated_code
                
                # Start style transfer thread
                self.style_transfer_thread = StyleTransferThread(
                    original_code,
                    style_request,
                    self.client
                )
                self.style_transfer_thread.finished.connect(self.on_style_transfer_finished)
                self.style_transfer_thread.error.connect(self.on_style_transfer_error)
                self.style_transfer_thread.progress.connect(self.on_progress_update)
                self.style_transfer_thread.log_message.connect(self.on_log_message)
                self.style_transfer_thread.start()
            else:
                msg = QMessageBox(self)
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("ℹ️ Info")
                msg.setText("未提供风格转换请求。风格转换已取消。")
                msg.setStyleSheet("""
                    QMessageBox {
                        background-color: white;
                    }
                    QMessageBox QLabel {
                        color: #2c3e50;
                    }
                """)
                msg.exec_()
        else:
            self.status_label.setText("风格转换已取消")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: #95a5a6;
                    padding: 8px;
                    background-color: #ecf0f1;
                    border-radius: 6px;
                }
            """)
    
    def on_style_transfer_finished(self, transformed_code):
        """Style transfer completed"""
        self.generated_code = transformed_code
        self.code_display.setPlainText(transformed_code)
        self.generate_btn.setEnabled(True)
        self.feedback_btn.setEnabled(True)
        self.save_midi_btn.setEnabled(True)
        self.style_transfer_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("✅ 风格转换完成！")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #27ae60;
                padding: 8px;
                background-color: #d5f4e6;
                border-radius: 6px;
            }
        """)
        self.log_display.append(f"\n✅ Style transfer completed!\n")
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Information)
        msg.setWindowTitle("✅ Success")
        msg.setText("风格转换完成！")
        msg.setInformativeText("代码已根据您的风格请求成功转换。")
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
            }
        """)
        msg.exec_()
    
    def on_style_transfer_error(self, error_msg):
        """Style transfer error"""
        self.generate_btn.setEnabled(True)
        self.feedback_btn.setEnabled(True)
        self.save_midi_btn.setEnabled(True)
        self.style_transfer_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("❌ 风格转换失败")
        self.status_label.setStyleSheet("""
            QLabel {
                color: #e74c3c;
                padding: 8px;
                background-color: #fadbd8;
                border-radius: 6px;
            }
        """)
        self.log_display.append(f"\n❌ Style transfer error: {error_msg}\n")
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("❌ Error")
        msg.setText("风格转换过程中发生错误")
        msg.setInformativeText(error_msg)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: white;
            }
            QMessageBox QLabel {
                color: #2c3e50;
            }
        """)
        msg.exec_()


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    # Set application palette for better color scheme
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(248, 249, 250))
    palette.setColor(QPalette.WindowText, QColor(44, 62, 80))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(236, 240, 241))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 255))
    palette.setColor(QPalette.ToolTipText, QColor(44, 62, 80))
    palette.setColor(QPalette.Text, QColor(44, 62, 80))
    palette.setColor(QPalette.Button, QColor(52, 152, 219))
    palette.setColor(QPalette.ButtonText, QColor(255, 255, 255))
    palette.setColor(QPalette.BrightText, QColor(231, 76, 60))
    palette.setColor(QPalette.Link, QColor(52, 152, 219))
    palette.setColor(QPalette.Highlight, QColor(52, 152, 219))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = MusicGeneratorGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

