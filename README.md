# RT Fix for NTE Global

A fork of [nte-ray-tracing-panel](https://github.com/llg1634/nte-ray-tracing-panel) by llg1634, which was originally built for the Chinese client only. This fork patches the tool to work with the **NTE Global PC release**.

Tested and working on **NVIDIA RTX 4060**.

![Screenshot 1](https://i.imgur.com/ZIVUDfD.png)
![Screenshot 2](https://i.imgur.com/uqRmYmE.jpeg)

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

> Please report any isues not on this list [here](https://github.com/scorpionbiscuits/nte-global-ray-tracing-panel/issues). Make sure to describe your issue in full detail.
---

## What Changed From the Original
 
### Global PC Release Compatibility
- Added `NTEGlobalGame.exe` and `NTEGame.exe` to the game executable detection candidates alongside the original `HTGame.exe`
- Default install path now pre-filled as `C:\Program Files\Neverness To Everness\Client\WindowsNoEditor\HT\Binaries\Win64\HTGame.exe` — the tool auto-detects and pre-populates the path field on startup without any user input in most cases
- Auto-detection now searches `Program Files\Neverness To Everness`, `Program Files (x86)\Neverness To Everness`, and the `NTEGlobal` subdirectory on every drive, in addition to the original drive-root-only scan
- Process kill and detection lists updated to include `NTEGlobalLauncher`, `NTEGlobalBrowser`, and `NTEGlobalWebBooster`
- `TargetProcessName` in `OptiScaler.ini` is now written dynamically from whichever executable was actually found on disk, instead of being hardcoded

---

# NTE GPU Feature Classification

> Source: `DefaultDeviceProfiles.ini` — classification by UI feature flags inherited from `BaseProfileName` and per-profile CVars.  
> Total profiles: 185
> Please report any discrepancies.

---

## Full RayTracing Enabled GPUs (8 profiles)
*Lumen, RayTracing, and FullRayTracing are all enabled.*

| | |
|---|---|
| NVIDIA GeForce RTX 4080 | NVIDIA GeForce RTX 4090 |
| NVIDIA GeForce RTX 5070 | NVIDIA GeForce RTX 5070 Laptop GPU |
| NVIDIA GeForce RTX 5070 Ti | NVIDIA GeForce RTX 5070 Ti Laptop GPU |
| NVIDIA GeForce RTX 5080 | NVIDIA GeForce RTX 5090 |

---

## Only RayTracing Enabled GPU (1 profile)
*Lumen and RayTracing enabled, FullRayTracing is not.*

| |
|---|
| NVIDIA TITANRTX |

---

## Lumen Enabled GPUs (30 profiles)
*Lumen enabled, RayTracing and FullRayTracing are not.*

| | | |
|---|---|---|
| AMD Radeon RX 6700XT | AMD Radeon RX 6750GRE | AMD Radeon RX 6750XT |
| AMD Radeon RX 6800 | AMD Radeon RX 6900XT | AMD Radeon RX 6950XT |
| AMD Radeon RX 7600XT | AMD Radeon RX 7700XT | AMD Radeon RX 7800M |
| AMD Radeon RX 7800XT | AMD Radeon RX 7900GRE | AMD Radeon RX 7900M |
| AMD Radeon RX 7900XT | AMD Radeon RX 7900XTX | AMD Radeon RX 9060XT |
| AMD Radeon RX 9070 | NVIDIA GeForce RTX 2080 Ti | NVIDIA GeForce RTX 3060 Ti |
| NVIDIA GeForce RTX 3070 | NVIDIA GeForce RTX 3070 Laptop GPU | NVIDIA GeForce RTX 3070 Ti Laptop GPU |
| NVIDIA GeForce RTX 3080 | NVIDIA GeForce RTX 3090 | NVIDIA GeForce RTX 4060 Ti |
| NVIDIA GeForce RTX 4070 | NVIDIA GeForce RTX 4070 Ti | NVIDIA GeForce RTX 5060 |
| NVIDIA GeForce RTX 5060 Ti | NVIDIA GeForce RTX 5060 Ti Laptop GPU | NVIDIA TITANV |

---

## Disabled / No Lumen (146 profiles)
*No effective Lumen or RayTracing UI flag enabled.*

**AMD**

| | | | |
|---|---|---|---|
| Radeon 760M Graphics | Radeon 780M Graphics | Radeon Graphics | Radeon Pro5300M |
| Radeon Pro5500XT | Radeon Pro5600M | Radeon R9 380 | Radeon R9 390 |
| Radeon RX 460 | Radeon RX 470 | Radeon RX 480 | Radeon RX 5300M |
| Radeon RX 5500 | Radeon RX 5500M | Radeon RX 5500XT | Radeon RX 5600 |
| Radeon RX 5600M | Radeon RX 560 | Radeon RX 560X | Radeon RX 5700 |
| Radeon RX 5700M | Radeon RX 5700XT | Radeon RX 580 | Radeon RX 590 |
| Radeon RX 590GME | Radeon RX 6400 | Radeon RX 6500XT | Radeon RX 6600 |
| Radeon RX 6600M | Radeon RX 6600XT | Radeon RX 6650XT | Radeon RX 6700 |
| Radeon RX 6700M | Radeon RX 6800M | Radeon RX 6800S | Radeon RX 6800XT |
| Radeon RX 6802048SP | Radeon RX 7500 | Radeon RX 7600 | Radeon RX 7600M |
| Radeon RX 7600MXT | Radeon RX 7600S | Radeon RX 7700S | Radeon RX 7900 |
| Radeon RXVega | Radeon RXVega10 Graphics | Radeon RXVega11 Graphics | Radeon RXVega56 |
| Radeon RXVega64 | Radeon Vega10 Mobile Graphics | Radeon Vega11 Mobile Graphics | Radeon Vega3 Graphics |
| Radeon Vega6 Graphics | Radeon Vega8 Graphics | Radeon Vega9 Graphics | Radeon VegaFrontierEdition |

**NVIDIA**

| | | | |
|---|---|---|---|
| GeForce GTX 550 Ti | GeForce GTX 645 | GeForce GTX 650 | GeForce GTX 650 Ti |
| GeForce GTX 650 TiBoost | GeForce GTX 660 | GeForce GTX 660 Ti | GeForce GTX 670 |
| GeForce GTX 670MX | GeForce GTX 675M | GeForce GTX 675MX | GeForce GTX 680 |
| GeForce GTX 680MX | GeForce GTX 690 | GeForce GTX 745 | GeForce GTX 750 |
| GeForce GTX 750 Ti | GeForce GTX 760 | GeForce GTX 760 Ti | GeForce GTX 765M |
| GeForce GTX 770 | GeForce GTX 775M | GeForce GTX 780 | GeForce GTX 780 Ti |
| GeForce GTX 850M | GeForce GTX 860M | GeForce GTX 870M | GeForce GTX 880M |
| GeForce GTX 950 | GeForce GTX 960 | GeForce GTX 960M | GeForce GTX 965M |
| GeForce GTX 970 | GeForce GTX 970M | GeForce GTX 980 | GeForce GTX 980 Ti |
| GeForce GTX 980M | GeForce GTX GTXTITAN | GeForce GTX GTXTITANBlack | GeForce GTX GTXTITANZ |
| GeForce GTX 1050 | GeForce GTX 1050 Ti | GeForce GTX 1060 | GeForce GTX 1060 with Max-Q |
| GeForce GTX 1630 | GeForce GTX 1650 | GeForce GTX 1650 SUPER | GeForce GTX 1650 Ti |
| GeForce GTX 1650 TiBoost | GeForce GTX 1650 with Max-Q | GeForce GTX 1660 | GeForce GTX 1660 SUPER |
| GeForce GTX 1660 Ti | GeForce GTX 1670 Ti | GeForce MX450 | GeForce RTX 1080 |
| GeForce RTX 1080 Ti | GeForce RTX 2060 | GeForce RTX 2060 SUPER | GeForce RTX 2060 with Max-Q |
| GeForce RTX 2070 | GeForce RTX 2070 SUPER | GeForce RTX 2070 with Max-Q | GeForce RTX 2080 |
| GeForce RTX 2080 SUPER | GeForce RTX 2080 Laptop GPU | GeForce RTX 3050 | GeForce RTX 3050 Laptop GPU |
| GeForce RTX 3060 | GeForce RTX 3060 Laptop GPU | GeForce RTX 4060 | GeForce RTX 4060 Laptop GPU |
| Quadro | TITANX | TITANXp | |

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
