import time
import win32gui
import win32process
import psutil

# Import EventTypes for the standalone test block
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from src.core.event_bus import EventTypes, EventBus


class WindowMonitor:
    def __init__(self, event_bus):
        self.event_bus = event_bus
        self.last_app_name = None
        self.last_window_title = None

        self.app_name_map = {
            # IDEs & Code Editors
            "Code.exe": "VS Code",
            "pycharm64.exe": "PyCharm",
            "idea64.exe": "IntelliJ IDEA",
            "clion64.exe": "CLion",
            "webstorm64.exe": "WebStorm",
            "rider64.exe": "Rider",
            "devenv.exe": "Visual Studio",
            "sublime_text.exe": "Sublime Text",
            "notepad++.exe": "Notepad++",

            # Browsers
            "chrome.exe": "Google Chrome",
            "firefox.exe": "Firefox",
            "msedge.exe": "Microsoft Edge",
            "brave.exe": "Brave Browser",
            "opera.exe": "Opera",

            # Communication
            "Discord.exe": "Discord",
            "Telegram.exe": "Telegram",
            "WhatsApp.exe": "WhatsApp",
            "Slack.exe": "Slack",
            "Teams.exe": "Microsoft Teams",
            "Zoom.exe": "Zoom",

            # AI Tools
            "ChatGPT.exe": "ChatGPT",
            "Claude.exe": "Claude",
            "Cursor.exe": "Cursor",

            # Media & Entertainment
            "spotify.exe": "Spotify",
            "vlc.exe": "VLC Media Player",
            "obs64.exe": "OBS Studio",
            "Steam.exe": "Steam",

            # Productivity
            "WINWORD.EXE": "Microsoft Word",
            "EXCEL.EXE": "Microsoft Excel",
            "POWERPNT.EXE": "PowerPoint",
            "OneNote.exe": "OneNote",
            "notion.exe": "Notion",
            "Obsidian.exe": "Obsidian",

            # Development Tools
            "WindowsTerminal.exe": "Windows Terminal",
            "cmd.exe": "Command Prompt",
            "powershell.exe": "PowerShell",
            "gitkraken.exe": "GitKraken",
            "githubdesktop.exe": "GitHub Desktop",
            "Postman.exe": "Postman",
            "Docker Desktop.exe": "Docker Desktop",

            # File Management
            "explorer.exe": "File Explorer",
            "Everything.exe": "Everything Search",

            # Design & Creative
            "Photoshop.exe": "Adobe Photoshop",
            "Illustrator.exe": "Adobe Illustrator",
            "Figma.exe": "Figma",

            # Misc
            "Taskmgr.exe": "Task Manager",
            "CalculatorApp.exe": "Calculator"
        }

        # Categories for Temporal Logic and Timeline Stability mapping
        self.app_categories = {
            # IDEs & Code Editors
            "VS Code": "coding",
            "PyCharm": "coding",
            "IntelliJ IDEA": "coding",
            "CLion": "coding",
            "WebStorm": "coding",
            "Rider": "coding",
            "Visual Studio": "coding",
            "Sublime Text": "coding",
            "Notepad++": "coding",

            # Browsers
            "Google Chrome": "browser",
            "Firefox": "browser",
            "Microsoft Edge": "browser",
            "Brave Browser": "browser",
            "Opera": "browser",

            # Communication
            "Discord": "communication",
            "Telegram": "communication",
            "WhatsApp": "communication",
            "Slack": "communication",
            "Microsoft Teams": "communication",
            "Zoom": "communication",

            # AI Tools
            "ChatGPT": "ai",
            "Claude": "ai",
            "Cursor": "coding",

            # Media & Entertainment
            "Spotify": "media",
            "VLC Media Player": "media",
            "OBS Studio": "media",
            "Steam": "gaming",

            # Productivity
            "Microsoft Word": "productivity",
            "Microsoft Excel": "productivity",
            "PowerPoint": "productivity",
            "OneNote": "productivity",
            "Notion": "productivity",
            "Obsidian": "productivity",

            # Development Tools
            "Windows Terminal": "terminal",
            "Command Prompt": "terminal",
            "PowerShell": "terminal",
            "GitKraken": "development",
            "GitHub Desktop": "development",
            "Postman": "development",
            "Docker Desktop": "development",

            # File Management
            "File Explorer": "system",
            "Everything Search": "system",

            # Design & Creative
            "Adobe Photoshop": "creative",
            "Adobe Illustrator": "creative",
            "Figma": "creative",

            # Misc
            "Task Manager": "system",
            "Calculator": "utility"
        }

    def get_active_window_info(self):
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                process = psutil.Process(pid)
                raw_app_name = process.name()
                app_name = self.app_name_map.get(raw_app_name, raw_app_name)
                window_title = win32gui.GetWindowText(hwnd)
                app_category = self.app_categories.get(app_name, "unknown")
                return app_name, window_title, app_category
        except (psutil.NoSuchProcess, psutil.AccessDenied, Exception):
            pass
        return None, None, None

    def poll(self):
        app_name, window_title, app_category = self.get_active_window_info()

        if app_name and app_name != self.last_app_name:
            self.last_app_name = app_name
            self.last_window_title = window_title

            # PUBLISH TO EVENT BUS INSTEAD OF PRINTING
            self.event_bus.publish(EventTypes.WINDOW_CHANGED, {
                "app_name": app_name,
                "window_title": window_title,
                "category": app_category
            })

            return app_name, window_title, app_category
        return None, None, None


# Temporary testing block updated to use local EventBus
if __name__ == "__main__":
    test_bus = EventBus()
    test_bus.subscribe(EventTypes.WINDOW_CHANGED, lambda e, p: print(f"[{e}] {p}"))

    monitor = WindowMonitor(test_bus)
    print("Window Monitor running in standalone mode (PubSub). Press Ctrl+C to stop.")
    try:
        while True:
            monitor.poll()
            time.sleep(1)
    except KeyboardInterrupt:
        pass