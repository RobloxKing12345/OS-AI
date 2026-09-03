#!/usr/bin/env python3
"""Local OS AI bridge: serves the UI and controls the real QEMU backend."""
from __future__ import annotations
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vm_manager import DEFAULTS, create_vm, load_config, qemu_binary, start_vm_process

HOST = "127.0.0.1"
PORT = 8765

class Handler(BaseHTTPRequestHandler):
    def send_json(self, data, status=200):
        raw = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if self.path == "/api/doctor":
            self.send_json({"ready": bool(qemu_binary()), "qemu": qemu_binary()})
            return
        if self.path == "/api/vms":
            self.send_json(load_config())
            return
        if self.path in ("/", "/OS_AI_Prototype_3_1.html"):
            data = (ROOT / "OS_AI_Prototype_3_1.html").read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_json({"error": "Not found"}, 404)

    def do_POST(self):
        if not self.path.startswith("/api/"):
            self.send_json({"error": "Not found"}, 404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = json.loads(self.rfile.read(length) or b"{}")
            if self.path == "/api/create":
                name, os_id = body["name"], body["os"]
                if os_id not in DEFAULTS:
                    raise ValueError("Unsupported OS for this native prototype")
                disk = create_vm(name, os_id)
                self.send_json({"ok": True, "disk": str(disk)})
                return
            if self.path == "/api/start":
                proc = start_vm_process(body["name"], body.get("iso"))
                self.send_json({"ok": True, "pid": proc.pid})
                return
            self.send_json({"error": "Not found"}, 404)
        except Exception as exc:
            self.send_json({"error": str(exc)}, 400)

    def log_message(self, fmt, *args):
        print("[OS AI] " + (fmt % args))

if __name__ == "__main__":
    print(f"OS AI native bridge: http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
