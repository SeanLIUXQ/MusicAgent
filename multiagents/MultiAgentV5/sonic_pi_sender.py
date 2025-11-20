"""
sonic_pi_sender.py

把生成的 Sonic Pi 代码自动“送进” Sonic Pi 的 GUI，并执行运行：

- 如果当前 Buffer 为空：在当前 Buffer 粘贴 + Cmd/Ctrl+R 运行
- 如果当前 Buffer 非空：切到“下一个 Buffer”，粘贴 + 运行

实现方式：
- macOS: AppleScript + pbcopy（推荐）
- Windows: AutoHotkey v2（需要手动安装 AHK 并可能调整快捷键）
- Linux: xdotool + xclip（需要安装并可能调整快捷键）

使用方式：
    from sonic_pi_sender import send_code_to_sonic_pi
    send_code_to_sonic_pi("play 60")
"""

from __future__ import annotations

import platform
import subprocess
import textwrap
import shutil
import tempfile
from pathlib import Path
from typing import Callable, Optional


def send_code_to_sonic_pi(
    code: str,
    log_callback: Optional[Callable[[str], None]] = None
) -> None:
    """
    跨平台入口函数：

    - macOS: 使用 AppleScript 控制 Sonic Pi GUI
    - Windows: 使用 AutoHotkey v2（如果已安装）
    - Linux: 使用 xdotool + xclip

    Args:
        code: 完整的 Sonic Pi 代码（Ruby 风格字符串）
        log_callback: 可选日志回调（例如 MultiAgent 里的 log(message)）
    """

    def log(msg: str) -> None:
        if log_callback:
            log_callback(msg)
        else:
            print(msg)

    if not code or not code.strip():
        log("⚠️ 发送到 Sonic Pi 失败：代码为空，跳过发送。\n")
        return

    system = platform.system()
    log(f"🖥 当前平台: {system}\n")

    try:
        if system == "Darwin":
            _send_on_macos(code, log)
        elif system == "Windows":
            _send_on_windows(code, log)
        else:
            _send_on_linux(code, log)
    except Exception as e:
        log(f"❌ 发送到 Sonic Pi 过程中出现异常: {e}\n")


# ====================================================================
# macOS 实现：AppleScript + pbcopy
# ====================================================================

def _send_on_macos(code: str, log: Callable[[str], None]) -> None:
    """
    macOS 下通过 AppleScript 控制 Sonic Pi：

    规则：
    - 如果当前 Buffer 为空：在当前 Buffer 粘贴 + Cmd+R 运行
    - 如果当前 Buffer 非空：切到下一个 Buffer（假定使用 Cmd+Option+右方向键），粘贴 + Cmd+R

    提示：
    - “切到下一个 Buffer”的快捷键你可以在 Sonic Pi 里确认后，修改 AppleScript 中对应那一行。
    """
    log("🍏 使用 macOS AppleScript 方式发送代码到 Sonic Pi。\n")

    # 1) 把代码写入系统剪贴板（pbcopy）
    pbcopy = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    pbcopy.communicate(code.encode("utf-8"))
    log("📋 已将代码写入剪贴板。\n")

    # 2) AppleScript：判断当前 buffer 是否为空 → 决定是否切到下一个 buffer → 粘贴 + 运行
    applescript = textwrap.dedent(
        r'''
        -- 判断当前 Buffer 是否为空
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

        -- 切换到下一个 Buffer（这里假定使用 Cmd+Option+右箭头，你可以按自己实际配置修改）
        on switch_to_next_buffer()
            tell application "System Events"
                if not (exists process "Sonic Pi") then return
                tell process "Sonic Pi"
                    -- ★★ 如需修改“下一个 Buffer”的快捷键，请调整这一行：
                    key code 124 using {command down, option down} -- 124 = 右方向键
                end tell
            end tell
        end switch_to_next_buffer

        -- 在当前 Buffer 中：全选 + 粘贴 + 运行
        on replace_buffer_and_run()
            tell application "System Events"
                if not (exists process "Sonic Pi") then return
                tell process "Sonic Pi"
                    keystroke "a" using {command down}
                    delay 0.05
                    keystroke "v" using {command down}
                    delay 0.1
                    -- 默认 Run 是 Cmd+R，如有改动，请修改下一行
                    keystroke "r" using {command down}
                end tell
            end tell
        end replace_buffer_and_run

        on run
            -- 激活 Sonic Pi
            tell application "Sonic Pi"
                activate
            end tell
            delay 0.4

            tell application "System Events"
                if not (exists process "Sonic Pi") then return
            end tell

            -- 检查当前 Buffer 是否为空
            set isEmpty to my is_current_buffer_empty()

            if isEmpty then
                -- 当前 Buffer 为空：直接粘贴 + 运行
                my replace_buffer_and_run()
            else
                -- 当前 Buffer 非空：切换到下一个 Buffer 后粘贴 + 运行
                my switch_to_next_buffer()
                delay 0.2
                my replace_buffer_and_run()
            end if
        end run
        '''
    )

    # 3) 调用 osascript 执行上述 AppleScript
    result = subprocess.run(
        ["osascript", "-e", applescript],
        capture_output=True,
        text=True
    )

    if result.returncode == 0:
        log("✅ 已通过 GUI 将代码粘贴到 Sonic Pi 并尝试自动运行（macOS）。\n")
    else:
        log(f"❌ AppleScript 执行失败（macOS）：{result.stderr}\n")


# ====================================================================
# Windows 实现：AutoHotkey v2（需要用户安装）
# ====================================================================

