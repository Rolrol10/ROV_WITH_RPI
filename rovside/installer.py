# install_requirements.py
# Auto-creates a local venv (.venv), re-execs inside it, then installs requirements.
import os
import sys
import subprocess
from pathlib import Path

try:
    import venv
except Exception as e:
    print("❌ Python's 'venv' module is unavailable.\n"
          "   On Raspberry Pi OS run: sudo apt install -y python3-venv\n"
          f"Details: {e}")
    sys.exit(1)

ROOT = Path(__file__).resolve().parents[1]  # project root (…/ROV_WITH_RPI)
VENV = ROOT / ".venv"
REQS = ROOT / "rovside" / "requirements.txt"

def in_venv() -> bool:
    # Works for Python 3.8+
    return (hasattr(sys, "real_prefix") or
            (hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix) or
            os.environ.get("VIRTUAL_ENV"))

def ensure_venv():
    if VENV.exists():
        return
    print(f"📦 Creating virtual environment at {VENV} …")
    venv.EnvBuilder(with_pip=True, clear=False, upgrade=False).create(str(VENV))

def reexec_in_venv():
    py = VENV / "bin" / "python"
    if not py.exists():
        print("❌ venv python not found after creation. Aborting.")
        sys.exit(1)
    print("🔁 Re-running installer inside the virtual environment …")
    os.execv(str(py), [str(py), __file__])

def pip(args):
    cmd = [sys.executable, "-m", "pip"] + args
    subprocess.check_call(cmd)

def install_requirements():
    if not REQS.exists():
        print(f"❌ requirements.txt not found at: {REQS}")
        sys.exit(1)

    print("📦 Upgrading pip/setuptools/wheel …")
    pip(["install", "-U", "pip", "setuptools", "wheel"])

    print(f"📦 Installing from {REQS} …")
    # No --break-system-packages; we're in a venv so it's clean
    pip(["install", "-r", str(REQS)])

def main():
    # If we're not inside the venv yet, create it and re-exec inside.
    if not in_venv():
        ensure_venv()
        reexec_in_venv()
        return

    # Inside venv now
    try:
        install_requirements()
        print("\n✅ Done.")
        print(f"👉 To use it next time:\n"
              f"   source {VENV}/bin/activate\n"
              f"   python your_entrypoint.py\n")
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Command failed: {' '.join(e.cmd)}\nExit code: {e.returncode}")
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
