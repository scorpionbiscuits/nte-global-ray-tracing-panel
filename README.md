# RT Fix for NTE Global

A fork of [nte-ray-tracing-panel](https://github.com/llg1634/nte-ray-tracing-panel) by llg1634, which was originally built for the Chinese client only. This fork patches the tool to work with the **NTE Global PC release** (`NTEGlobalGame.exe`).

Tested and working on **NVIDIA RTX 4060**.

> GPU spoofing is done entirely inside the game process via OptiScaler's DXGI/Streamline hooks. The system-wide GPU registry is never touched.

---

## Important!
### Close These Programs Before Running the Tool -

The following programs must be closed before using the tool, or the installation will fail:

1. **NTE** and its launcher (`NTEGlobalLauncher.exe`) — the tool needs to write to the game directory while it is not running.
2. **MSI Afterburner / RivaTuner Statistics Server (RTSS)** — these hook DXGI at the same layer as OptiScaler.
3. **Process Monitor (Procmon)** — its kernel filter driver (`PROCMON`) intercepts file operations at a low level and can cause the install to silently fail. The tool shows a warning in the *Machine Status* card if it detects the driver is loaded. A full reboot clears it.

---

## Installation Guide

### Method 1 — Direct Installation (Recommended)

1. Go to the [Releases](../../releases) page and download the latest `NTERayTracingPanel.exe`.
2. Right click the file and `Run as Administrator`.
3. A browser tab opens automatically at [`http://127.0.0.1:22642`](http://127.0.0.1:22642). If it doesn't, open that URL manually.
4. In the **Game Path** card, click **Select** and if different from default, navigate to your NTE install folder (e.g. `C:\Program Files\Neverness To Everness\NTEGlobal`), or paste the path directly and click **Detect**.
5. In the **OptiScaler** card, click **Download / Prepare OptiScaler** and wait for it to finish. You should see a version if installed correctly. In case it fails or gives an error, press Exit Tool then close the browser and try again.
6. In the **Ray Tracing Unlock** card, choose a target GPU profile:
   - **RTX 5080M** — default, recommended
   - **RTX 4090** — alternative
   - **Local (current GPU)** — use this only if you already have a supported GPU and want to restore normal identity
7. Leave the mode on **DXGI** (default). Only switch to *Full Experimental* if DXGI mode fails.
8. Click **Backup and Install Ray Tracing Unlock**.
9. Launch the game. You should see Optiscaler on the bottom left if everything is installed correctly. Go to **Settings → Graphics** — ray tracing and path tracing options should now be visible.

> To undo: open the tool, go to **Backup & Restore**, select the latest backup, and click **Restore**.

---

### Method 2 — Running from Source

**Requirements:** Python 3.11+, Git

```bash
# 1. Clone the repo
git clone https://github.com/scorpionbiscuits/nte-global-ray-tracing-panel
cd nte-global-ray-tracing-panel

# 2. Install dependencies
pip install -r requirements.txt
```

**To build the exe yourself:**

```bash
build_onefile_exe.bat
# Output: dist\NTERayTracingPanel.exe

# Run as Administrator
run_as_admin.bat
```

---

## Troubleshooting

| Error | Fix |
|---|---|
| `WinError 5 Access Denied` | Add the game's `Win64` folder to Defender exclusions, then retry. |
| Ray tracing options still not visible after install | Read the Important section above. If you see Optiscaler at the bottom right when launching the game, yo've done it correctly. |
| Game crashes frequently | Lower the DLSS Super Resolution and other settings. |
| Browser doesn't open automatically | Navigate to `http://127.0.0.1:22642` manually. |
| Procmon warning in Machine Status | Fully reboot the PC — the Procmon kernel driver stays loaded until you do. |
| Optiscaler installation issue | Press Exit Tool, close the browser and try again. |

---

## What Changed From the Original

- Detection of `NTEGlobalGame.exe` (global release) alongside the original `HTGame.exe`
- Auto-detection now searches `C:\Program Files\Neverness To Everness\NTEGlobal` and `Program Files (x86)` paths
- `TargetProcessName` in `OptiScaler.ini` is now set dynamically to whichever exe was actually found
- Process kill/detect list updated for `NTEGlobalLauncher`, `NTEGlobalBrowser`, `NTEGlobalWebBooster` 
- WinError 5 handling with actionable error messages instead of a generic crash
- Browser launch fixed when running as administrator (`explorer.exe` de-escalation)
- Compiled exe now embeds a UAC manifest (`--uac-admin`) so it self-elevates on launch

---

Search Keywords: How to enable ray tracing in NTE, NTE ray tracing fix, NTE path tracing unlock, NTE ray tracing option missing, NTE ray tracing not showing, NTE ray tracing won't open, NTE RTX 5060 no ray tracing, NTE RTX 4060 ray tracing, NTE one-click ray tracing unlock, NTE one-click install, NTE OptiScaler one-click setup, NTE winmm.dll install, NTE unlock ray tracing without registry edits.

The `NTE Ray Tracing Panel (异环光追一键部署面板)` is a local WebUI tool designed to solve issues like "How to enable ray tracing in NTE" or "Why is the ray tracing option missing?" It automates the preparation of OptiScaler, installs the local `winmm.dll` and `OptiScaler.ini`, and turns the verified GPU spoofing process into an automated, selectable, and reversible one-click workflow.

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

This tool uses OptiScaler's DXGI/Streamline GPU spoofing to disguise the GPU name seen by `HTGame.exe` or for the global version `NTEGlobalGame.exe` as a targeted whitelist model. The WebUI currently offers three profiles: Original Configuration, NVIDIA GeForce RTX 4090, and NVIDIA GeForce RTX 5080 Laptop GPU. This method has been verified to unlock the ray tracing settings in-game.

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

## Operation and Exit

The tool consists of two layers:
* Frontend WebUI: The browser page for status and commands.
* Backend Service: NTERayTracingPanel.exe (or python app.py), which listens to the port and performs file operations.

Closing the browser tab will not free up port 22642. To exit, click "Exit Tool" at the bottom of the WebUI. If you already closed the page, navigate back to http://127.0.0.1:22642 to exit, or kill the process in Task Manager.

---

## Restoration

In the "Backup & Restore" card on the page, select your most recent backup and click Restore. Alternatively, use the command line:

```bash
python app.py --no-browser
```
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