def _send_on_windows(code: str, log: Callable[[str], None]) -> None:
    """
    Windows 下通过 AutoHotkey v2 控制 Sonic Pi:

    依赖：
    - 安装 AutoHotkey v2
    - ahk.exe 或 AutoHotkey.exe 在 PATH 中

    行为：
    - 激活标题含 “Sonic Pi” 的窗口
    - Ctrl+A + Ctrl+C 读取当前缓冲区内容，判断是否为空
    - 非空则切换到“下一个 Buffer”（需要你修改对应快捷键）
    - Ctrl+A + Ctrl+V 粘贴传入的 code
    - Ctrl+R 运行（如你有自定义，需修改脚本）
    """
    log("🪟 使用 Windows + AutoHotkey 方式发送代码到 Sonic Pi。\n")

    ahk_path = shutil.which("ahk.exe") or shutil.which("AutoHotkey.exe")
    if not ahk_path:
        log("❌ 未找到 AutoHotkey (ahk.exe / AutoHotkey.exe)，请安装 AutoHotkey v2 并加入 PATH。\n")
        return

    # 将代码写入临时文件，传给 AHK
    tmp_code = Path(tempfile.gettempdir()) / "sonic_pi_code.rb"
    tmp_code.write_text(code, encoding="utf-8")

    ahk_script = textwrap.dedent(
        r'''
        ; SonicPiSend.ahk (AutoHotkey v2)
        ; 参数 1：代码文件路径

        #SingleInstance Force

        codeFile := A_Args[1]
        code := FileRead(codeFile, "UTF-8")

        ; 激活 Sonic Pi 窗口（标题按你实际情况调整）
        if !WinActivate("Sonic Pi") {
            MsgBox "找不到 Sonic Pi 窗口"
            ExitApp
        }

        WinWaitActive("Sonic Pi", , 2)

        ; 复制当前 buffer 内容
        Send "^a"
        Sleep 80
        Send "^c"
        Sleep 120

        ClipWait 1
        buf := A_Clipboard
        isEmpty := (Trim(buf) = "")

        if !isEmpty {
            ; ★★ TODO: 修改为你系统的“下一个 buffer”快捷键：
            ; 下面是示例，假设 Alt+Right 为下一 Buffer
            Send "^{Tab}"
            Sleep 150
        }

        ; 将生成的代码放到剪贴板
        A_Clipboard := code
        Sleep 80

        ; 粘贴 + 运行
        Send "^a"
        Sleep 60
        Send "^v"
        Sleep 150
        ; ★★ 默认 Sonic Pi Run 为 Ctrl+R，如有不同请改这里
        Send "^r"

        ExitApp
        '''
    )

    ahk_file = Path(tempfile.gettempdir()) / "SonicPiSend.ahk"
    ahk_file.write_text(ahk_script, encoding="utf-8")

    subprocess.run([ahk_path, str(ahk_file), str(tmp_code)], check=False)
    log("✅ 已调用 AutoHotkey 脚本尝试在 Sonic Pi 中粘贴并运行代码（Windows）。\n")


# ====================================================================
# Linux 实现：xdotool + xclip
# ====================================================================

def _send_on_linux(code: str, log: Callable[[str], None]) -> None:
    """
    Linux 下通过 xdotool + xclip 控制 Sonic Pi：

    依赖：
    - xdotool
    - xclip

    行为：
    - 激活标题含 “Sonic Pi” 的窗口
    - Ctrl+A + Ctrl+C 复制当前 buffer，使用 xclip 读取文本判断是否为空
    - 非空则按“下一个 buffer”快捷键（需要你自行修改）
    - Ctrl+A + Ctrl+V 粘贴新代码
    - Ctrl+R 运行（如你自定义快捷键需修改）
    """
    log("🐧 使用 Linux + xdotool + xclip 方式发送代码到 Sonic Pi。\n")

    if not shutil.which("xdotool"):
        log("❌ 未找到 xdotool（请安装：sudo apt install xdotool）。\n")
        return
    if not shutil.which("xclip"):
        log("❌ 未找到 xclip（请安装：sudo apt install xclip）。\n")
        return

    # 将代码写入剪贴板
    proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
    proc.communicate(code.encode("utf-8"))

    # Bash 脚本：判断当前 buffer 是否为空 → 决定是否切 buffer → 粘贴 + Run
    script = r'''
    #!/usr/bin/env bash

    # 激活 Sonic Pi 窗口（标题匹配可按需修改）
    xdotool search --name "Sonic Pi" windowactivate

    # 复制当前 buffer 内容
    xdotool key ctrl+a
    sleep 0.05
    xdotool key ctrl+c
    sleep 0.1

    current_buf=$(xclip -selection clipboard -o 2>/dev/null || echo "")
    trimmed=$(echo "$current_buf" | tr -d '[:space:]')

    if [ -n "$trimmed" ]; then
      # ★★ TODO: 修改为你的“下一个 buffer”快捷键：
      # 例如：ctrl+Right
      xdotool key ctrl+Right
      sleep 0.1
    fi

    # 现在剪贴板里是我们从 Python 写入的 Sonic Pi 代码
    xdotool key ctrl+a
    sleep 0.05
    xdotool key ctrl+v
    sleep 0.1

    # ★★ 默认假定 Run 为 ctrl+r，如有不同请修改：
    xdotool key ctrl+r
    '''

    subprocess.run(["bash", "-c", script], check=False)
    log("✅ 已调用 xdotool/xclip 尝试在 Sonic Pi 中粘贴并运行代码（Linux）。\n")