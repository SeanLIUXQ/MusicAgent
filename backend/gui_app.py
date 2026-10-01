"""Compatibility launcher for the browser-native MusicAgent workspace."""

import os
import threading
import webbrowser

from app import app, client


def main() -> None:
    host = os.getenv("MUSICAGENT_HOST", "127.0.0.1")
    port = int(os.getenv("MUSICAGENT_PORT", "5000"))
    url = f"http://{host}:{port}"
    print(f"Opening MusicAgent at {url}")
    print(f"DeepSeek enabled: {client is not None}")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=host, port=port, debug=False, use_reloader=False)


if __name__ == "__main__":
    main()
