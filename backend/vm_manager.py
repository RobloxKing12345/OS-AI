#!/usr/bin/env python3
"""OS AI native VM launcher prototype.

Starts a real VM through QEMU when QEMU is installed. This is intentionally
small: the web UI can call this process later, while this backend owns the
actual VM process and disk image.
"""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VM_ROOT = ROOT / "vms"
CONFIG = ROOT / "backend" / "vms.json"

DEFAULTS = {
    "windows11": {"ram": "4G", "cpu": "2", "disk": "64G"},
    "linux": {"ram": "2G", "cpu": "2", "disk": "25G"},
    "android": {"ram": "3G", "cpu": "2", "disk": "24G"},
}


def qemu_binary() -> str | None:
    return shutil.which("qemu-system-x86_64") or shutil.which("qemu-system-aarch64")


def load_config() -> dict:
    if not CONFIG.exists():
        return {}
    try:
        return json.loads(CONFIG.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_config(data: dict) -> None:
    CONFIG.parent.mkdir(parents=True, exist_ok=True)
    CONFIG.write_text(json.dumps(data, indent=2), encoding="utf-8")


def create_vm(name: str, os_id: str) -> Path:
    if os_id not in DEFAULTS:
        raise SystemExit(f"Unsupported prototype OS: {os_id}")
    vm_dir = VM_ROOT / name
    vm_dir.mkdir(parents=True, exist_ok=True)
    disk = vm_dir / "disk.qcow2"
    qemu = qemu_binary()
    if not qemu:
        raise SystemExit("QEMU is not installed. Install QEMU, then run this command again.")
    if not disk.exists():
        size = DEFAULTS[os_id]["disk"]
        subprocess.run([qemu, "-drive", f"file={disk},if=none,format=qcow2", "-qmp", "stdio", "-nographic", "-nodefaults", "-S"], input="{\"execute\":\"quit\"}\n", text=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # qemu-img is the correct tool for creating the image.
        qemu_img = shutil.which("qemu-img")
        if not qemu_img:
            raise SystemExit("qemu-img is not installed.")
        subprocess.run([qemu_img, "create", "-f", "qcow2", str(disk), size], check=True)
    cfg = load_config()
    cfg[name] = {"name": name, "os": os_id, **DEFAULTS[os_id], "disk": str(disk)}
    save_config(cfg)
    return disk


def start_vm(name: str, iso: str | None = None) -> None:
    cfg = load_config().get(name)
    if not cfg:
        raise SystemExit(f"VM '{name}' is not in the OS AI library. Create it first.")
    qemu = qemu_binary()
    if not qemu:
        raise SystemExit("QEMU is not installed.")
    cmd = [qemu, "-name", f"OS-AI-{name}", "-m", cfg["ram"], "-smp", cfg["cpu"], "-drive", f"file={cfg['disk']},if=virtio,format=qcow2", "-nic", "user", "-display", "default"]
    if iso:
        cmd += ["-cdrom", str(Path(iso).expanduser().resolve()), "-boot", "menu=on"]
    print("Starting real VM:", " ".join(cmd))
    os.execv(qemu, cmd)


def main() -> None:
    parser = argparse.ArgumentParser(prog="os-ai-vm-manager")
    sub = parser.add_subparsers(dest="action", required=True)
    c = sub.add_parser("create", help="Create a VM disk and save it to the library")
    c.add_argument("name")
    c.add_argument("os", choices=sorted(DEFAULTS))
    s = sub.add_parser("start", help="Start an existing VM")
    s.add_argument("name")
    s.add_argument("--iso", help="Optional installer ISO for first boot")
    sub.add_parser("doctor", help="Check native virtualization dependencies")
    args = parser.parse_args()
    if args.action == "create":
        print(f"Created {args.name}: {create_vm(args.name, args.os)}")
    elif args.action == "start":
        start_vm(args.name, args.iso)
    elif args.action == "doctor":
        qemu = qemu_binary()
        print(json.dumps({"qemu": qemu, "qemu_img": shutil.which("qemu-img"), "ready": bool(qemu and shutil.which("qemu-img"))}, indent=2))


if __name__ == "__main__":
    main()
