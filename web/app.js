const $ = (selector) => document.querySelector(selector);

const state = {
  path: "",
  detected: null,
  lastState: null,
  profiles: [],
  defaultProfile: "rtx5080m",
};

function toast(message, isError = false) {
  const node = $("#toast");
  node.textContent = message;
  node.style.borderColor = isError ? "var(--danger)" : "var(--line)";
  node.classList.add("show");
  clearTimeout(toast.timer);
  toast.timer = setTimeout(() => node.classList.remove("show"), 4200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!response.ok || data.ok === false) {
    throw new Error(data.error || `HTTP ${response.status}`);
  }
  return data;
}

function setBusy(button, busy, text) {
  if (!button) return;
  if (busy) {
    button.dataset.oldText = button.textContent;
    button.textContent = text || "Processing...";
    button.disabled = true;
  } else {
    button.textContent = button.dataset.oldText || button.textContent;
    button.disabled = false;
  }
}

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem("nte-rt-theme", theme);
  $("#themeToggle").textContent = theme === "dark" ? "Dark" : "Light";
}

function currentMode() {
  return document.querySelector("input[name='mode']:checked")?.value || "dxgi";
}

function currentProfile() {
  return document.querySelector("input[name='profile']:checked")?.value || state.defaultProfile || "rtx5080m";
}

function processText(processes) {
  if (!processes || processes.length === 0) return "Not running";
  const names = [...new Set(processes.map((item) => item.ProcessName || item.processName).filter(Boolean))];
  return names.join(", ");
}

function findProfileByInstall(install) {
  const ini = install?.optScalerIni || {};
  const deviceId = (ini.SpoofedDeviceId || "").toLowerCase();
  const gpuName = (ini.SpoofedGPUName || "").toLowerCase();
  return state.profiles.find((profile) => (
    (profile.deviceId || "").toLowerCase() === deviceId ||
    (profile.gpuName || "").toLowerCase() === gpuName
  ));
}

function setProfileSelection(profileId) {
  const input = document.querySelector(`input[name='profile'][value='${profileId}']`);
  if (input) input.checked = true;
  const selected = state.profiles.find((profile) => profile.id === currentProfile());
  $("#profileBadge").textContent = selected ? selected.label : "Target GPU";
}

function renderProfiles(profiles, defaultProfile) {
  if (!Array.isArray(profiles) || profiles.length === 0) return;
  const selectedBefore = currentProfile();
  state.profiles = profiles;
  state.defaultProfile = defaultProfile || state.defaultProfile;
  const selectedId = profiles.some((profile) => profile.id === selectedBefore) ? selectedBefore : state.defaultProfile;
  const grid = $("#profileGrid");
  grid.innerHTML = "";
  profiles.forEach((profile) => {
    const label = document.createElement("label");
    label.className = "profile-option";
    const checked = profile.id === selectedId ? "checked" : "";
    label.innerHTML = `
      <input type="radio" name="profile" value="${profile.id}" ${checked} />
      <span>
        <strong>${profile.label}</strong>
        <small>${profile.gpuName} / ${profile.deviceId}</small>
      </span>
    `;
    label.querySelector("input").addEventListener("change", () => setProfileSelection(profile.id));
    grid.appendChild(label);
  });
  setProfileSelection(document.querySelector("input[name='profile']:checked")?.value || selectedId);
}

function updateHero(install) {
  const installed = install?.installed;
  $("#statusGlyph").textContent = installed ? "Active" : "Inactive";
  $("#statusLine").textContent = installed ? "Ray tracing unlock is installed" : "Ray tracing unlock not installed";
  $("#installBadge").textContent = installed ? "Installed" : "Not installed";
}

function updateDetected(detected) {
  state.detected = detected;
  if (!detected) return;
  state.path = detected.win64;
  $("#gamePath").value = detected.win64;
  $("#pathHint").textContent = `Game executable: ${detected.exe}`;
  updateHero(detected.install);
  renderInstallState(detected.install);
  const installedProfile = findProfileByInstall(detected.install);
  if (installedProfile) setProfileSelection(installedProfile.id);
  renderBackups(detected.backups || []);
}

function renderBackups(backups) {
  const select = $("#backupSelect");
  select.innerHTML = "";
  $("#backupCount").textContent = `${backups.length} backup(s)`;
  $("#openBackupBtn").disabled = backups.length === 0;
  if (backups.length === 0) {
    const option = document.createElement("option");
    option.textContent = "No backups";
    option.value = "";
    select.appendChild(option);
    return;
  }
  backups.forEach((backup) => {
    const option = document.createElement("option");
    option.value = backup.id;
    option.textContent = `${backup.id} / ${backup.mode || "unknown"} / ${backup.profile || "profile"}`;
    option.dataset.path = backup.path;
    select.appendChild(option);
  });
}

