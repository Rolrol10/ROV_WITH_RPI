import subprocess
import os
import webbrowser
import platform

TYPE = "gui"
ACTIONS = {
    "launch": lambda data: launch_gui()
}

def launch_gui():
    gui_path = os.path.abspath("modules/gui.html")

    # Option 1: Specific Chrome app-style window
    CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    if os.path.exists(CHROME_PATH):
        subprocess.Popen([
            CHROME_PATH,
            "--new-window",
            f"--app=file:///{gui_path.replace(os.sep, '/')}"
        ])
    else:
        # Option 2: fallback to default browser
        print("🌐 Chrome not found, using default browser.")
        webbrowser.open(f"file:///{gui_path}")
