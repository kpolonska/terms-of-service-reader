function showState(id) {
  ["state-loading", "state-no-tos", "state-error", "state-result"].forEach((s) => {
    document.getElementById(s).classList.add("hidden");
  });
  document.getElementById(id).classList.remove("hidden");
}

function renderResult(data) {
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

    card.appendChild(quote);
    card.appendChild(plain);
    card.appendChild(meta);
    list.appendChild(card);
  });

  showState("state-result");
}

function applyResult(result) {
  if (result.status === "success") {
    renderResult(result.data);
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
