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
                             QMessageBox, QProgressBar, QDialog, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

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
import v2
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
        """Callback function for logging from v2 module"""
        self.log_message.emit(message)

    def run(self):
        try:
            # Show original prompt in code display before translation
            self.progress.emit("📝 Displaying original prompt...")
            self.log_message.emit(f"📝 Original User Prompt:\n{self.prompt_text}\n")
            self.log_message.emit("=" * 60 + "\n")
            
            self.progress.emit("🌐 Translating user requirements to professional terminology...")
            code, midi_path = v2.multi_agent_generate_sonic_pi(
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
        self.setWindowTitle("Music Feedback")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        label = QLabel("Please provide your feedback on the generated music:")
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)
        
        self.feedback_text = QTextEdit()
        self.feedback_text.setPlaceholderText("e.g., tempo too fast, pitch too high, need more bass, etc...")
        layout.addWidget(self.feedback_text)
        
        button_layout = QHBoxLayout()
        self.submit_btn = QPushButton("Submit Feedback")
        self.skip_btn = QPushButton("Skip")
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.skip_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.submit_btn.clicked.connect(self.accept)
        self.skip_btn.clicked.connect(self.reject)
    
    def get_feedback(self):
        return self.feedback_text.toPlainText()


class StyleTransferDialog(QDialog):
    """Style transfer dialog"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Style Transfer")
        self.setModal(True)
        self.resize(500, 300)
        
        layout = QVBoxLayout()
        
        label = QLabel("Please enter your style transfer request:")
        label.setFont(QFont("Arial", 12))
        layout.addWidget(label)
        
        help_label = QLabel("Examples:\n- Convert to rock style\n- Make it jazz\n- Transform to soft/quiet style\n- Change to electronic style")
        help_label.setFont(QFont("Arial", 9))
        help_label.setStyleSheet("color: gray;")
        layout.addWidget(help_label)
        
        self.style_text = QTextEdit()
        self.style_text.setPlaceholderText("e.g., convert to rock style, make it jazz, transform to soft/quiet style...")
        layout.addWidget(self.style_text)
        
        button_layout = QHBoxLayout()
        self.submit_btn = QPushButton("Transfer Style")
        self.cancel_btn = QPushButton("Cancel")
        button_layout.addWidget(self.submit_btn)
        button_layout.addWidget(self.cancel_btn)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        
        self.submit_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
    
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
        self.setWindowTitle("Sonic Pi Music Generator")
        self.setGeometry(100, 100, 900, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Title
        title = QLabel("🎵 Sonic Pi Music Generator")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Input area
        input_label = QLabel("Please enter music description:")
        input_label.setFont(QFont("Arial", 11))
        layout.addWidget(input_label)
        
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("e.g., a calm piano solo in C major, slow tempo, dreamy style")
        self.prompt_input.setMaximumHeight(100)
        layout.addWidget(self.prompt_input)
        
        # Button area
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Music Code")
        self.generate_btn.setFont(QFont("Arial", 11))
        self.generate_btn.clicked.connect(self.on_generate_clicked)
        button_layout.addWidget(self.generate_btn)
        
        self.feedback_btn = QPushButton("Provide Feedback")
        self.feedback_btn.setFont(QFont("Arial", 11))
        self.feedback_btn.clicked.connect(self.on_feedback_clicked)
        self.feedback_btn.setEnabled(False)
        button_layout.addWidget(self.feedback_btn)
        
        self.save_midi_btn = QPushButton("Save as MIDI")
        self.save_midi_btn.setFont(QFont("Arial", 11))
        self.save_midi_btn.clicked.connect(self.on_save_midi_clicked)
        self.save_midi_btn.setEnabled(False)
        button_layout.addWidget(self.save_midi_btn)
        
        self.style_transfer_btn = QPushButton("Style Transfer")
        self.style_transfer_btn.setFont(QFont("Arial", 11))
        self.style_transfer_btn.clicked.connect(self.on_style_transfer_clicked)
        self.style_transfer_btn.setEnabled(False)
        button_layout.addWidget(self.style_transfer_btn)
        
        layout.addLayout(button_layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Generated code display area
        code_label = QLabel("Generated Code:")
        code_label.setFont(QFont("Arial", 11))
        layout.addWidget(code_label)
        
        self.code_display = QTextEdit()
        self.code_display.setReadOnly(True)
        self.code_display.setFont(QFont("Courier", 10))
        layout.addWidget(self.code_display)
        
        # Log output area
        log_label = QLabel("Generation Log (Intermediate Results):")
        log_label.setFont(QFont("Arial", 11))
        layout.addWidget(log_label)
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        self.log_display.setFont(QFont("Courier", 9))
        self.log_display.setMaximumHeight(200)
        layout.addWidget(self.log_display)
        
    def init_client(self):
        """Initialize OpenAI client"""
        # Note: User needs to configure API key here
        api_key = 'sk-7416236c6b924c9e9343c642572ed969'  # Can be read from config file or environment variable
        base_url = "https://api.deepseek.com"
        self.client = OpenAI(api_key=api_key, base_url=base_url)
    
    def on_generate_clicked(self):
        """Generate button click event"""
        prompt_text = self.prompt_input.toPlainText().strip()
        if not prompt_text:
            QMessageBox.warning(self, "Warning", "Please enter music description!")
            return
        
        # Store original prompt
        self.original_prompt = prompt_text
        
        # Clear previous outputs
        self.code_display.clear()
        self.log_display.clear()
        
        # Show original prompt in code display before translation
        self.code_display.setPlainText(f"Original Prompt:\n{prompt_text}\n\nWaiting for translation...")
        
        # Disable buttons
        self.generate_btn.setEnabled(False)
        self.feedback_btn.setEnabled(False)
        self.save_midi_btn.setEnabled(False)
        self.style_transfer_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.status_label.setText("Generating...")
        
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
            self.status_label.setText(f"Generation completed! MIDI saved: {Path(midi_path).name}")
            self.log_display.append(f"\n✅ Generation completed! MIDI file: {self.midi_path}\n")
        else:
            self.status_label.setText("Generation completed! (MIDI compilation failed)")
            self.log_display.append("\n⚠️ Generation completed but MIDI compilation failed.\n")
        
        QMessageBox.information(
            self, 
            "Success", 
            f"Music code generation completed!\n\n"
            f"{'MIDI file saved: ' + str(self.midi_path) if self.midi_path else 'Note: MIDI compilation failed, but code generation succeeded.'}"
        )
    
    def on_generation_error(self, error_msg):
        """Generation error"""
        self.generate_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Generation failed")
        QMessageBox.critical(self, "Error", error_msg)
    
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
            QMessageBox.warning(self, "Warning", "No generated code available. Please generate code first.")
            return
        
        # Show feedback dialog
        feedback_dialog = FeedbackDialog(self)
        if feedback_dialog.exec_() == QDialog.Accepted:
            feedback = feedback_dialog.get_feedback()
            if feedback.strip():
                # Use feedback to regenerate code
                self.status_label.setText("Regenerating with feedback...")
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
                QMessageBox.information(self, "Info", "No feedback provided. Code remains unchanged.")
        else:
            self.status_label.setText("Feedback cancelled")
    
    def on_save_midi_clicked(self):
        """Save as MIDI button click event"""
        if not self.generated_code:
            QMessageBox.warning(self, "Warning", "No generated code available. Please generate code first.")
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
        self.status_label.setText("Starting MIDI recording...")
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
        self.status_label.setText(f"MIDI saved: {Path(filepath).name}")
        self.log_display.append(f"✅ MIDI file saved: {filepath}\n")
        QMessageBox.information(
            self,
            "Success",
            f"MIDI file saved successfully!\n\nFile: {filepath}\n\n"
            "You can now use this MIDI file in other music software."
        )
    
    def on_midi_save_failed(self):
        """Called when MIDI save failed"""
        self.save_midi_btn.setEnabled(True)
        self.status_label.setText("MIDI recording failed")
        self.log_display.append("❌ MIDI recording failed\n")
        QMessageBox.warning(
            self,
            "Warning",
            "Failed to record MIDI.\n\n"
            "Possible reasons:\n"
            "1. No MIDI output detected from Sonic Pi\n"
            "2. Sonic Pi code doesn't use 'midi' function\n"
            "3. MIDI port not found\n\n"
            "Make sure your code includes MIDI output commands like:\n"
            "  midi :C4\n"
            "  midi_note_on :E4, 80"
        )
    
    def on_midi_save_error(self, error_msg):
        """Called when MIDI save encounters an error"""
        self.save_midi_btn.setEnabled(True)
        self.status_label.setText("MIDI recording error")
        self.log_display.append(f"❌ MIDI recording error: {error_msg}\n")
        QMessageBox.critical(self, "Error", f"Error during MIDI recording:\n{error_msg}")
    
    def on_style_transfer_clicked(self):
        """Style transfer button click event"""
        if not self.generated_code:
            QMessageBox.warning(self, "Warning", "No generated code available. Please generate code first.")
            return
        
        # Show style transfer dialog
        style_dialog = StyleTransferDialog(self)
        if style_dialog.exec_() == QDialog.Accepted:
            style_request = style_dialog.get_style_request()
            if style_request.strip():
                # Start style transfer
                self.status_label.setText("Transferring style...")
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
                QMessageBox.information(self, "Info", "No style request provided. Style transfer cancelled.")
        else:
            self.status_label.setText("Style transfer cancelled")
    
    def on_style_transfer_finished(self, transformed_code):
        """Style transfer completed"""
        self.generated_code = transformed_code
        self.code_display.setPlainText(transformed_code)
        self.generate_btn.setEnabled(True)
        self.feedback_btn.setEnabled(True)
        self.save_midi_btn.setEnabled(True)
        self.style_transfer_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Style transfer completed!")
        self.log_display.append(f"\n✅ Style transfer completed!\n")
        QMessageBox.information(
            self,
            "Success",
            "Style transfer completed successfully!\n\nThe code has been transformed according to your style request."
        )
    
    def on_style_transfer_error(self, error_msg):
        """Style transfer error"""
        self.generate_btn.setEnabled(True)
        self.feedback_btn.setEnabled(True)
        self.save_midi_btn.setEnabled(True)
        self.style_transfer_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Style transfer failed")
        self.log_display.append(f"\n❌ Style transfer error: {error_msg}\n")
        QMessageBox.critical(self, "Error", f"Error during style transfer:\n{error_msg}")


def main():
    app = QApplication(sys.argv)
    
    # Set application style
    app.setStyle('Fusion')
    
    window = MusicGeneratorGUI()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

