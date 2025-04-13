from ruamel.yaml import YAML
import subprocess
import time
import os
import signal

# --- Module type ---

TYPE = "stream"

# --- CONFIG ---
MODULE_DIR = os.path.dirname(__file__)
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CONFIG_PATH = os.path.join(BASE_DIR, "video", "mediamtx.yml")
MEDIAMTX_EXEC = os.path.join(BASE_DIR, "video", "mediamtx")
mediamtx_proc = None

# Settings to apply
default_settings = {
    "rpiCameraMode": "1640:1232:8", # Sensor mode, in format [width]:[height]:[bit-depth]:[packing]
    "rpiCameraWidth": 360,          # Width of frames
    "rpiCameraHeight": 240,         # Height of frames
    "rpiCameraFPS": 30,             # frames per second
    "rpiCameraBitrate": 500000,     # Bitrate
    "rpiCameraIDRPeriod": 60,       # Period between IDR frames
    "rpiCameraVFlip": False,        # Flip vertically
    "rpiCameraHFlip": False,        # Flip horizontally
    "rpiCameraBrightness": 0,       # Brightness [-1, 1]
    "rpiCameraContrast": 1,         # Contrast [0, 16]
    "rpiCameraSaturation": 1,       # Saturation [0, 16]
    "rpiCameraSharpness": 1,        # Sharpness [0, 16]
    "rpiCameraExposure": "normal",  # Exposure mode. values: normal, short, long, custom
    "rpiCameraAWB": "auto",         # Auto-white-balance mode. values: auto, incandescent, tungsten, fluorescent, indoor, daylight, cloudy, custom
    "rpiCameraDenoise": "off",      # Denoise operating mode. values: off, cdn_off, cdn_fast, cdn_hq
    "rpiCameraMetering": "centre",  # Metering mode of the AEC/AGC algorithm. values: centre, spot, matrix, custom
    "rpiCameraShutter": 0,          # Fixed shutter speed, in microseconds.
    "rpiCameraGain": 0,             # Fixed gain
    "rpiCameraAfMode": "continuous"# Autofocus mode. values: auto, manual, continuous
}

class MediaMTXManager:
    def __init__(self, exec_path, config_path):
        self.exec_path = exec_path
        self.config_path = config_path
        self.process = None

    def start_mediamtx(self, data):
        if self.process is None:
            print("Starting MediaMTX...")
            self.process = subprocess.Popen([self.exec_path, self.config_path])#,
                         #stdout=subprocess.DEVNULL,
                         #stderr=subprocess.DEVNULL)
            print("MediaMTX Started.")
        else:
            print("⚠️ MediaMTX is already running.")

    def stop_mediamtx(self, data):
        if self.process is not None:
            print("🛑 Stopping MediaMTX...")
            self.process.send_signal(signal.SIGINT)  # Graceful shutdown
            try:
                self.process.wait(timeout=5)  # Wait up to 5 seconds
            except subprocess.TimeoutExpired:
                print("⚠️ MediaMTX did not shut down, forcing termination...")
                self.process.kill()
            self.process = None
            print("✅ MediaMTX stopped.")
        else:
            print("⚠️ MediaMTX is not running.")

    def restart_mediamtx(self, data):
        self.stop_mediamtx(data)
        self.start_mediamtx(data)

    def is_running(self):
        return self.process is not None and self.process.poll() is None


    def apply_default_setting(self, ):
        yaml = YAML()
        yaml.preserve_quotes = True

        with open(CONFIG_PATH, "r") as f:
            config = yaml.load(f)

        if "paths" in config and "cam" in config["paths"]:
            for key, value in default_settings.items():
                config["paths"]["cam"][key] = value
            with open(CONFIG_PATH, "w") as f:
                yaml.dump(config, f)
            print("✅ Config updated.")
        else:
            print("⚠️ 'cam' path not found in config!")

# --- Handle WebSocket Command ---
    def change_settings(self, data):

        print("🎛️ Updating MediaMTX stream settings...")

        # Extract and sanitize user-defined settings
        new_settings = {}
        allowed_keys = {
            "rpiCameraMode",
            "rpiCameraWidth",
            "rpiCameraHeight",
            "rpiCameraFPS",
            "rpiCameraBitrate",
            "rpiCameraIDRPeriod",
            "rpiCameraVFlip",
            "rpiCameraHFlip",
            "rpiCameraBrightness",
            "rpiCameraContrast",
            "rpiCameraSaturation",
            "rpiCameraSharpness",
            "rpiCameraExposure",
            "rpiCameraAWB",
            "rpiCameraDenoise",
            "rpiCameraMetering",
            "rpiCameraShutter",
            "rpiCameraGain",
            "rpiCameraAfMode"
        }

        for key in allowed_keys:
            if key in data:
                new_settings[key] = data[key]

        # Load and update YAML config
        yaml = YAML()
        yaml.preserve_quotes = True

        try:
            with open(CONFIG_PATH, "r") as f:
                config = yaml.load(f)

            if "paths" in config and "cam" in config["paths"]:
                for key, value in new_settings.items():
                    config["paths"]["cam"][key] = value

                with open(CONFIG_PATH, "w") as f:
                    yaml.dump(config, f)

                print("✅ Camera config updated.")
            else:
                print("⚠️ Couldn't find 'cam' path in config.")

        except Exception as e:
            print(f"❌ Failed to update config: {e}")

stream_manager = MediaMTXManager(MEDIAMTX_EXEC, CONFIG_PATH)

ACTIONS = {
    "start_stream": stream_manager.start_mediamtx,
    "restart_stream": stream_manager.restart_mediamtx,
    "stop_stream": stream_manager.stop_mediamtx,
    "default_settings": stream_manager.apply_default_setting,
    "change_settings": stream_manager.change_settings,
    "check_stream": stream_manager.is_running
}