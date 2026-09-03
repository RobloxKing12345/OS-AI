# OS AI native VM backend

Prototype 3.1 now connects the HTML UI to this local native bridge. The bridge starts real QEMU processes instead of showing a simulated guest desktop.

## Requirements

- Python 3
- QEMU and `qemu-img` installed on the host
- An OS installer ISO that you are legally entitled to use

Check QEMU:

```bash
python backend/vm_manager.py doctor
```

## Run OS AI with the native backend

From the repository root:

```bash
python backend/api_server.py
```

Then open:

```text
http://127.0.0.1:8765/OS_AI_Prototype_3_1.html
```

Do not open the HTML with `file://` if you want real VM control. The local server provides the bridge between the browser UI and QEMU.

## How it works

1. Pick an OS in Home.
2. Click **Add VM**.
3. OS AI calls `/api/create` and creates a persistent QCOW2 disk.
4. The VM is saved in the native backend configuration and the OS AI library.
5. Click **Start VM** on that existing VM.
6. OS AI calls `/api/start` and QEMU opens a real native VM window.
7. If the disk is new, put the installer ISO path in Settings before starting it.
8. After installation, start the same VM without an ISO.

The Start button never creates a second VM. It starts the existing library VM by name.

## Important platform notes

This is a real virtualization prototype, but it is not yet a polished production hypervisor. Windows 11 may require additional UEFI/TPM configuration, and macOS guests have platform and licensing restrictions. Performance depends on the host CPU, GPU, virtualization support, and guest OS.

The browser UI cannot directly launch QEMU by itself because browsers are sandboxed. The local Python bridge is the native boundary used by this prototype.

Installation media is not included in this repository. Use official installation media you are legally entitled to use.
