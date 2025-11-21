from __future__ import annotations

"""
sonic_pi_sender.py

用于将 Sonic Pi 代码发送到 Sonic Pi：

- 单元测试模式：
    使用 FakeClient 直接接收 OSC 信息（不触发任何 GUI 或系统调用）

- 真实模式：
    macOS: AppleScript
    Windows: AutoHotkey v2
    Linux: xdotool + xclip
"""

from pythonosc.osc_message import OscMessage
from pythonosc.osc_message_builder import OscMessageBuilder
import platform
import subprocess
import textwrap
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional


# -------------------------------------------------------------------
# 全局：会被 unittest 覆盖的 OSC client
# -------------------------------------------------------------------
_osc_client = None


# -------------------------------------------------------------------
# 主入口
# -------------------------------------------------------------------
def send_code_to_sonic_pi(code: str, log_callback=None):
    """
    主入口函数。

    如果 unittest 设置了 _osc_client，则进入测试模式：
        - 构造 /run-code 的 OscMessage
        - FakeClient.send(msg)
    否则进入真实 GUI 模式：
        - macOS: AppleScript
        - Windows: AutoHotkey
        - Linux: xdotool + xclip
    """

    def log(msg: str):
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    # === 空代码 ===
    if not code or not code.strip():
        log("代码为空")
        return

    global _osc_client

    # ================================================================
    # 1. 单元测试模式（FakeClient）
    #    使用 OscMessageBuilder 正常构造 OscMessage
    # ================================================================
    if _osc_client is not None:
        try:
            # 使用 Builder 构造 OscMessage，避免 datagram 解析错误
            builder = OscMessageBuilder(address="/run-code")
            builder.add_arg(code)
            msg: OscMessage = builder.build()

            # 调用 unittest 注入的 FakeClient / ErrorClient
            _osc_client.send(msg)

            log("已通过 OSC 将代码发送到 Sonic Pi")
        except Exception as e:
            log("发送到 Sonic Pi 失败")
            log(str(e))
        return

    # ================================================================
    # 2. 真实模式：macOS / Windows / Linux
    # ================================================================
    system = platform.system()
    log(f"🖥 当前平台: {system}")

    try:
        if system == "Darwin":
            _send_on_macos(code, log)
        elif system == "Windows":
            _send_on_windows(code, log)
        else:
            _send_on_linux(code, log)
    except Exception as e:
        log("发送到 Sonic Pi 失败")
        log(str(e))


# ===================================================================
# macOS 实现
# ===================================================================
def _send_on_macos(code: str, log: Callable[[str], None]) -> None:
    log("🍏 使用 macOS AppleScript 方式发送代码到 Sonic Pi。")

    # 将代码写入剪贴板
    pbcopy = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    pbcopy.communicate(code.encode("utf-8"))
    log("📋 已将代码写入剪贴板。")

    applescript = textwrap.dedent(
        r'''
        on is_current_buffer_empty()
            set oldClip to the clipboard
            tell application "System Events"
                if not (exists process "Sonic Pi") then return true
                tell process "Sonic Pi"
                    keystroke "a" using {command down}
                    delay 0.05
                    keystroke "c" using {command down}
                end tell
            end tell
            delay 0.05
            set currentCode to the clipboard as text
            set the clipboard to oldClip

            if currentCode is "" or currentCode is linefeed or currentCode is " " then
                return true
            else
                return false
            end if
        end is_current_buffer_empty

        on switch_to_next_buffer()
            tell application "System Events"
                if not (exists process "Sonic Pi") then return
                tell process "Sonic Pi"
                    key code 124 using {command down, option down}
                end tell
            end tell
        end switch_to_next_buffer

        on replace_buffer_and_run()
            tell application "System Events"
                if not (exists process "Sonic Pi") then return
                tell process "Sonic Pi"
                    keystroke "a" using {command down}
                    delay 0.05
                    keystroke "v" using {command down}
                    delay 0.1
                    keystroke "r" using {command down}
                end tell
            end tell
        end replace_buffer_and_run

        on run
            tell application "Sonic Pi"
                activate
            end tell
            delay 0.4

            tell application "System Events"
                if not (exists process "Sonic Pi") then return
            end tell

            set isEmpty to my is_current_buffer_empty()

            if isEmpty then
                my replace_buffer_and_run()
            else:
                my switch_to_next_buffer()
                delay 0.2
                my replace_buffer_and_run()
            end if
        end run
        '''
    )

    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        log("✅ 已通过 GUI 将代码粘贴到 Sonic Pi 并尝试自动运行（macOS）。")
    else:
        log(f"❌ AppleScript 执行失败（macOS）：{result.stderr}")


