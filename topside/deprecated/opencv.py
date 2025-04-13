import subprocess
import os

# --- CONFIG ---
STREAM_URL = "http://10.253.0.10:8889/cam"

# Path to Chrome executable (adjust if needed)
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"

# --- Launch Chrome in app mode ---
def launch_stream():
    if not os.path.exists(CHROME_PATH):
        print("❌ Chrome not found. Please update the path.")
        return

    subprocess.Popen([
        CHROME_PATH,
        f"--app={STREAM_URL}",
        "--autoplay-policy=no-user-gesture-required",
        "--disable-web-security",           # Optional for CORS issues
        "--use-fake-ui-for-media-stream"    # Optional for auto permission
    ])

if __name__ == "__main__":
    launch_stream()
