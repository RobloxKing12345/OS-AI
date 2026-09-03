#!/usr/bin/env python3
"""Native VM backend for OS AI. Uses QEMU and persistent QCOW2 disks."""
from __future__ import annotations
import argparse
import json
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VM_ROOT = ROOT / "vms"
CONFIG = ROOT / "backend" / "vms.json"

DEFAULTS = {
    "windows11": {"ram": "4G", "cpu": "2", "disk": "64G"},
    "linux": {"ram": "2G", "cpu": "2", "disk": "25G"},
    "macos": {"ram": "6G", "cpu": "4", "disk": "80G"},
    "chromeos": {"ram": "4G", "cpu": "2", "disk": "32G"},
    "android": {"ram": "3G", "cpu": "2", "disk": "24G"},
    "other": {"ram": "2G", "cpu": "2", "disk": "25G"},
}


def qemu_binary() -> str | None:
    return shutil.which("qemu-system-x86_64") or shutil.which("qemu-system-aarch64")


def qemu_img_binary() -> str | None:
    return shutil.which("qemu-img")


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
        raise ValueError(f"Unsupported OS: {os_id}")
    qemu_img = qemu_img_binary()
    if not qemu_img:
        raise RuntimeError("qemu-img is not installed. Install QEMU first.")
    vm_dir = VM_ROOT / name
    vm_dir.mkdir(parents=True, exist_ok=True)
    disk = vm_dir / "disk.qcow2"
    if not disk.exists():
        subprocess.run([qemu_img, "create", "-f", "qcow2", str(disk), DEFAULTS[os_id]["disk"]], check=True)
    cfg = load_config()
    cfg[name] = {"name": name, "os": os_id, **DEFAULTS[os_id], "disk": str(disk), "status": "stopped"}
    save_config(cfg)
    return disk


def build_qemu_command(name: str, iso: str | None = None) -> list[str]:
    cfg = load_config().get(name)
    if not cfg:
        raise ValueError(f"VM '{name}' is not in the OS AI library. Create it first.")
    qemu = qemu_binary()
    if not qemu:
        raise RuntimeError("QEMU is not installed. Install QEMU first.")
    cmd = [qemu, "-name", f"OS-AI-{name}", "-m", cfg["ram"], "-smp", cfg["cpu"], "-drive", f"file={cfg['disk']},if=virtio,format=qcow2", "-nic", "user", "-display", "default"]
    if iso:
        iso_path = Path(iso).expanduser().resolve()
        if not iso_path.exists():
            raise ValueError(f"Installer ISO not found: {iso_path}")
        cmd += ["-cdrom", str(iso_path), "-boot", "menu=on"]
    return cmd


def start_vm_process(name: str, iso: str | None = None) -> subprocess.Popen:
    """Start an existing VM as a separate native QEMU process."""
    cmd = build_qemu_command(name, iso)
    cfg = load_config()
    cfg[name]["status"] = "running"
    save_config(cfg)
    return subprocess.Popen(cmd, cwd=str(ROOT))


def start_vm(name: str, iso: str | None = None) -> None:
    proc = start_vm_process(name, iso)
    print(f"Started OS AI VM '{name}' (PID {proc.pid}).")
    proc.wait()
    cfg = load_config()
    if name in cfg:
        cfg[name]["status"] = "stopped"
        save_config(cfg)


def main() -> None:
    parser = argparse.ArgumentParser(prog="os-ai-vm-manager")
    sub = parser.add_subparsers(dest="action", required=True)
    c = sub.add_parser("create", help="Create a persistent VM disk")
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
        qemu, img = qemu_binary(), qemu_img_binary()
        print(json.dumps({"qemu": qemu, "qemu_img": img, "ready": bool(qemu and img)}, indent=2))


if __name__ == "__main__":
    main()