function renderInstallState(install) {
  if (!install) {
    $("#installState").textContent = "Not detected.";
    return;
  }
  const lines = [
    `installed: ${install.installed}`,
    `winmm: ${install.winmm ? `${install.winmm.size} bytes, optiscaler=${install.winmm.looksLikeOptiScaler}` : "missing"}`,
    `OptiScaler dir: ${install.optScalerDirExists}`,
    `legacy DLSSTweaks ini: ${install.legacyDlsstweaksIni}`,
    "",
    "[OptiScaler.ini]",
  ];
  const ini = install.optScalerIni || {};
  Object.keys(ini).sort().forEach((key) => lines.push(`${key}=${ini[key]}`));
  const matched = findProfileByInstall(install);
  if (matched) {
    lines.splice(4, 0, `matchedProfile: ${matched.label}`);
  }
  $("#installState").textContent = lines.join("\n");
}

function updateStateView(data) {
  state.lastState = data;
  renderProfiles(data.profiles || [], data.defaultProfile);
  $("#versionText").textContent = data.version || "0.1.0";
  if (data.name) document.title = `${data.name} / ${data.englishName || "NTE Ray Tracing Panel"}`;
  const gpu = data.nvidia?.[0];
  $("#gpuName").textContent = gpu ? `${gpu.Name} (${gpu.DeviceIdHex || "unknown"})` : "No NVIDIA GPU detected";
  $("#procmonState").textContent = data.procmon?.present ? "Driver present" : "Clean";
  $("#processState").textContent = processText(data.processes || []);
  $("#optiBadge").textContent = data.optiscaler ? `Ready ${data.optiscaler.tag}` : "Not ready";
  if (data.selectedDetected && !data.selectedDetected.error) {
    updateDetected(data.selectedDetected);
  } else if (data.commonDetected) {
    updateDetected(data.commonDetected);
  } else {
    // No game found yet — pre-fill the default path so the user can see
    // where the tool will look and just click Detect to confirm
    if (!$("#gamePath").value.trim() && data.defaultGamePath) {
      $("#gamePath").value = data.defaultGamePath;
      $("#pathHint").textContent = "Default install path — click Detect to confirm.";
    }
    updateHero(null);
  }
}

async function refreshState() {
  const path = $("#gamePath").value.trim();
  const url = path ? `/api/state?path=${encodeURIComponent(path)}` : "/api/state";
  const data = await api(url);
  updateStateView(data);
}

async function detectGame() {
  const button = $("#detectBtn");
  setBusy(button, true, "Detecting...");
  try {
    const data = await api("/api/detect", {
      method: "POST",
      body: JSON.stringify({ path: $("#gamePath").value.trim() }),
    });
    updateDetected(data.detected);
    toast("NTE Win64 directory detected.");
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(button, false);
  }
}

async function browseGame() {
  const button = $("#browseBtn");
  setBusy(button, true, "Selecting...");
  try {
    const data = await api("/api/browse", { method: "POST", body: "{}" });
    if (data.path) {
      $("#gamePath").value = data.path;
      await detectGame();
    }
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(button, false);
  }
}

async function downloadOpti(force = false) {
  const button = force ? $("#forceDownloadBtn") : $("#downloadBtn");
  setBusy(button, true, force ? "Re-downloading..." : "Downloading...");
  showProgress("Connecting...", 0);
  try {
    const data = await api("/api/download", {
      method: "POST",
      body: JSON.stringify({ force }),
    });
    if (!data.downloading) {
      // Resolved instantly (cached) — no SSE needed
      hideProgress();
      $("#optiBadge").textContent = `Ready ${data.optiscaler.tag}`;
      toast(data.optiscaler.downloaded ? "OptiScaler downloaded and extracted." : "OptiScaler is ready.");
      await refreshState();
      return;
    }
    // Stream progress via SSE
    await new Promise((resolve, reject) => {
      const es = new EventSource("/api/download/progress");
      es.onmessage = (e) => {
        try {
          const snap = JSON.parse(e.data);
          if (snap.phase === "downloading") {
            const label = snap.total > 0
              ? `Downloading ${snap.filename} — ${formatBytes(snap.downloaded)} / ${formatBytes(snap.total)}`
              : `Downloading ${snap.filename} — ${formatBytes(snap.downloaded)}`;
            showProgress(label, snap.pct);
          } else if (snap.phase === "extracting") {
            showProgress(`Extracting ${snap.filename}...`, 100);
          } else if (snap.phase === "done") {
            showProgress("Done!", 100);
            es.close();
            resolve();
          } else if (snap.phase === "error") {
            es.close();
            reject(new Error(snap.error || "Download failed."));
          }
        } catch (_) {}
      };
      es.onerror = () => { es.close(); reject(new Error("Progress stream disconnected.")); };
    });
    hideProgress();
    await refreshState();
    const stage = state.lastState?.optiscaler;
    if (stage) $("#optiBadge").textContent = `Ready ${stage.tag}`;
    toast("OptiScaler downloaded and extracted.");
  } catch (error) {
    hideProgress();
    toast(error.message, true);
  } finally {
    setBusy(button, false);
  }
}

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function showProgress(label, pct) {
  let bar = $("#downloadProgress");
  if (!bar) {
    bar = document.createElement("div");
    bar.id = "downloadProgress";
    bar.innerHTML = `
      <div class="progress-label" id="progressLabel"></div>
      <div class="progress-track">
        <div class="progress-fill" id="progressFill"></div>
      </div>
      <div class="progress-pct" id="progressPct"></div>
    `;
    // Insert after the download buttons' parent card
    const downloadBtn = $("#downloadBtn");
    downloadBtn.closest(".card").appendChild(bar);
  }
  bar.style.display = "block";
  $("#progressLabel").textContent = label;
  $("#progressFill").style.width = `${Math.min(pct, 100)}%`;
  $("#progressPct").textContent = pct > 0 ? `${pct.toFixed(1)}%` : "";
}

