import subprocess
import webbrowser
import os

# Your WebRTC stream URL
STREAM_URL = "http://10.253.0.10:8889/cam"

# Path to Chrome/Edge/Brave (modify for your setup)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

def launch_stream_window():
    if os.path.exists(CHROME_PATH):
        subprocess.Popen([
            CHROME_PATH,
            "--new-window",
            "--app=" + STREAM_URL  # Minimal window, no browser UI
        ])
    else:
        # Fallback to default browser if Chrome not found
        webbrowser.open(STREAM_URL)

launch_stream_window()
