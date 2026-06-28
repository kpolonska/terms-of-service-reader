const EXPLAIN_URL = "http://localhost:8000/explain";

async function handleExplain(clause, card, btn) {
  btn.disabled = true;
  btn.textContent = "Loading…";

  try {
    const res = await fetch(EXPLAIN_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ quote: clause.quote, category: clause.category }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    btn.remove();
    renderExplanation(card, data);
  } catch {
    btn.disabled = false;
    btn.textContent = "Explain more";
  }
}

function renderExplanation(card, data) {
  const section = document.createElement("div");
  section.className = "explain-section";

  const makeBlock = (label, text) => {
    const wrap = document.createElement("div");
    wrap.className = "explain-block";

    const heading = document.createElement("p");
    heading.className = "explain-heading";
    heading.textContent = label;

    const body = document.createElement("p");
    body.className = "explain-body";
    body.textContent = text;

    wrap.appendChild(heading);
    wrap.appendChild(body);
    return wrap;
  };

  section.appendChild(makeBlock("What this really means", data.detailed_explanation));
  section.appendChild(makeBlock("Real-world example", data.real_world_example));
  section.appendChild(makeBlock("What you can do", data.what_you_can_do));

  card.appendChild(section);
}

function showState(id) {
  ["state-loading", "state-no-tos", "state-error", "state-result"].forEach((s) => {
    document.getElementById(s).classList.add("hidden");
  });
  document.getElementById(id).classList.remove("hidden");
}

function renderResult(data, domain) {
  if (data.risk) {
    const badge = document.getElementById("risk-badge");
    const label = data.risk.label.toLowerCase();
    badge.className = `risk-badge risk-${label}`;
    document.getElementById("risk-score").textContent = `${data.risk.score}/10`;
    document.getElementById("risk-label").textContent = data.risk.label;
  }

  document.getElementById("tldr-text").textContent = data.tldr;

  const list = document.getElementById("clauses-list");
  list.innerHTML = "";

  data.clauses.forEach((clause) => {
    const card = document.createElement("div");
    card.className = `clause-card severity-${clause.severity}`;

    const quote = document.createElement("p");
    quote.className = "clause-quote";
    quote.textContent = `"${clause.quote}"`;

    const plain = document.createElement("p");
    plain.className = "clause-plain";
    plain.textContent = clause.plain_english;

    const meta = document.createElement("div");
    meta.className = "clause-meta";

    const makeBadge = (text, extra = "") => {
      const span = document.createElement("span");
      span.className = `badge${extra ? " " + extra : ""}`;
      span.textContent = text;
      return span;
    };

    meta.appendChild(makeBadge(clause.category.replaceAll("_", " ")));
    meta.appendChild(makeBadge(clause.severity.toUpperCase(), "severity-badge"));
    meta.appendChild(makeBadge(clause.concept, "concept"));

    const explainBtn = document.createElement("button");
    explainBtn.className = "explain-btn";
    explainBtn.textContent = "Explain more";
    explainBtn.addEventListener("click", () => handleExplain(clause, card, explainBtn));

    card.appendChild(quote);
    card.appendChild(plain);
    card.appendChild(meta);
    card.appendChild(explainBtn);
    list.appendChild(card);
  });

  if (domain) {
    const downloadBtn = document.createElement("button");
    downloadBtn.className = "download-btn";
    downloadBtn.textContent = "Download PDF Report";
    downloadBtn.addEventListener("click", () => {
      chrome.tabs.create({ url: `http://localhost:8000/report/${domain}` });
    });
    document.getElementById("clauses-section").appendChild(downloadBtn);
  }

  showState("state-result");
}

function applyResult(result) {
  if (result.status === "success") {
    renderResult(result.data, result.domain);
  } else if (result.status === "error") {
    showState("state-error");
    document.getElementById("error-detail").textContent = result.data?.message ?? "";
  } else {
    showState("state-no-tos");
  }
}

async function init() {
  showState("state-loading");

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const result = await chrome.runtime.sendMessage({
    type: "GET_RESULT",
    tabId: tab.id,
  });

  if (!result || result.status === "no_tos") {
    showState("state-no-tos");
    return;
  }

  if (result.status === "loading") {
    showState("state-loading");
    // Auto-update when the service worker writes the finished result to storage
    const storageKey = `result_${tab.id}`;
    const listener = (changes, area) => {
      if (area !== "session" || !changes[storageKey]) return;
      chrome.storage.onChanged.removeListener(listener);
      applyResult(changes[storageKey].newValue);
    };
    chrome.storage.onChanged.addListener(listener);
    return;
  }

  applyResult(result);
}

document.addEventListener("DOMContentLoaded", init);