# ===================================================================
# Windows 实现：AutoHotkey v2
# ===================================================================
def _send_on_windows(code: str, log: Callable[[str], None]) -> None:
    log("🪟 使用 Windows + AutoHotkey 方式发送代码到 Sonic Pi。")

    ahk_path = shutil.which("ahk.exe") or shutil.which("AutoHotkey.exe")
    if not ahk_path:
        log("❌ 未找到 AutoHotkey (ahk.exe / AutoHotkey.exe)，请安装 AutoHotkey v2 并加入 PATH。")
        return

    tmp_code = Path(tempfile.gettempdir()) / "sonic_pi_code.rb"
    tmp_code.write_text(code, encoding="utf-8")

    ahk_script = textwrap.dedent(
        r'''
        #SingleInstance Force

        codeFile := A_Args[1]
        code := FileRead(codeFile, "UTF-8")

        if !WinActivate("Sonic Pi") {
            MsgBox "找不到 Sonic Pi 窗口"
            ExitApp
        }

        WinWaitActive("Sonic Pi", , 2)

        Send "^a"
        Sleep 80
        Send "^c"
        Sleep 120

        ClipWait 1
        buf := A_Clipboard
        isEmpty := (Trim(buf) = "")

        if !isEmpty {
            Send "^{Tab}"
            Sleep 150
        }

        A_Clipboard := code
        Sleep 80

        Send "^a"
        Sleep 60
        Send "^v"
        Sleep 150
        Send "^r"

        ExitApp
        '''
    )

    ahk_file = Path(tempfile.gettempdir()) / "SonicPiSend.ahk"
    ahk_file.write_text(ahk_script, encoding="utf-8")

    subprocess.run([ahk_path, str(ahk_file), str(tmp_code)], check=False)
    log("✅ 已调用 AutoHotkey 脚本尝试在 Sonic Pi 中粘贴并运行代码（Windows）。")


# ===================================================================
# Linux 实现：xdotool + xclip
# ===================================================================
def _send_on_linux(code: str, log: Callable[[str], None]) -> None:
    log("🐧 使用 Linux + xdotool + xclip 方式发送代码到 Sonic Pi。")

    if not shutil.which("xdotool"):
        log("❌ 未找到 xdotool（sudo apt install xdotool）。")
        return

    if not shutil.which("xclip"):
        log("❌ 未找到 xclip（sudo apt install xclip）。")
        return

    proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
    proc.communicate(code.encode("utf-8"))

    script = r'''
    #!/usr/bin/env bash

    xdotool search --name "Sonic Pi" windowactivate

    xdotool key ctrl+a
    sleep 0.05
    xdotool key ctrl+c
    sleep 0.1

    current_buf=$(xclip -selection clipboard -o 2>/dev/null || echo "")
    trimmed=$(echo "$current_buf" | tr -d '[:space:]')

    if [ -n "$trimmed" ]; then
      xdotool key ctrl+Right
      sleep 0.1
    fi

    xdotool key ctrl+a
    sleep 0.05
    xdotool key ctrl+v
    sleep 0.1

    xdotool key ctrl+r
    '''

    subprocess.run(["bash", "-c", script], check=False)
    log("✅ 已调用 xdotool/xclip 尝试在 Sonic Pi 中粘贴并运行代码（Linux）。")
