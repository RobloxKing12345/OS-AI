# OS AI native VM backend

This backend is the first step from the HTML simulation to a real interactive VM.

## What it does

- Creates a persistent QCOW2 VM disk.
- Stores VM configuration in `backend/vms.json`.
- Starts the exact existing VM instead of creating a duplicate.
- Uses QEMU as the virtualization engine.
- Can attach an installer ISO on first boot.

## Requirements

Install **QEMU + qemu-img** on the host computer. The HTML prototype alone cannot launch a local hypervisor because browsers are sandboxed.

Check the installation with:

```bash
python backend/vm_manager.py doctor
```

Create a Windows 11 VM disk:

```bash
python backend/vm_manager.py create "Windows 11 VM" windows11
```

Start it with a Windows installer ISO:

```bash
python backend/vm_manager.py start "Windows 11 VM" --iso "/path/to/Windows.iso"
```

After the OS is installed, start it without `--iso`.

## Next integration step

The OS AI desktop UI should communicate with this local backend through a small native IPC/API layer. The backend then owns the QEMU process, VM lifecycle, storage, and display connection. The existing noVNC UI can later connect to a QEMU VNC/WebSocket display, or the native app can embed a local VM display directly.

**Important:** this repository does not include Windows installation media. Use installation media you are legally entitled to use.
