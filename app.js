let draftSets = [];
let chart = null;

function normalizeBase(url) {
  // If user leaves blank, use same origin
  if (!url || !url.trim()) return window.location.origin;

  url = url.trim().replace(/\/+$/, ""); // remove trailing slashes
  return url;
}

function getApiUrl() {
  return normalizeBase(localStorage.getItem("apiUrl"));
}

function saveApiUrl() {
  const v = document.getElementById("apiUrl").value;
  localStorage.setItem("apiUrl", v.trim());
  setStatus(`Saved API URL: ${getApiUrl()}`);
  refreshExercises().catch(err => setStatus(err.message, true));
}

function setStatus(msg, isErr = false) {
  const el = document.getElementById("status");
  if (!el) return;
  el.textContent = msg;
  el.style.color = isErr ? "crimson" : "inherit";
}

async function api(path, opts = {}) {
  const base = getApiUrl();
  const url = base + path;

  const res = await fetch(url, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });

  if (!res.ok) {
    const txt = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${txt}`);
  }

  // some endpoints might return empty; handle safely
  const text = await res.text();
  return text ? JSON.parse(text) : null;
}

async function refreshExercises() {
  // show saved value in input
  const saved = localStorage.getItem("apiUrl") || "";
  const apiInput = document.getElementById("apiUrl");
  if (apiInput) apiInput.value = saved;

  const list = await api("/api/exercises/");

  // Exercise dropdown (for logging sets)
  const sel = document.getElementById("exerciseSelect");
  if (sel) {
    sel.innerHTML = "";
    if (!list || list.length === 0) {
      const o = document.createElement("option");
      o.value = "";
      o.textContent = "No exercises yet";
      sel.appendChild(o);
    } else {
      for (const ex of list) {
        const o = document.createElement("option");
        o.value = ex.id;
        o.textContent = ex.name;
        sel.appendChild(o);
      }
    }
  }

  // Progress selector dropdown (Bodyweight + exercises)
  const progSel = document.getElementById("progressSelect");
  if (progSel) {
    progSel.innerHTML = "";

    // Always include Bodyweight option first
    const bwOpt = document.createElement("option");
    bwOpt.value = "bodyweight";
    bwOpt.textContent = "Bodyweight";
    progSel.appendChild(bwOpt);

    if (list && list.length > 0) {
      for (const ex of list) {
        const o = document.createElement("option");
        o.value = `exercise:${ex.id}`;
        o.textContent = ex.name;
        progSel.appendChild(o);
      }
    }
  }
}

async function addExercise() {
  const name = document.getElementById("exName").value.trim();
  if (!name) return;

  await api("/api/exercises/", {
    method: "POST",
    body: JSON.stringify({ name }),
  });

  document.getElementById("exName").value = "";
  await refreshExercises();
}

function addSetToDraft() {
  const sel = document.getElementById("exerciseSelect");
  const exercise_id = Number(sel?.value);
  const exercise_name = sel?.options?.[sel.selectedIndex]?.textContent || "";

  const weight = Number(document.getElementById("weight").value);
  const reps = Number(document.getElementById("reps").value);
  const rpeVal = document.getElementById("rpe").value.trim();
  const rpe = rpeVal === "" ? null : Number(rpeVal);

  if (!exercise_id || !weight || !reps) return;

  draftSets.push({ exercise_id, exercise_name, weight, reps, rpe });
  renderDraft();

  document.getElementById("weight").value = "";
  document.getElementById("reps").value = "";
  document.getElementById("rpe").value = "";
}

function renderDraft() {
  const el = document.getElementById("draftSets");
  if (!el) return;

  if (draftSets.length === 0) {
    el.textContent = "(none)";
    return;
  }
  el.textContent = draftSets
    .map(
      (s, i) =>
        `${i + 1}) ${s.exercise_name} - ${s.weight} x ${s.reps}` +
        (s.rpe != null ? ` @RPE ${s.rpe}` : "")
    )
    .join("\n");
}

async function saveWorkout() {
  if (draftSets.length === 0) return;

  const notesEl = document.getElementById("notes");
  const notes = notesEl ? (notesEl.value || "") : "";

  const payload = {
    notes,
    sets: draftSets.map(s => ({
      exercise_id: s.exercise_id,
      reps: s.reps,
      weight: s.weight,
      rpe: s.rpe,
    })),
  };

  await api("/api/workouts/", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  draftSets = [];
  renderDraft();
  if (notesEl) notesEl.value = "";
  alert("Workout saved!");
}

// -------------------------
// ✅ NEW: Bodyweight logging
// -------------------------
async function logBodyweight() {
  const bwEl = document.getElementById("bwValue");
  if (!bwEl) return;

  const w = Number(bwEl.value);
  if (!w) return;

  await api("/api/bodyweight/", {
    method: "POST",
    body: JSON.stringify({ weight: w, notes: "" }),
  });

  bwEl.value = "";
  setStatus("Bodyweight logged!");
}

// -------------------------
// ✅ NEW: Graph/Progress view
// -------------------------
function destroyChartIfAny() {
  if (chart) {
    chart.destroy();
    chart = null;
  }
}

function renderChart(labels, values, labelText) {
  const canvas = document.getElementById("progressChart");
  if (!canvas) return;

  destroyChartIfAny();

  chart = new Chart(canvas, {
    type: "line",
    data: {
      labels,
      datasets: [
        {
          label: labelText,
          data: values,
          tension: 0.2,
          pointRadius: 2,
        },
      ],
    },
    options: {
      responsive: true,
      parsing: false,
      plugins: {
        legend: { display: true },
      },
      scales: {
        x: { ticks: { maxRotation: 0 } },
      },
    },
  });
}

function setProgressStats(text) {
  const el = document.getElementById("progressStats");
  if (!el) return;
  el.textContent = text;
}

async function loadSelectedProgressAndGraph() {
  const sel = document.getElementById("progressSelect");
  if (!sel) return;

  const choice = sel.value;

  if (choice === "bodyweight") {
    // expects backend endpoint: GET /api/progress/bodyweight
    const data = await api("/api/progress/bodyweight");

    const labels = (data.series || []).map(p => new Date(p.t).toLocaleDateString());
    const values = (data.series || []).map(p => p.weight);

    renderChart(labels, values, "Bodyweight");
    setProgressStats(`Entries: ${values.length} | Best: ${data.best_weight}`);
    return;
  }

  if (choice.startsWith("exercise:")) {
    const exerciseId = Number(choice.split(":")[1]);
    const data = await api(`/api/progress/${exerciseId}`);

    // We’ll graph e1RM over time if available; otherwise weight
    const series = data.series || [];
    const labels = series.map(p => new Date(p.t).toLocaleDateString());
    const values = series.map(p => (p.e1rm != null ? p.e1rm : p.weight));

    // Use label from dropdown text
    const labelText = sel.options[sel.selectedIndex]?.textContent || "Exercise";

    renderChart(labels, values, `${labelText} (e1RM)`);
    setProgressStats(`Best Weight: ${data.best_weight} | Best e1RM: ${data.best_1rm}`);
    return;
  }
}

// Old text-based progress (optional) — keep if your HTML still has progressOut
async function loadProgressTextFallback() {
  const exercise_id = Number(document.getElementById("exerciseSelect")?.value);
  if (!exercise_id) return;

  const data = await api(`/api/progress/${exercise_id}`);
  const out = document.getElementById("progressOut");
  if (!out) return;

  out.textContent =
    `Best Weight: ${data.best_weight}\n` +
    `Best e1RM: ${data.best_1rm}\n\n` +
    `Recent sets:\n` +
    (data.series || [])
      .slice(-10)
      .map(s => `- ${s.weight} x ${s.reps} (e1RM ${s.e1rm})`)
      .join("\n");
}

function wireButtons() {
  document.getElementById("saveApiUrlBtn")?.addEventListener("click", saveApiUrl);

  document.getElementById("addExerciseBtn")?.addEventListener("click", () => {
    addExercise().catch(err => setStatus(err.message, true));
  });

  document.getElementById("addSetBtn")?.addEventListener("click", addSetToDraft);

  document.getElementById("saveWorkoutBtn")?.addEventListener("click", () => {
    saveWorkout().catch(err => setStatus(err.message, true));
  });

  // ✅ NEW: log bodyweight
  document.getElementById("logBWBtn")?.addEventListener("click", () => {
    logBodyweight().catch(err => setStatus(err.message, true));
  });

  // ✅ NEW: graph progress
  document.getElementById("graphBtn")?.addEventListener("click", () => {
    loadSelectedProgressAndGraph().catch(err => setStatus(err.message, true));
  });

  // If your old button still exists, keep it wired
  document.getElementById("loadProgressBtn")?.addEventListener("click", () => {
    loadProgressTextFallback().catch(err => setStatus(err.message, true));
  });
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js").catch(() => {});
}

wireButtons();
refreshExercises().catch(() => {});
renderDraft();