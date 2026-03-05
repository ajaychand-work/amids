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

function renderKpiSummary(payload) {
  const el = document.getElementById("kpiSummary");
  const roi = payload.summary_stats?.roi || {};
  const cac = payload.summary_stats?.cac || {};
  const cvr = payload.summary_stats?.lead_conversion_rate || {};
  el.innerHTML = `
    <div class="grid">
      <article class="card"><strong>ROI Mean</strong><div>${roi.mean ?? "n/a"}</div></article>
      <article class="card"><strong>CAC Median</strong><div>${cac.median ?? "n/a"}</div></article>
      <article class="card"><strong>Lead CVR Mean</strong><div>${cvr.mean ?? "n/a"}</div></article>
      <article class="card"><strong>Segments</strong><div>${payload.latest_segments?.length ?? 0}</div></article>
    </div>
  `;
}

function renderTrendSummary(payload) {
  const el = document.getElementById("trendSummary");
  const stats = payload.summary_stats || {};
  const anomalies = payload.anomalies || [];
  el.innerHTML = `
    <div class="grid">
      <article class="card"><strong>Revenue Mean</strong><div>${stats.mean ?? "n/a"}</div></article>
      <article class="card"><strong>Revenue Variance</strong><div>${stats.variance ?? "n/a"}</div></article>
      <article class="card"><strong>Anomalies</strong><div>${anomalies.length}</div></article>
      <article class="card"><strong>Observation Count</strong><div>${stats.count ?? 0}</div></article>
    </div>
  `;
}

function renderPerformanceSummary(payload) {
  const el = document.getElementById("performanceSummary");
  const riskRows = payload.risk_distribution || [];
  const monitorRows = payload.kpi_monitoring || [];

  const riskHtml = riskRows.map((r) => `
    <div class="row">
      <strong>${r.risk_band}</strong> • segments: ${r.segments} • avg risk: ${r.avg_risk_score}
    </div>
  `).join("");

  const monitorHtml = monitorRows.map((m) => `
    <div class="row">
      <strong>${m.metric}</strong> = ${m.value} • status: <span class="tag ${m.status === "critical" ? "high" : "low"}">${m.status}</span>
    </div>
  `).join("");

  el.innerHTML = `
    <h3>Risk Score Distribution</h3>
    ${riskHtml || "<p>No risk distribution data available.</p>"}
    <h3>KPI Monitoring</h3>
    ${monitorHtml || "<p>No KPI monitoring data available.</p>"}
  `;
}

function renderTopMetrics(metrics) {
  const metricsEl = document.getElementById("metrics");
  metricsEl.innerHTML = [
    metricCard("Predictions", metrics.prediction_count),
    metricCard("Feedback Total", metrics.feedback_total),
    metricCard("Negative Feedback", metrics.feedback_negative),
    metricCard("High Severity", metrics.feedback_high_severity),
    metricCard("Risk Mean", metrics.risk_score_mean ?? "n/a"),
    metricCard("SLA (hrs)", metrics.feedback_response_sla_hours)
  ].join("");
}

async function boot() {
  const [health, roadmap, metrics, feedback, kpis, trends, performance] = await Promise.all([
    getJson("/api/health"),
    getJson("/api/roadmap"),
    getJson("/api/metrics"),
    getJson("/api/feedback"),
    getJson("/api/dashboard/kpis"),
    getJson("/api/dashboard/trends"),
    getJson("/api/dashboard/performance")
  ]);

  document.getElementById("title").textContent = roadmap.project;
  document.getElementById("focus").textContent = roadmap.betaFocus;
  document.getElementById("assignee").textContent = `Assignee: ${roadmap.assignee}`;
  document.getElementById("date").textContent = `Date: ${roadmap.date}`;
  document.getElementById("health").textContent = `Service: ${health.status}`;

  renderTopMetrics(metrics);
  renderMilestones(roadmap.milestones || []);
  renderFeedback(feedback || []);
  renderKpiSummary(kpis);
  renderTrendSummary(trends);
  renderPerformanceSummary(performance);
}

async function refreshPanels() {
  const [metrics, feedback, kpis, trends, performance] = await Promise.all([
    getJson("/api/metrics"),
    getJson("/api/feedback"),
    getJson("/api/dashboard/kpis"),
    getJson("/api/dashboard/trends"),
    getJson("/api/dashboard/performance")
  ]);
  renderTopMetrics(metrics);
  renderFeedback(feedback || []);
  renderKpiSummary(kpis);
  renderTrendSummary(trends);
  renderPerformanceSummary(performance);
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
