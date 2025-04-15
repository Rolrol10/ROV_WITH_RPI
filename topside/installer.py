# install_requirements.py

import subprocess
import sys
import importlib.util

def parse_requirements(file_path):
    modules = []
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                module = line.split("==")[0]  # Get just the module name
                modules.append(module)
    return modules

def is_module_installed(module_name):
    return importlib.util.find_spec(module_name) is not None

def install_requirements():
    print("📦 Installing from requirements.txt...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "topside/requirements.txt"])

def main():
    required_modules = parse_requirements("topside/requirements.txt")
    missing = [m for m in required_modules if not is_module_installed(m)]
    if missing:
        print(f"⚠️ Missing modules: {', '.join(missing)}")
        install_requirements()
    else:
        print("✅ All required modules are already installed.")

if __name__ == "__main__":
    main()
