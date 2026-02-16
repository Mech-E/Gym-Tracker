let draftSets = [];

function getApiUrl() {
  return localStorage.getItem("apiUrl") || "";
}
function saveApiUrl() {
  const v = document.getElementById("apiUrl").value.trim();
  localStorage.setItem("apiUrl", v);
  alert("Saved!");
  refreshExercises();
}

async function api(path, opts={}) {
  const base = getApiUrl();
  if (!base) throw new Error("Set API URL first");
  const res = await fetch(base + path, {
    headers: { "Content-Type": "application/json" },
    ...opts
  });
  if (!res.ok) {
    const txt = await res.text();
    throw new Error(txt);
  }
  return res.json();
}

async function refreshExercises() {
  const base = getApiUrl();
  document.getElementById("apiUrl").value = base;

  const list = await api("/exercises");
  const sel = document.getElementById("exerciseSelect");
  sel.innerHTML = "";
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
  await api("/exercises", { method: "POST", body: JSON.stringify({ name }) });
  document.getElementById("exName").value = "";
  refreshExercises();
}

function addSetToDraft() {
  const exercise_id = Number(document.getElementById("exerciseSelect").value);
  const weight = Number(document.getElementById("weight").value);
  const reps = Number(document.getElementById("reps").value);
  const rpeVal = document.getElementById("rpe").value;
  const rpe = rpeVal === "" ? null : Number(rpeVal);

  if (!exercise_id || !weight || !reps) return;

  draftSets.push({ exercise_id, weight, reps, rpe });
  renderDraft();
}

function renderDraft() {
  const out = draftSets.map((s, i) => `${i+1}) ex ${s.exercise_id} - ${s.weight} x ${s.reps}${s.rpe ? ` @RPE ${s.rpe}` : ""}`);
  document.getElementById("draftSets").textContent = out.join("\n");
}

async function saveWorkout() {
  if (draftSets.length === 0) return;
  await api("/workouts", { method: "POST", body: JSON.stringify({ notes: "", sets: draftSets }) });
  draftSets = [];
  renderDraft();
  alert("Workout saved!");
}

async function loadProgress() {
  const exercise_id = Number(document.getElementById("exerciseSelect").value);
  const data = await api(`/progress/${exercise_id}`);
  document.getElementById("progressOut").textContent =
    `Best Weight: ${data.best_weight}\nBest e1RM: ${data.best_e1rm}\nRecent sets:\n` +
    data.series.slice(-10).map(s => `- ${s.weight} x ${s.reps} (e1RM ${s.e1rm})`).join("\n");
}

if ("serviceWorker" in navigator) {
  navigator.serviceWorker.register("service-worker.js");
}

refreshExercises().catch(() => {});
