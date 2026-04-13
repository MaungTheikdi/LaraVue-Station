"""
DevStation — Portable Local Development Environment Controller
"""

from __future__ import annotations

import json
import logging
import os
import re
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, scrolledtext
import tkinter as tk


# ── Portable base resolution ──────────────────────────────────────────────────
# Works identically whether run as `python theikdi_maung.py` or as a frozen EXE.
BASE: Path = (
    Path(sys.executable).parent if getattr(sys, "frozen", False)
    else Path(__file__).parent
)

# ── App constants ─────────────────────────────────────────────────────────────
APP_NAME    = "DevStation"
APP_VERSION = "1.0.0"
LOG_FILE    = BASE / "devstation.log"


# ── File + console logger (survives frozen EXE) ───────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
_log = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────
def _fwd(p: object) -> str:
    """Return path string with forward slashes (Apache/MySQL friendly)."""
    return str(p).replace("\\", "/")


def _deep_merge(base: dict, override: dict) -> dict:
    """Return a new dict: override wins for existing keys, base fills missing ones."""
    result = dict(base)
    for k, v in override.items():
        if k in result and isinstance(result[k], dict) and isinstance(v, dict):
            result[k] = _deep_merge(result[k], v)
        else:
            result[k] = v
    return result


# ── Default config (all paths derived from BASE at import time) ───────────────
DEFAULTS: dict = {
    "base": _fwd(BASE),
    "apache": {
        "port": 8080,
        "bin":  _fwd(BASE / "bin/apache/bin/httpd.exe"),
        "conf": _fwd(BASE / "bin/apache/conf/httpd.conf"),
    },
    "mysql": {
        "port":     3306,
        "user":     "root",
        "password": "password",
        "bin":      _fwd(BASE / "bin/mysql-9.4.0-winx64/bin/mysqld.exe"),
        "defaults": _fwd(BASE / "bin/mysql-9.4.0-winx64/my.ini"),
    },
    "php": {
        "bin": _fwd(BASE / "bin/php/php.exe"),
    },
    "www": _fwd(BASE / "www"),
}


