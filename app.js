let draftSets = [];

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
  document.getElementById("apiUrl").value = saved;

  const list = await api("/api/exercises/");
  const sel = document.getElementById("exerciseSelect");
  sel.innerHTML = "";

  if (!list || list.length === 0) {
    const o = document.createElement("option");
    o.value = "";
    o.textContent = "No exercises yet";
    sel.appendChild(o);
    return;
  }

  for (const ex of list) {
    const o = document.createElement("option");
    o.value = ex.id;
    o.textContent = ex.name;
    sel.appendChild(o);
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
  const exercise_id = Number(sel.value);
  const exercise_name = sel.options[sel.selectedIndex]?.textContent || "";

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

  const notes = document.getElementById("notes").value || "";

  // API expects exercise_id, reps, weight, rpe
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
  document.getElementById("notes").value = "";
  alert("Workout saved!");
}

async function loadProgress() {
  const exercise_id = Number(document.getElementById("exerciseSelect").value);
  if (!exercise_id) return;

  const data = await api(`/api/progress/${exercise_id}`);
  document.getElementById("progressOut").textContent =
    `Best Weight: ${data.best_weight}\n` +
    `Best e1RM: ${data.best_1rm}\n\n` +
    `Recent sets:\n` +
    data.series
      .slice(-10)
      .map(s => `- ${s.weight} x ${s.reps} (e1RM ${s.e1rm})`)
      .join("\n");
}

function wireButtons() {
  document.getElementById("saveApiUrlBtn").addEventListener("click", saveApiUrl);
  document.getElementById("addExerciseBtn").addEventListener("click", () => {
    addExercise().catch(err => setStatus(err.message, true));
  });
  document.getElementById("addSetBtn").addEventListener("click", addSetToDraft);
  document.getElementById("saveWorkoutBtn").addEventListener("click", () => {
    saveWorkout().catch(err => setStatus(err.message, true));
  });
  document.getElementById("loadProgressBtn").addEventListener("click", () => {
    loadProgress().catch(err => setStatus(err.message, true));
  });
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js").catch(() => {});
}

wireButtons();
refreshExercises().catch(() => {});
renderDraft();
