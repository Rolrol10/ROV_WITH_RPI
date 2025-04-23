import subprocess
import os
import platform
import webbrowser

TYPE = "gui"
ACTIONS = {
    "launch": lambda data: launch_gui()
}

def launch_gui(return_process=False):
    # New folder structure: HTML and Electron are in topside/gui/
    gui_index = os.path.abspath("topside/gui/gui.html").replace(os.sep, "/")
    url = f"file:///{gui_index}"

    # Optional: still allow launching HTML directly in a browser
    system = platform.system()
    OPERA_PATH = r"C:\Users\Rolfk\AppData\Local\Programs\Opera\opera.exe"

    # 🔁 Option 1: Preferred – Launch Electron GUI
    electron_launcher = os.path.abspath("topside/gui/electron")
    # print(electron_launcher)
    if os.path.exists(os.path.join(electron_launcher, "package.json")):
        print("🚀 Launching Electron GUI...")
        try:
            proc = subprocess.Popen(["npm.cmd", "start"], cwd=electron_launcher)
            # subprocess.Popen(["npm.cmd", "start"], cwd=electron_launcher)
            # return
            if return_process:
                return proc
            return None
        except FileNotFoundError:
            print("❌ npm not found. Make sure Node.js is installed and in PATH.")
        except Exception as e:
            print(f"❌ Failed to launch Electron GUI: {e}")

    # 🔁 Option 2: Fallback to Opera or default browser
    if system == "Windows" and os.path.exists(OPERA_PATH):
        print("🌐 Launching GUI in Opera...")
        subprocess.Popen([OPERA_PATH, "--new-window", url])
    else:
        print("🌐 Opera not found, opening GUI in default browser.")
        webbrowser.open(url)
