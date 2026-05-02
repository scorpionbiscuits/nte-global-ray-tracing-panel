# RTX Fix for NTEGlobal
This is a fork of nte-ray-tracing-panel originally by which works only on Chinese version of the game. This fix ensures that the tool works for NTE Global Release. Tested on NVIDIA RTX 4060.

# How to Enable Ray Tracing in NTE: One-Click Ray Tracing Unlock / Deployment Tool

Search Keywords: How to enable ray tracing in NTE, NTE ray tracing fix, NTE path tracing unlock, NTE ray tracing option missing, NTE ray tracing not showing, NTE ray tracing won't open, NTE RTX 5060 no ray tracing, NTE RTX 4060 ray tracing, NTE one-click ray tracing unlock, NTE one-click install, NTE OptiScaler one-click setup, NTE winmm.dll install, NTE unlock ray tracing without registry edits.

The `NTE Ray Tracing Panel (异环光追一键部署面板)` is a local WebUI tool designed to solve issues like "How to enable ray tracing in NTE" or "Why is the ray tracing option missing?" It automates the preparation of OptiScaler, installs the local `winmm.dll` and `OptiScaler.ini`, and turns the verified GPU spoofing process into an automated, selectable, and reversible one-click workflow.

English README: [README.en.md](README.en.md)

Local URL:
http://127.0.0.1:22642

Note: This is not an online service; it runs entirely on your local machine. The web page handles the display, directory selection, and execution, while the Python/exe backend handles the server at 127.0.0.1:22642, downloads OptiScaler, writes files, and manages backups. Closing the browser tab will not stop the backend service. You must click "Exit Tool" in the panel or end NTERayTracingPanel.exe via Task Manager.

---

## Project Purpose

The focus of this project is not to be a "Generic Mod Manager," but to turn the specific ray tracing unlock path for *Neverness To Everness* into a reusable process:

* Whitelist Issue: The current NTE test version hides ray tracing options based on a GPU model whitelist.
* Verified Solution: Using OptiScaler DXGI/Streamline to spoof a whitelisted GPU successfully unlocks the in-game options.
* Safety: Modifying the system-wide GPU registry affects the entire OS and is unsuitable for primary development machines.
* Local Scope: This tool defaults to writing local proxy files only within the game's Win64 directory and provides manifest-based backups and restoration.

---

## What It Solves

Many RTX 50/40/30 series cards support ray tracing, but the NTE test version hides the "Ray Tracing / Path Tracing" options based on a whitelist. 

This tool uses OptiScaler's DXGI/Streamline GPU spoofing to disguise the GPU name seen by HTGame.exe as a targeted whitelist model. The WebUI currently offers three profiles: Original Configuration, NVIDIA GeForce RTX 4090, and NVIDIA GeForce RTX 5080 Laptop GPU. This method has been verified to unlock the ray tracing settings in-game.

---

## Document Navigation

For first-time users, it is recommended to read in order:
1. [Quick Start](docs/01-快速使用.md)
2. [Principles and Trial Path](docs/02-原理与试错路径.md)
3. [Backup/Restore and Scope of Changes](docs/03-备份恢复与修改范围.md)
4. [Release Guide](docs/04-发布指南.md)
5. [FAQ](docs/05-常见问题.md)

---

## Security Boundaries

* No intrusive tools: Does not use ProcMon, Sysmon, driver monitors, or kernel hooking tools.
* No Registry Edits: By default, it does not modify HKLM\SYSTEM\CurrentControlSet\Enum\PCI.
* Focused Scope: Manages only these files within the game directory:
  - winmm.dll
  - OptiScaler.ini
  - OptiScaler.log
  - OptiScaler\ folder
  - Legacy compatibility backups: dlsstweaks.ini, dlsstweaks.log
* Automated Backups: Creates a _nte_rt_backups\<timestamp>\manifest.json before every installation.
* Safe Restoration: Restores files strictly according to the manifest to avoid deleting non-tool files.

---

## Usage Instructions

1. Run run.bat or double-click the release version NTERayTracingPanel.exe.
2. Once the page opens, select the NTE installation root directory or the specific path: Client\WindowsNoEditor\HT\Binaries\Win64.
3. Click "Download/Prepare OptiScaler."
4. Select a target GPU profile: Original, RTX 4090, or RTX 5080M.
5. Ensure the game and launcher are closed.
6. Click "Backup and Install Ray Tracing Unlock."
7. Launch the game and check the Graphics settings for Ray Tracing options.

---

## Operation and Exit

The tool consists of two layers:
* Frontend WebUI: The browser page for status and commands.
* Backend Service: NTERayTracingPanel.exe (or python app.py), which listens to the port and performs file operations.

Closing the browser tab will not free up port 22642. To exit, click "Exit Tool" at the bottom of the WebUI. If you already closed the page, navigate back to http://127.0.0.1:22642 to exit, or kill the process in Task Manager.

---

## Restoration

In the "Backup & Restore" card on the page, select your most recent backup and click Restore. Alternatively, use the command line:

python app.py --no-browser

Then use the WebUI to restore the specific backup.

---

## Technical Principles

OptiScaler's GPU spoofing overrides the GPU description, VendorId, DeviceId, and VRAM information that the game process reads via DXGI/Streamline. This tool generates configurations based on your selection:

* Original: Reads your actual NVIDIA name and DeviceId (for reverting).
* RTX 4090: SpoofedGPUName=NVIDIA GeForce RTX 4090, SpoofedDeviceId=0x2684.
* RTX 5080M: SpoofedGPUName=NVIDIA GeForce RTX 5080 Laptop GPU, SpoofedDeviceId=0x2C59.

All profiles maintain these safe defaults:
* TargetProcessName=HTGame.exe
* SpoofedVendorId=0x10de
* Dxgi=true
* StreamlineSpoofing=true
* Registry=false
* User32=false

Difference from Registry Hacks: While registry hacks affect the entire system, DXGI spoofing only takes effect when the local proxy DLL is loaded by HTGame.exe.

---

## Core Projects and Credits

* [OptiScaler](https://github.com/optiscaler/OptiScaler): The core source of the GPU spoofing functionality. This panel fetches OptiScaler.dll from official releases and installs it as a winmm.dll proxy.
* [DLSSTweaks](https://github.com/emoose/DLSSTweaks): A related graphics wrapper tool. This project does not use DLSSTweaks for DLSS scaling but recognizes existing dlsstweaks.ini/log files during backup to avoid overwriting your experimental files.

This project is not OptiScaler itself, nor a fork of DLSSTweaks, nor an official NVIDIA tool; it is a dedicated installation and management panel for NTE built around OptiScaler.
