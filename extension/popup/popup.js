function showState(id) {
  ["state-loading", "state-no-tos", "state-error", "state-result"].forEach((s) => {
    document.getElementById(s).classList.add("hidden");
  });
  document.getElementById(id).classList.remove("hidden");
}

function renderResult(data) {
  document.getElementById("tldr-text").textContent = data.tldr;

  const list = document.getElementById("clauses-list");
  list.innerHTML = "";

  data.clauses.forEach((clause) => {
    const card = document.createElement("div");
    card.className = `clause-card severity-${clause.severity}`;

    card.innerHTML = `
      <p class="clause-quote">"${clause.quote}"</p>
      <p class="clause-plain">${clause.plain_english}</p>
      <div class="clause-meta">
        <span class="badge">${clause.category}</span>
        <span class="badge">${clause.severity.toUpperCase()}</span>
        <span class="badge concept">${clause.concept}</span>
      </div>
    `;

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
