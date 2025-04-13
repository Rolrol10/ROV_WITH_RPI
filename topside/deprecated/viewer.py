import subprocess
CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
subprocess.Popen([
    CHROME_PATH,
    "--new-window",
    "--app=file:///C:/Users/Rolfk/Nextcloud/Python/ROV/modules/viewer.html"
])