# ── Main application ──────────────────────────────────────────────────────────
class DevStation:

    # Catppuccin Mocha palette
    C = {
        "bg":      "#1e1e2e",
        "surface": "#313244",
        "overlay": "#45475a",
        "text":    "#cdd6f4",
        "subtext": "#a6adc8",
        "muted":   "#6c7086",
        "green":   "#a6e3a1",
        "red":     "#f38ba8",
        "yellow":  "#f9e2af",
        "blue":    "#89b4fa",
        "mauve":   "#cba6f7",
        "peach":   "#fab387",
        "teal":    "#94e2d5",
        "sky":     "#89dceb",
    }

    def __init__(self, root: tk.Tk) -> None:
        self.root      = root
        self.processes: dict[str, subprocess.Popen] = {}
        self.config:    dict                        = {}

        self._init_config()
        self._build_ui()
        self._start_monitor()

        self.root.title(f"{APP_NAME}  {APP_VERSION}")
        self.root.geometry("720x560")
        self.root.configure(bg=self.C["bg"])
        self.root.resizable(True, True)
        self.root.minsize(680, 480)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        _log.info("DevStation started  BASE=%s", BASE)
        self._emit(f"{APP_NAME} {APP_VERSION}  |  {BASE}", "info")

    # ── Config ────────────────────────────────────────────────────────────────

    def _cfg_path(self) -> Path:
        return BASE / "config.json"

    def _init_config(self) -> None:
        """
        Load config.json (creating it from defaults if absent).
        If the folder has been moved to a new location since the last run,
        automatically rewrite httpd.conf and my.ini with the new base path.
        """
        path = self._cfg_path()
        raw: dict = {}
        if path.exists():
            try:
                raw = json.loads(path.read_text(encoding="utf-8"))
            except Exception as exc:
                _log.warning("config.json unreadable (%s) — rebuilding defaults.", exc)

        self.config = _deep_merge(DEFAULTS, raw)

        old_base = _fwd(self.config.get("base", BASE))
        new_base = _fwd(BASE)

        if old_base != new_base:
            _log.info("Base moved  %s → %s — rewriting service configs.", old_base, new_base)
            self._patch_httpd(old_base, new_base)
            self._patch_myini(new_base)
            # Refresh all stored paths to the new location
            self.config.update({
                "base": new_base,
                "www":  _fwd(BASE / "www"),
            })
            self.config["apache"].update({
                "bin":  _fwd(BASE / "bin/apache/bin/httpd.exe"),
                "conf": _fwd(BASE / "bin/apache/conf/httpd.conf"),
            })
            self.config["mysql"].update({
                "bin":      _fwd(BASE / "bin/mysql-9.4.0-winx64/bin/mysqld.exe"),
                "defaults": _fwd(BASE / "bin/mysql-9.4.0-winx64/my.ini"),
            })
            self.config["php"]["bin"] = _fwd(BASE / "bin/php/php.exe")

        self.config["base"] = new_base
        self._save_config()

    def _save_config(self) -> None:
        try:
            self._cfg_path().write_text(
                json.dumps(self.config, indent=4), encoding="utf-8"
            )
        except Exception as exc:
            _log.error("Failed to save config.json: %s", exc)

    def _patch_httpd(self, old: str, new: str) -> None:
        """Replace every occurrence of old base path with new base in httpd.conf."""
        p = Path(self.config["apache"]["conf"])
        if not p.exists():
            return
        try:
            p.write_text(p.read_text(encoding="utf-8").replace(old, new), encoding="utf-8")
            _log.info("Patched %s", p)
        except Exception as exc:
            _log.error("patch httpd.conf: %s", exc)

    def _patch_myini(self, new: str) -> None:
        """Rewrite basedir and datadir in my.ini to reflect the new base path."""
        p = Path(self.config["mysql"]["defaults"])
        if not p.exists():
            return
        mysql_dir = f"{new}/bin/mysql-9.4.0-winx64"
        try:
            txt = p.read_text(encoding="utf-8")
            txt = re.sub(r"^basedir\s*=.*", f"basedir={mysql_dir}",      txt, flags=re.M)
            txt = re.sub(r"^datadir\s*=.*", f"datadir={mysql_dir}/data", txt, flags=re.M)
            p.write_text(txt, encoding="utf-8")
            _log.info("Patched %s", p)
        except Exception as exc:
            _log.error("patch my.ini: %s", exc)

    # ── UI ────────────────────────────────────────────────────────────────────

    def _btn(self, parent: tk.Widget, label: str, cmd, color: str, **kw) -> tk.Button:
        props = {"padx": 10, "pady": 5}
        props.update(kw)
        return tk.Button(
            parent, text=label, command=cmd,
            bg=color, fg=self.C["bg"], activebackground=color,
            font=("Segoe UI", 9, "bold"),
            relief=tk.FLAT, cursor="hand2", bd=0,
            **props,
        )

    def _build_ui(self) -> None:
        C = self.C

        # Header bar
        hdr = tk.Frame(self.root, bg=C["surface"], pady=8)
        hdr.pack(fill=tk.X)
        tk.Label(hdr, text=f"  {APP_NAME}", font=("Segoe UI", 14, "bold"),
                 bg=C["surface"], fg=C["mauve"]).pack(side=tk.LEFT)
        tk.Label(hdr, text=f"v{APP_VERSION}  ", font=("Segoe UI", 9),
                 bg=C["surface"], fg=C["muted"]).pack(side=tk.RIGHT, anchor="s")

        # Primary controls
        ctrl = tk.Frame(self.root, bg=C["bg"], pady=8)
        ctrl.pack(fill=tk.X, padx=12)
        self._btn(ctrl, "START ALL",  self.start_all,         C["green"],  width=12).pack(side=tk.LEFT, padx=3)
        self._btn(ctrl, "STOP ALL",   self.stop_all,          C["red"],    width=12).pack(side=tk.LEFT, padx=3)
        self._btn(ctrl, "CLEAR PORT", self.clear_apache_port, C["yellow"], width=12).pack(side=tk.LEFT, padx=3)
        self._btn(ctrl, "SETTINGS",   self.open_settings,     C["blue"],   width=12).pack(side=tk.LEFT, padx=3)

        # Service status pills
        self._status: dict[str, tk.Label] = {}
        st = tk.Frame(self.root, bg=C["bg"], pady=4)
        st.pack(fill=tk.X, padx=12)
        for svc in ("Apache", "MySQL", "PHP"):
            pill = tk.Frame(st, bg=C["surface"], padx=12, pady=4)
            pill.pack(side=tk.LEFT, padx=3)
            lbl = tk.Label(pill, text=f"{svc}  STOPPED",
                           fg=C["muted"], bg=C["surface"],
                           font=("Consolas", 9, "bold"))
            lbl.pack()
            self._status[svc] = lbl

        # Quick-link row
        lnk = tk.Frame(self.root, bg=C["bg"], pady=4)
        lnk.pack(fill=tk.X, padx=12)
        self._btn(lnk, "localhost",   self.open_localhost,   C["sky"],    width=12).pack(side=tk.LEFT, padx=3)
        self._btn(lnk, "phpMyAdmin",  self.open_phpmyadmin,  C["mauve"],  width=12).pack(side=tk.LEFT, padx=3)
        self._btn(lnk, "www Folder",  self.open_www_dir,     C["peach"],  width=12).pack(side=tk.LEFT, padx=3)
        self._btn(lnk, "MySQL Dir",   self.open_mysql_dir,   C["teal"],   width=12).pack(side=tk.LEFT, padx=3)
        self._btn(lnk, "Start MySQL", self.start_mysql_only, C["green"],  width=12).pack(side=tk.LEFT, padx=3)

        # Log header
        lhdr = tk.Frame(self.root, bg=C["bg"])
        lhdr.pack(fill=tk.X, padx=12, pady=(6, 0))
        tk.Label(lhdr, text="Log", bg=C["bg"], fg=C["muted"],
                 font=("Segoe UI", 8)).pack(side=tk.LEFT)
        self._btn(lhdr, "Clear", self._clear_log, C["surface"],
                  pady=2, padx=6).pack(side=tk.RIGHT)

        # Log area
        self.log_area = scrolledtext.ScrolledText(
            self.root, height=14, state="disabled",
            font=("Consolas", 9), bg="#11111b", fg=C["text"],
            insertbackground=C["text"], relief=tk.FLAT, bd=0,
        )
        self.log_area.pack(padx=12, pady=(2, 10), fill=tk.BOTH, expand=True)
        for tag, fg in (
            ("ok",   C["green"]),
            ("err",  C["red"]),
            ("warn", C["yellow"]),
            ("info", C["blue"]),
        ):
            self.log_area.tag_config(tag, foreground=fg)

    # ── Logging helpers ───────────────────────────────────────────────────────

    def _emit(self, msg: str, tag: str = "") -> None:
        """Thread-safe append to the GUI log widget."""
        def _write() -> None:
            self.log_area.config(state="normal")
            ts = datetime.now().strftime("%H:%M:%S")
            self.log_area.insert(tk.END, f"[{ts}]  {msg}\n", tag)
            self.log_area.see(tk.END)
            self.log_area.config(state="disabled")
        self.root.after(0, _write)

    def _clear_log(self) -> None:
        self.log_area.config(state="normal")
        self.log_area.delete("1.0", tk.END)
        self.log_area.config(state="disabled")

    # ── Service status ────────────────────────────────────────────────────────

    def _set_status(self, svc: str, state: str) -> None:
        _map = {
            "RUNNING":  self.C["green"],
            "STARTING": self.C["yellow"],
            "STOPPING": self.C["yellow"],
            "ERROR":    self.C["red"],
            "STOPPED":  self.C["muted"],
        }
        fg = _map.get(state, self.C["muted"])
        def _w() -> None:
            if svc in self._status:
                self._status[svc].config(text=f"{svc}  {state}", fg=fg)
        self.root.after(0, _w)

    # ── Health monitor ────────────────────────────────────────────────────────

    @staticmethod
    def _tcp(host: str, port: int) -> bool:
        """Return True if a TCP connection to host:port succeeds."""
        try:
            with socket.create_connection((host, port), timeout=0.5):
                return True
        except OSError:
            return False

    def _start_monitor(self) -> None:
        threading.Thread(target=self._monitor_loop, daemon=True).start()

    def _monitor_loop(self) -> None:
        while True:
            ap = self.config.get("apache", {}).get("port", 8080)
            my = self.config.get("mysql",  {}).get("port", 3306)
            self._set_status("Apache", "RUNNING" if self._tcp("127.0.0.1", ap) else "STOPPED")
            self._set_status("MySQL",  "RUNNING" if self._tcp("127.0.0.1", my) else "STOPPED")
            php_alive = (
                "PHP" in self.processes
                and self.processes["PHP"].poll() is None
            )
            self._set_status("PHP", "RUNNING" if php_alive else "STOPPED")
            time.sleep(3)

    # ── Spawn helpers ─────────────────────────────────────────────────────────

    def _spawn(self, name: str, cmd: list, cwd: str) -> None:
        try:
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            proc = subprocess.Popen(
                cmd, cwd=cwd,
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, creationflags=flags,
            )
            self.processes[name] = proc
            self._emit(f"[{name}] Started  PID {proc.pid}", "ok")
            _log.info("[%s] PID=%s", name, proc.pid)
            threading.Thread(target=self._tail, args=(proc, name), daemon=True).start()
        except FileNotFoundError:
            self._emit(f"[{name}] binary not found: {cmd[0]}", "err")
            _log.error("[%s] binary not found: %s", name, cmd[0])
        except Exception as exc:
            self._emit(f"[{name}] {exc}", "err")
            _log.error("[%s] %s", name, exc)

    def _tail(self, proc: subprocess.Popen, name: str) -> None:
        """Stream subprocess output to the GUI log."""
        for line in proc.stdout:
            line = line.rstrip()
            if line:
                tag = "err" if "error" in line.lower() else ""
                self._emit(f"[{name}] {line}", tag)
        self._emit(f"[{name}] exited  code={proc.returncode}", "warn")
        _log.info("[%s] exited  code=%s", name, proc.returncode)

    def _wait_port(self, host: str, port: int, timeout: int = 20) -> bool:
        """Poll until port accepts connections or timeout expires."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            if self._tcp(host, port):
                return True
            time.sleep(0.5)
        return False

    # ── Service control ───────────────────────────────────────────────────────

    def start_all(self) -> None:
        threading.Thread(target=self._start_all_bg, daemon=True).start()

    def _start_all_bg(self) -> None:
        self._emit("─── Starting stack ───", "info")

        # PHP version check (used as Apache module; no long-running process needed)
        php = self.config["php"]["bin"]
        if os.path.exists(php):
            flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
            r = subprocess.run(
                [php, "-r", "echo PHP_VERSION;"],
                capture_output=True, text=True, creationflags=flags,
            )
            self._emit(f"[PHP] {r.stdout.strip()}", "ok")
            self._set_status("PHP", "RUNNING")
        else:
            self._emit(f"[PHP] binary missing: {php}", "warn")

        # MySQL — wait for it to be ready before starting Apache
        my_port = self.config["mysql"]["port"]
        if self._tcp("127.0.0.1", my_port):
            self._emit("[MySQL] Already running.", "ok")
        else:
            self._start_mysql()
            if not self._wait_port("127.0.0.1", my_port, timeout=20):
                self._emit("[MySQL] Did not start within 20 s — aborting.", "err")
                return

        # Apache
        ap_port = self.config["apache"]["port"]
        if self._tcp("127.0.0.1", ap_port):
            self._emit("[Apache] Already running.", "ok")
        else:
            self._start_apache()

        self._emit("─── Stack ready ───", "ok")

    def _start_mysql(self) -> None:
        bin_  = self.config["mysql"]["bin"]
        ini_  = self.config["mysql"]["defaults"]
        if not os.path.exists(bin_):
            self._emit(f"[MySQL] binary missing: {bin_}", "err")
            return
        # --defaults-file MUST be the first argument after the binary (MySQL requirement)
        cmd = [bin_]
        if os.path.exists(ini_):
            cmd.append(f"--defaults-file={ini_}")
        cmd.append("--console")
        self._set_status("MySQL", "STARTING")
        self._spawn("MySQL", cmd, str(Path(bin_).parent))

    def _start_apache(self) -> None:
        bin_ = self.config["apache"]["bin"]
        if not os.path.exists(bin_):
            self._emit(f"[Apache] binary missing: {bin_}", "err")
            return
        self._set_status("Apache", "STARTING")
        self._spawn("Apache", [bin_], str(Path(bin_).parent))

    def start_mysql_only(self) -> None:
        if self._tcp("127.0.0.1", self.config["mysql"]["port"]):
            self._emit("[MySQL] Already running.", "warn")
            return
        threading.Thread(target=self._start_mysql, daemon=True).start()

    def stop_all(self) -> None:
        self._emit("─── Stopping stack ───", "warn")
        for name, proc in list(self.processes.items()):
            if proc.poll() is None:
                self._emit(f"[{name}] Stopping...", "warn")
                proc.terminate()
                try:
                    proc.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    self._emit(f"[{name}] Force-killed.", "err")
        self.processes.clear()
        self._emit("─── Stack stopped ───", "warn")

    # ── Quick links ───────────────────────────────────────────────────────────

    def open_localhost(self) -> None:
        url = f"http://localhost:{self.config['apache']['port']}"
        self._emit(f"[Browser] {url}", "info")
        webbrowser.open(url)

    def open_phpmyadmin(self) -> None:
        url = f"http://localhost:{self.config['apache']['port']}/phpmyadmin"
        self._emit(f"[Browser] {url}", "info")
        webbrowser.open(url)

    def open_www_dir(self) -> None:
        d = self.config.get("www", _fwd(BASE / "www"))
        self._emit(f"[Explorer] {d}", "info")
        os.startfile(d)

    def open_mysql_dir(self) -> None:
        d = str(Path(self.config["mysql"]["bin"]).parent)
        self._emit(f"[Explorer] {d}", "info")
        os.startfile(d)

    # ── Port clearing ─────────────────────────────────────────────────────────

    def clear_apache_port(self) -> None:
        port = int(self.config["apache"]["port"])
        self._emit(f"[Port] Checking :{port}...", "info")
        try:
            flags = subprocess.CREATE_NO_WINDOW
            out = subprocess.run(
                ["netstat", "-ano"], capture_output=True, text=True, creationflags=flags
            ).stdout
            pids = {
                ln.split()[-1]
                for ln in out.splitlines()
                if f":{port}" in ln and "LISTENING" in ln
            }
            if not pids:
                self._emit(f"[Port] Nothing listening on :{port}.", "ok")
                return
            for pid in pids:
                subprocess.run(
                    ["taskkill", "/F", "/PID", pid],
                    capture_output=True, creationflags=flags,
                )
                self._emit(f"[Port] Killed PID {pid}", "ok")
        except Exception as exc:
            self._emit(f"[Port] {exc}", "err")

    # ── Settings ──────────────────────────────────────────────────────────────

    def open_settings(self) -> None:
        C   = self.C
        win = tk.Toplevel(self.root)
        win.title("Settings")
        win.geometry("560x395")
        win.configure(bg=C["bg"])
        win.transient(self.root)
        win.grab_set()

        def row(parent: tk.Widget, label: str, value: object, r: int) -> tk.Entry:
            tk.Label(parent, text=label, bg=C["bg"], fg=C["subtext"],
                     font=("Segoe UI", 9)).grid(row=r, column=0, sticky="w", padx=12, pady=5)
            e = tk.Entry(parent, width=44, bg=C["surface"], fg=C["text"],
                         insertbackground=C["text"], relief=tk.FLAT, font=("Consolas", 9))
            e.insert(0, str(value))
            e.grid(row=r, column=1, padx=10, pady=5)
            return e

        frame = tk.Frame(win, bg=C["bg"])
        frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        ac = self.config.get("apache", {})
        mc = self.config.get("mysql",  {})

        e_ap_port = row(frame, "Apache Port",     ac.get("port", 8080),      0)
        e_ap_conf = row(frame, "httpd.conf Path", ac.get("conf", ""),         1)
        e_my_port = row(frame, "MySQL Port",       mc.get("port", 3306),     2)
        e_my_user = row(frame, "MySQL User",       mc.get("user", "root"),   3)
        e_my_pass = row(frame, "MySQL Password",   mc.get("password", ""),   4)
        e_my_bin  = row(frame, "mysqld.exe Path",  mc.get("bin", ""),        5)
        e_my_ini  = row(frame, "my.ini Path",      mc.get("defaults", ""),   6)

        bf = tk.Frame(win, bg=C["bg"])
        bf.pack(pady=10)

        def on_save() -> None:
            try:
                ap = int(e_ap_port.get().strip())
                my = int(e_my_port.get().strip())
            except ValueError:
                messagebox.showerror("Invalid Input", "Ports must be integers.")
                return
            self.config["apache"].update({"port": ap, "conf": e_ap_conf.get().strip()})
            self.config["mysql"].update({
                "port":     my,
                "user":     e_my_user.get().strip(),
                "password": e_my_pass.get().strip(),
                "bin":      e_my_bin.get().strip(),
                "defaults": e_my_ini.get().strip(),
            })
            self._save_config()
            self._emit("[Settings] Saved — restart services to apply.", "ok")
            win.destroy()

        self._btn(bf, "SAVE",   on_save,     C["green"], width=12).pack(side=tk.LEFT, padx=8)
        self._btn(bf, "CANCEL", win.destroy, C["muted"], width=12).pack(side=tk.LEFT, padx=8)

    # ── Close ─────────────────────────────────────────────────────────────────

    def _on_close(self) -> None:
        if any(p.poll() is None for p in self.processes.values()):
            if not messagebox.askokcancel(
                "Quit", "Services are running.\nStop them and quit?"
            ):
                return
            self.stop_all()
        self.root.destroy()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    root = tk.Tk()
    DevStation(root)
    root.mainloop()