function hideProgress() {
  const bar = $("#downloadProgress");
  if (bar) bar.style.display = "none";
}

async function installSpoof() {
  const button = $("#installBtn");
  setBusy(button, true, "Installing...");
  try {
    const data = await api("/api/install", {
      method: "POST",
      body: JSON.stringify({
        path: $("#gamePath").value.trim(),
        mode: currentMode(),
        profile: currentProfile(),
        closeGame: $("#closeGame").checked,
      }),
    });
    updateDetected(data.detected);
    toast(`Installation complete. Backup created: ${data.backup}`);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(button, false);
  }
}

async function restoreBackup() {
  const button = $("#restoreBtn");
  const backup = $("#backupSelect").value;
  if (!backup) {
    toast("No backup selected.", true);
    return;
  }
  setBusy(button, true, "Restoring...");
  try {
    const data = await api("/api/restore", {
      method: "POST",
      body: JSON.stringify({
        path: $("#gamePath").value.trim(),
        backup,
        closeGame: $("#closeGame").checked,
      }),
    });
    updateDetected(data.detected);
    toast(data.message);
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(button, false);
  }
}

async function refreshLog() {
  const button = $("#logBtn");
  setBusy(button, true, "Reading...");
  try {
    const path = encodeURIComponent($("#gamePath").value.trim());
    const data = await api(`/api/log?path=${path}`);
    $("#logView").textContent = data.log.exists ? data.log.tail || "Log is empty." : "OptiScaler.log has not been generated yet.";
  } catch (error) {
    toast(error.message, true);
  } finally {
    setBusy(button, false);
  }
}

async function shutdown() {
  try {
    await api("/api/shutdown", { method: "POST", body: "{}" });
  } catch (_) {
    // Server closing mid-response is expected — not an error
  }
  window.close();
}

function bindNav() {
  const links = [...document.querySelectorAll(".nav a")];
  links.forEach((link) => {
    link.addEventListener("click", () => {
      links.forEach((item) => item.classList.remove("active"));
      link.classList.add("active");
    });
  });
}

function bindEvents() {
  $("#themeToggle").addEventListener("click", () => {
    setTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  });
  $("#browseBtn").addEventListener("click", browseGame);
  $("#detectBtn").addEventListener("click", detectGame);
  $("#refreshBtn").addEventListener("click", () => refreshState().catch((error) => toast(error.message, true)));
  $("#downloadBtn").addEventListener("click", () => downloadOpti(false));
  $("#forceDownloadBtn").addEventListener("click", () => downloadOpti(true));
  $("#installBtn").addEventListener("click", installSpoof);
  $("#restoreBtn").addEventListener("click", restoreBackup);
  $("#logBtn").addEventListener("click", refreshLog);
  $("#shutdownBtn").addEventListener("click", shutdown);
  $("#shutdownBtnTop").addEventListener("click", shutdown);
  $("#openBackupBtn").addEventListener("click", () => {
    const selected = $("#backupSelect").selectedOptions[0];
    toast(selected?.dataset.path || "No backup path found.");
  });
}

function init() {
  setTheme(localStorage.getItem("nte-rt-theme") || "light");
  bindNav();
  bindEvents();
  refreshState().catch((error) => toast(error.message, true));
}

init();
