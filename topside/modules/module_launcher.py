# modules/module_launcher.py

import tkinter as tk
import asyncio
import threading

# These will be passed from rov_topside
queue_ref = None
main_loop = None

# Button configuration: label -> (command, optional stop_command)
BUTTONS = {
    "Input_controllers": ("start_input_controllers", "stop_input_controllers"),
    "Image Processor": ("start_image", "stop_image"),
    "GUI (Browser)": ("start_gui", None),
    "Quit All": ("quit", None),
}

def send_command(command):
    if queue_ref and main_loop:
        asyncio.run_coroutine_threadsafe(queue_ref.put(command), main_loop)

# GUI setup function
def launch_ui(command_queue, loop):
    global queue_ref, main_loop
    queue_ref = command_queue
    main_loop = loop

    def build():
        root = tk.Tk()
        root.title("ROV Module Launcher")
        root.geometry("360x220")
        root.resizable(False, False)

        row = 0
        for label, (start_cmd, stop_cmd) in BUTTONS.items():
            tk.Label(root, text=label, font=("Arial", 10)).grid(row=row, column=0, sticky="w", padx=10, pady=5)
            if start_cmd:
                btn_text = "Quit" if label == "Quit All" else "Start"
                tk.Button(root, text=btn_text, width=10, command=lambda c=start_cmd: send_command(c)).grid(row=row, column=1, padx=5)

            if stop_cmd:
                tk.Button(root, text="Stop", width=10, command=lambda c=stop_cmd: send_command(c)).grid(row=row, column=2, padx=5)

            row += 1

        root.mainloop()

    threading.Thread(target=build, daemon=True).start()
