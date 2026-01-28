import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import os
import sys
import threading
import time
import signal
import json

class MaungApp:
    def __init__(self, root):
        self.root = root
        self.root.title("LaraVue-Station Dev Environment Controller")
        self.root.geometry("600x450")
        self.root.configure(bg="#f0f0f0")

        # --- Configuration ---
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.bin_dir = os.path.join(self.base_dir, "bin")
        self.app_dir = os.path.join(self.base_dir, "app")
        self.config = self.load_config()
        self.apache_port = self.config.get("apache", {}).get("port", 8080)
        
        # Paths to executables (Adjust these if your folder names differ)
        self.paths = {
            "apache2": os.path.join(self.bin_dir, "apache", "bin", "httpd.exe"),
            "mysql": os.path.join(self.bin_dir, "mysql-9.4.0-winx64", "bin", "mysqld.exe"),
            "php": os.path.join(self.bin_dir, "php", "php.exe")
        }
        self.mysql_defaults = os.path.join(self.bin_dir, "mysql-9.4.0-winx64", "my.ini")

        self.processes = {}
        self.is_running = False

        # --- UI Layout ---
        header = tk.Label(root, text="Dev Environment Controller", font=("Segoe UI", 16, "bold"), bg="#f0f0f0")
        header.pack(pady=10)

        btn_frame = tk.Frame(root, bg="#f0f0f0")
        btn_frame.pack(pady=10)

        self.btn_start = tk.Button(btn_frame, text="START ALL", command=self.start_all, 
                                   bg="#28a745", fg="white", font=("Segoe UI", 10, "bold"), width=15, height=2)
        self.btn_start.pack(side=tk.LEFT, padx=10)

        self.btn_stop = tk.Button(btn_frame, text="STOP ALL", command=self.stop_all, 
                                  bg="#dc3545", fg="white", font=("Segoe UI", 10, "bold"), width=15, height=2, state=tk.DISABLED)
        self.btn_stop.pack(side=tk.LEFT, padx=10)

        self.btn_clear_port = tk.Button(btn_frame, text="CLEAR PORT", command=self.clear_apache_port,
                                        bg="#ff9800", fg="white", font=("Segoe UI", 10, "bold"), width=15, height=2)
        self.btn_clear_port.pack(side=tk.LEFT, padx=10)

        self.btn_settings = tk.Button(btn_frame, text="SETTINGS", command=self.open_settings,
                                      bg="#007bff", fg="white", font=("Segoe UI", 10, "bold"), width=15, height=2)
        self.btn_settings.pack(side=tk.LEFT, padx=10)

        # Status Indicators
        self.status_labels = {}
        status_frame = tk.Frame(root, bg="#f0f0f0")
        status_frame.pack(pady=5)
        
        for service in ["Apache2", "MySQL", "PHP"]:
            lbl = tk.Label(status_frame, text=f"{service}: OFF", fg="gray", bg="#f0f0f0", font=("Consolas", 10))
            lbl.pack(side=tk.LEFT, padx=15)
            self.status_labels[service] = lbl

        # Log Window
        tk.Label(root, text="Process Logs:", bg="#f0f0f0").pack(anchor="w", padx=10)
        self.log_area = scrolledtext.ScrolledText(root, height=12, state='disabled', font=("Consolas", 9))
        self.log_area.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)

        # Handle Close Window
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def load_config(self):
        """Loads config.json if present; returns empty dict on failure."""
        config_path = os.path.join(self.base_dir, "config.json")
        if not os.path.exists(config_path):
            return {}
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            if hasattr(self, "log_area"):
                self.log(f"[Config] ERROR: {str(e)}")
            else:
                print(f"[Config] ERROR: {str(e)}")
            return {}

    def save_config(self):
        config_path = os.path.join(self.base_dir, "config.json")
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
            self.log("[Config] Saved config.json")
        except Exception as e:
            self.log(f"[Config] ERROR: {str(e)}")

    def open_settings(self):
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("420x300")
        win.configure(bg="#f0f0f0")
        win.transient(self.root)
        win.grab_set()

        def add_row(parent, label_text, default_value, row):
            tk.Label(parent, text=label_text, bg="#f0f0f0").grid(row=row, column=0, sticky="w", padx=10, pady=6)
            entry = tk.Entry(parent, width=30)
            entry.insert(0, str(default_value))
            entry.grid(row=row, column=1, padx=10, pady=6)
            return entry

        frame = tk.Frame(win, bg="#f0f0f0")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        apache_cfg = self.config.get("apache", {})
        mysql_cfg = self.config.get("mysql", {})

        entry_apache_port = add_row(frame, "Apache Port", apache_cfg.get("port", 8080), 0)
        entry_apache_conf = add_row(frame, "Apache Conf Path", apache_cfg.get("conf", ""), 1)
        entry_mysql_port = add_row(frame, "MySQL Port", mysql_cfg.get("port", 3306), 2)
        entry_mysql_user = add_row(frame, "MySQL User", mysql_cfg.get("user", "root"), 3)
        entry_mysql_pass = add_row(frame, "MySQL Password", mysql_cfg.get("password", ""), 4)

        btn_row = tk.Frame(win, bg="#f0f0f0")
        btn_row.pack(pady=10)

        def on_save():
            try:
                apache_port = int(entry_apache_port.get().strip())
                mysql_port = int(entry_mysql_port.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Input", "Ports must be numbers.")
                return

            self.config["apache"] = {
                "port": apache_port,
                "conf": entry_apache_conf.get().strip()
            }
            self.config["mysql"] = {
                "port": mysql_port,
                "user": entry_mysql_user.get().strip(),
                "password": entry_mysql_pass.get().strip()
            }
            self.apache_port = apache_port
            self.save_config()
            self.log("[Config] Settings updated. Restart services to apply.")
            win.destroy()

        def on_cancel():
            win.destroy()

        tk.Button(btn_row, text="SAVE", command=on_save, bg="#28a745", fg="white", width=12).pack(side=tk.LEFT, padx=8)
        tk.Button(btn_row, text="CANCEL", command=on_cancel, bg="#6c757d", fg="white", width=12).pack(side=tk.LEFT, padx=8)

    def log(self, message):
        """Thread-safe logging to the text area"""
        self.log_area.config(state='normal')
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)
        self.log_area.config(state='disabled')

    def set_status(self, service, status):
        color = "#28a745" if status == "RUNNING" else "gray"
        self.status_labels[service].config(text=f"{service}: {status}", fg=color)

    def start_service(self, name, cmd_args, cwd):
        """Starts a generic service subprocess"""
        try:
            # CREATE_NO_WINDOW prevents extra console windows popping up
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            
            proc = subprocess.Popen(
                cmd_args, 
                cwd=cwd,
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags
            )
            self.processes[name] = proc
            self.set_status(name, "RUNNING")
            self.log(f"[{name}] Started with PID {proc.pid}")
            
            # Start a thread to read logs
            threading.Thread(target=self.read_output, args=(proc, name), daemon=True).start()
            
        except FileNotFoundError:
            self.log(f"[{name}] ERROR: Executable not found at {cmd_args[0]}")
        except Exception as e:
            self.log(f"[{name}] ERROR: {str(e)}")

    def run_once(self, name, cmd_args, cwd):
        """Runs a one-off command and logs output"""
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            result = subprocess.run(
                cmd_args,
                cwd=cwd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=creationflags
            )
            output = result.stdout.strip() or result.stderr.strip()
            if output:
                self.log(f"[{name}] {output}")
        except FileNotFoundError:
            self.log(f"[{name}] ERROR: Executable not found at {cmd_args[0]}")
        except Exception as e:
            self.log(f"[{name}] ERROR: {str(e)}")

    def read_output(self, proc, name):
        """Reads stdout/stderr from subprocess"""
        while True:
            line = proc.stdout.readline()
            if not line and proc.poll() is not None:
                break
            if line:
                self.log(f"[{name}] {line.strip()}")
            # Also check stderr
            err = proc.stderr.readline()
            if err:
                self.log(f"[{name}] {err.strip()}")

    def start_all(self):
        if self.is_running:
            return

        self.log("--- Starting Stack ---")
        
        # 0. Check PHP
        if os.path.exists(self.paths['php']):
            self.run_once("PHP", [self.paths['php'], "-v"], os.path.dirname(self.paths['php']))
            self.set_status("PHP", "RUNNING")
        else:
            self.log("[PHP] Binary not found. Check path.")

        # 1. Start MySQL
        # Note: MySQL needs the console flag to output logs to stdout
        if os.path.exists(self.paths['mysql']):
            mysql_args = [self.paths['mysql'], "--console"]
            if os.path.exists(self.mysql_defaults):
                mysql_args.append(f"--defaults-file={self.mysql_defaults}")
            self.start_service("MySQL", mysql_args, os.path.dirname(self.paths['mysql']))
        else:
            self.log("[MySQL] Binary not found. Check path.")

        # 2. Start Apache
        # Note: Apache needs PHP configured in httpd.conf before starting
        if os.path.exists(self.paths['apache2']):
            self.start_service("Apache2", [self.paths['apache2']], os.path.dirname(self.paths['apache2']))
        else:
            self.log("[Apache2] Binary not found. Check path.")

        self.is_running = True
        self.btn_start.config(state=tk.DISABLED)
        self.btn_stop.config(state=tk.NORMAL)

    def stop_all(self):
        self.log("--- Stopping Stack ---")
        for name, proc in self.processes.items():
            if proc.poll() is None: # If still running
                self.log(f"[{name}] Terminating...")
                proc.terminate() # Try graceful termination first
                try:
                    proc.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    proc.kill() # Force kill if stuck
                self.set_status(name, "OFF")
        
        self.processes.clear()
        self.is_running = False
        for service in ["Apache2", "MySQL", "PHP"]:
            self.set_status(service, "OFF")
        self.btn_start.config(state=tk.NORMAL)
        self.btn_stop.config(state=tk.DISABLED)

    def clear_apache_port(self):
        """Kills any process listening on the configured Apache port."""
        if sys.platform != "win32":
            self.log("[Clear Port] Not supported on this OS.")
            return

        port = int(self.apache_port)
        self.log(f"[Clear Port] Checking port {port}...")

        try:
            result = subprocess.run(
                ["netstat", "-ano"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            lines = result.stdout.splitlines()
            pids = set()
            token = f":{port}"
            for line in lines:
                if token in line and "LISTENING" in line:
                    parts = line.split()
                    if parts:
                        pids.add(parts[-1])

            if not pids:
                self.log(f"[Clear Port] No process is listening on port {port}.")
                return

            for pid in pids:
                self.log(f"[Clear Port] Killing PID {pid} on port {port}...")
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

            self.log(f"[Clear Port] Port {port} cleared.")
        except Exception as e:
            self.log(f"[Clear Port] ERROR: {str(e)}")

    def on_close(self):
        if self.is_running:
            if tk.messagebox.askokcancel("Quit", "Services are running. Stop them and quit?"):
                self.stop_all()
                self.root.destroy()
        else:
            self.root.destroy()

if __name__ == "__main__":
    # Optional: Verify Python environment or install requirements
    root = tk.Tk()
    app = MaungApp(root)
    root.mainloop()
