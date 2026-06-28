const API_URL = "http://localhost:8000/stats";

const BAR_COLOR = "#1e2952";
const SEVERITY_COLORS = { high: "#991b1b", medium: "#92400e", low: "#065f46" };

function show(id) {
  ["state-loading", "state-empty", "state-stats"].forEach((s) => {
    document.getElementById(s).classList.add("hidden");
  });
  document.getElementById(id).classList.remove("hidden");
}

function drawHorizontalBars(canvasId, data) {
  const entries = Object.entries(data);
  if (!entries.length) return;

  const canvas = document.getElementById(canvasId);
  const rowH = 22;
  const labelW = 170;
  const barMaxW = 160;
  const padding = 8;

  canvas.width = 348;
  canvas.height = entries.length * rowH + padding * 2;

  const ctx = canvas.getContext("2d");
  const maxVal = Math.max(...entries.map(([, v]) => v));

  entries.forEach(([key, val], i) => {
    const y = padding + i * rowH;
    const barW = maxVal > 0 ? Math.round((val / maxVal) * barMaxW) : 0;

    // label
    ctx.fillStyle = "#555";
    ctx.font = "11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    ctx.textBaseline = "middle";
    const label = key.replace(/_/g, " ").replace(/\(.*\)/, "").trim();
    ctx.fillText(label.length > 22 ? label.slice(0, 21) + "…" : label, 0, y + rowH / 2);

    // bar
    ctx.fillStyle = BAR_COLOR;
    ctx.globalAlpha = 0.85;
    ctx.beginPath();
    ctx.roundRect(labelW, y + 4, barW || 2, rowH - 8, 3);
    ctx.fill();
    ctx.globalAlpha = 1;

    // count
    ctx.fillStyle = "#888";
    ctx.font = "10px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    ctx.fillText(val, labelW + barW + 5, y + rowH / 2);
  });
}

function drawSeverityBars(data) {
  const canvas = document.getElementById("chart-severity");
  const entries = [
    ["high", data.high ?? 0],
    ["medium", data.medium ?? 0],
    ["low", data.low ?? 0],
  ];
  const rowH = 22;
  const labelW = 60;
  const barMaxW = 240;
  const padding = 8;

  canvas.width = 348;
  canvas.height = entries.length * rowH + padding * 2;

  const ctx = canvas.getContext("2d");
  const maxVal = Math.max(...entries.map(([, v]) => v), 1);

  entries.forEach(([key, val], i) => {
    const y = padding + i * rowH;
    const barW = Math.round((val / maxVal) * barMaxW);

    ctx.fillStyle = "#555";
    ctx.font = "11px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    ctx.textBaseline = "middle";
    ctx.fillText(key.charAt(0).toUpperCase() + key.slice(1), 0, y + rowH / 2);

    ctx.fillStyle = SEVERITY_COLORS[key];
    ctx.globalAlpha = 0.85;
    ctx.beginPath();
    ctx.roundRect(labelW, y + 4, barW || 2, rowH - 8, 3);
    ctx.fill();
    ctx.globalAlpha = 1;

    ctx.fillStyle = "#888";
    ctx.font = "10px -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif";
    ctx.fillText(val, labelW + barW + 5, y + rowH / 2);
  });
}

function renderDomains(domains) {
  const list = document.getElementById("domains-list");
  list.replaceChildren();

  if (!domains.length) {
    const p = document.createElement("p");
    p.className = "muted";
    p.textContent = "No domains yet.";
    list.appendChild(p);
    return;
  }

  domains.forEach((d) => {
    const row = document.createElement("div");
    row.className = "domain-row";

    const name = document.createElement("span");
    name.className = "domain-name";
    name.textContent = d.domain;

    const score = document.createElement("span");
    score.className = `domain-score label-${d.label.toLowerCase()}`;
    score.textContent = `${d.score}/10 · ${d.label}`;

    row.appendChild(name);
    row.appendChild(score);
    list.appendChild(row);
  });
}

async function init() {
  try {
    const res = await fetch(API_URL);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    if (!data.total_analyzed) {
      show("state-empty");
      return;
    }

    document.getElementById("total-count").textContent = data.total_analyzed;
    document.getElementById("avg-score").textContent = `${data.average_score}/10`;

    renderDomains(data.most_dangerous_domains);
    drawHorizontalBars("chart-categories", data.category_distribution);
    drawHorizontalBars("chart-concepts", data.concept_distribution);
    drawSeverityBars(data.severity_distribution);

    show("state-stats");
  } catch {
    show("state-empty");
  }
}

document.addEventListener("DOMContentLoaded", init);
