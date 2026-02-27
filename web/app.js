const API = "";

async function getJson(path, options) {
  const res = await fetch(`${API}${path}`, options);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${path} failed: ${text}`);
  }
  return res.json();
}

function metricCard(label, value) {
  return `<div class="metric"><strong>${label}</strong><span>${value}</span></div>`;
}

function renderMilestones(rows) {
  const el = document.getElementById("milestones");
  el.innerHTML = rows.map((m) => `
    <article class="card">
      <span class="window">${m.window}</span>
      <h3>${m.title}</h3>
      <ul>${m.deliverables.map((d) => `<li>${d}</li>`).join("")}</ul>
    </article>
  `).join("");
}

function renderFeedback(rows) {
  const el = document.getElementById("feedbackList");
  if (!rows.length) {
    el.innerHTML = "<p>No feedback yet.</p>";
    return;
  }
  el.innerHTML = rows.slice(0, 8).map((r) => `
    <div class="row">
      <strong>${r.user_id}</strong> • ${r.feature} • <span class="tag ${r.severity}">${r.severity}</span>
      <div>${r.sentiment}: ${r.message}</div>
      <small>${new Date(r.created_at).toLocaleString()}</small>
    </div>
  `).join("");
}

async function boot() {
  const [health, roadmap, metrics, feedback] = await Promise.all([
    getJson("/api/health"),
    getJson("/api/roadmap"),
    getJson("/api/metrics"),
    getJson("/api/feedback")
  ]);

  document.getElementById("title").textContent = roadmap.project;
  document.getElementById("focus").textContent = roadmap.betaFocus;
  document.getElementById("assignee").textContent = `Assignee: ${roadmap.assignee}`;
  document.getElementById("date").textContent = `Date: ${roadmap.date}`;
  document.getElementById("health").textContent = `Service: ${health.status}`;

  const metricsEl = document.getElementById("metrics");
  metricsEl.innerHTML = [
    metricCard("Predictions", metrics.prediction_count),
    metricCard("Feedback Total", metrics.feedback_total),
    metricCard("Negative Feedback", metrics.feedback_negative),
    metricCard("High Severity", metrics.feedback_high_severity),
    metricCard("SLA (hrs)", metrics.feedback_response_sla_hours)
  ].join("");

  renderMilestones(roadmap.milestones || []);
  renderFeedback(feedback || []);
}

async function refreshPanels() {
  const [metrics, feedback] = await Promise.all([
    getJson("/api/metrics"),
    getJson("/api/feedback")
  ]);
  const metricsEl = document.getElementById("metrics");
  metricsEl.innerHTML = [
    metricCard("Predictions", metrics.prediction_count),
    metricCard("Feedback Total", metrics.feedback_total),
    metricCard("Negative Feedback", metrics.feedback_negative),
    metricCard("High Severity", metrics.feedback_high_severity),
    metricCard("SLA (hrs)", metrics.feedback_response_sla_hours)
  ].join("");
  renderFeedback(feedback || []);
}

document.getElementById("predictForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const payload = {
    account_id: String(form.get("account_id")),
    events_last_7d: Number(form.get("events_last_7d")),
    active_minutes_last_7d: Number(form.get("active_minutes_last_7d")),
    error_rate: Number(form.get("error_rate")),
    feedback_count_last_30d: Number(form.get("feedback_count_last_30d"))
  };
  const out = await getJson("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  document.getElementById("predictOut").textContent = JSON.stringify(out, null, 2);
  await refreshPanels();
});

document.getElementById("feedbackForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const payload = {
    user_id: String(form.get("user_id")),
    feature: String(form.get("feature")),
    sentiment: String(form.get("sentiment")),
    severity: String(form.get("severity")),
    message: String(form.get("message"))
  };
  const saved = await getJson("/api/feedback", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  });
  document.getElementById("feedbackOut").textContent = `Saved feedback #${saved.id}`;
  await refreshPanels();
});

boot().catch((err) => {
  document.body.innerHTML = `<main style="padding:2rem;font-family:sans-serif">App failed to load: ${err.message}</main>`;
});
