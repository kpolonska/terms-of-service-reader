const EXPLAIN_URL = "https://terms-of-service-reader.vercel.app/explain";

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

const SUBSCRIBE_URL = "https://terms-of-service-reader.vercel.app/subscribe";

async function initSubscribeButton(domain) {
  const row = document.getElementById("subscribe-row");
  const btn = document.getElementById("subscribe-btn");

  if (!domain) {
    row.classList.add("hidden");
    return;
  }

  row.classList.remove("hidden");

  const { subscriptions = [] } = await chrome.storage.local.get("subscriptions");
  let subscribed = subscriptions.includes(domain);

  const update = () => {
    btn.textContent = subscribed ? "Unsubscribe from changes" : "Subscribe to changes";
    btn.classList.toggle("subscribed", subscribed);
  };
  update();

  btn.addEventListener("click", async () => {
    const stored = await chrome.storage.local.get("subscriptions");
    const list = stored.subscriptions ?? [];

    if (subscribed) {
      const next = list.filter((d) => d !== domain);
      await chrome.storage.local.set({ subscriptions: next });
      fetch(`${SUBSCRIBE_URL}/${encodeURIComponent(domain)}`, { method: "DELETE" }).catch(() => {});
      subscribed = false;
    } else {
      list.push(domain);
      await chrome.storage.local.set({ subscriptions: list });
      fetch(SUBSCRIBE_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ domain }),
      }).catch(() => {});
      subscribed = true;
    }
    update();
  });
}

function renderDiff(diff) {
  const section = document.getElementById("diff-section");
  const list = document.getElementById("diff-list");
  list.replaceChildren();

  if (!diff || !diff.has_changes) {
    section.classList.add("hidden");
    return;
  }

  section.classList.remove("hidden");

  const DIRECTION_ICON = { worse: "↑", better: "↓", new: "+", removed: "−" };
  const DIRECTION_CLASS = { worse: "diff-worse", better: "diff-better", new: "diff-new", removed: "diff-removed" };

  diff.changed_clauses.forEach((item) => {
    const row = document.createElement("div");
    row.className = `diff-row ${DIRECTION_CLASS[item.direction] ?? ""}`;

    const icon = document.createElement("span");
    icon.className = "diff-icon";
    icon.textContent = DIRECTION_ICON[item.direction] ?? "?";

    const label = document.createElement("span");
    label.className = "diff-label";
    label.textContent = item.category.replaceAll("_", " ");

    const detail = document.createElement("span");
    detail.className = "diff-detail";
    if (item.direction === "new") {
      detail.textContent = `new · ${item.current_severity}`;
    } else if (item.direction === "removed") {
      detail.textContent = "removed";
    } else {
      detail.textContent = `${item.previous_severity} → ${item.current_severity}`;
    }

    row.appendChild(icon);
    row.appendChild(label);
    row.appendChild(detail);
    list.appendChild(row);
  });

  const date = new Date(diff.previous_analyzed_at);
  const stamp = document.createElement("p");
  stamp.className = "diff-stamp";
  stamp.textContent = `vs. analysis from ${date.toLocaleDateString()}`;
  list.appendChild(stamp);
}

function renderAlternatives(alternatives) {
  const section = document.getElementById("alternatives-section");
  const list = document.getElementById("alternatives-list");
  list.replaceChildren();

  if (!alternatives.length) {
    section.classList.add("hidden");
    return;
  }

  section.classList.remove("hidden");

  alternatives.forEach((alt) => {
    const card = document.createElement("div");
    card.className = "alt-card";
    if (alt.url) card.style.cursor = "pointer";

    const top = document.createElement("div");
    top.className = "alt-top";

    const name = document.createElement("span");
    name.className = "alt-name";
    name.textContent = alt.name;

    const url = document.createElement("span");
    url.className = "alt-url";
    url.textContent = alt.url;

    top.appendChild(name);
    top.appendChild(url);

    const reason = document.createElement("p");
    reason.className = "alt-reason";
    reason.textContent = alt.reason;

    card.appendChild(top);
    card.appendChild(reason);

    if (alt.url) {
      card.addEventListener("click", () => {
        const href = alt.url.startsWith("http") ? alt.url : `https://${alt.url}`;
        chrome.tabs.create({ url: href });
      });
    }

    list.appendChild(card);
  });
}

const PROFILE_DESCS = {
  general:    "Standard analysis of key clauses and risks.",
  journalist: "Focus on data collection, surveillance, and press freedom clauses.",
  activist:   "Highlights censorship, account termination, and civil rights risks.",
  business:   "Examines liability, IP ownership, and commercial use restrictions.",
};

function showState(id) {
  ["state-idle", "state-loading", "state-no-tos", "state-error", "state-result"].forEach((s) => {
    document.getElementById(s).classList.add("hidden");
  });
  document.getElementById(id).classList.remove("hidden");
}

function renderResult(data, domain) {
  showState("state-result");
  initSubscribeButton(domain);

  if (data.risk) {
    const card = document.getElementById("risk-badge");
    const label = data.risk.label.toLowerCase();
    card.className = `risk-card risk-${label}`;
    document.getElementById("risk-score").textContent = `${data.risk.score}/10`;
    document.getElementById("risk-label").textContent = data.risk.label;
    const bar = document.getElementById("risk-bar");
    if (bar) bar.style.width = `${(data.risk.score / 10) * 100}%`;
  }

  renderDiff(data.diff ?? null);
  renderAlternatives(data.alternatives ?? []);

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
      chrome.tabs.create({ url: `https://terms-of-service-reader.vercel.app/report/${domain}` });
    });
    document.getElementById("clauses-section").appendChild(downloadBtn);
  }

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

let activeProfile = "general";

async function initProfile() {
  const select = document.getElementById("profile-select");
  const stored = await chrome.storage.local.get("profile");
  activeProfile = stored.profile ?? "general";
  if (select) select.value = activeProfile;

  if (select) {
    select.addEventListener("change", () => {
      const newProfile = select.value;
      if (newProfile !== activeProfile) {
        activeProfile = newProfile;
        chrome.storage.local.set({ profile: activeProfile });
        // Reload popup to show idle state with new profile
        location.reload();
      }
    });
  }
}

function initIdleProfilePicker() {
  const btns = document.querySelectorAll(".profile-btn");
  const desc = document.getElementById("profile-desc");

  btns.forEach((btn) => {
    if (btn.dataset.profile === activeProfile) btn.classList.add("active");
    else btn.classList.remove("active");

    btn.addEventListener("click", () => {
      btns.forEach((b) => b.classList.remove("active"));
      btn.classList.add("active");
      activeProfile = btn.dataset.profile;
      chrome.storage.local.set({ profile: activeProfile });
      if (desc) desc.textContent = PROFILE_DESCS[activeProfile] ?? "";
      // sync header select
      const select = document.getElementById("profile-select");
      if (select) select.value = activeProfile;
    });
  });

  if (desc) desc.textContent = PROFILE_DESCS[activeProfile] ?? "";
}

async function fetchTosText(tabId) {
  let resp = await new Promise((resolve) => {
    chrome.tabs.sendMessage(tabId, { type: "GET_TOS_TEXT" }, (r) => {
      if (chrome.runtime.lastError) resolve(null);
      else resolve(r);
    });
  });

  if (!resp) {
    try {
      await chrome.scripting.executeScript({ target: { tabId }, files: ["content/content.js"] });
      await new Promise(r => setTimeout(r, 600));
      resp = await new Promise((resolve) => {
        chrome.tabs.sendMessage(tabId, { type: "GET_TOS_TEXT" }, (r) => {
          if (chrome.runtime.lastError) resolve(null);
          else resolve(r);
        });
      });
    } catch {
      return null;
    }
  }
  return resp?.text ? resp : null;
}

async function startAnalysis(tab) {
  showState("state-loading");

  const tosResponse = await fetchTosText(tab.id);
  if (!tosResponse) {
    showState("state-no-tos");
    return;
  }

  await chrome.runtime.sendMessage({
    type: "TOS_TEXT_FROM_POPUP",
    text: tosResponse.text,
    domain: tosResponse.domain,
    tabId: tab.id,
    profile: activeProfile,
  });

  const storageKey = `result_${tab.id}`;
  const listener = (changes, area) => {
    if (area !== "session" || !changes[storageKey]) return;
    chrome.storage.onChanged.removeListener(listener);
    applyResult(changes[storageKey].newValue);
  };
  chrome.storage.onChanged.addListener(listener);
}

async function init() {
  showState("state-loading");
  await initProfile();

  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });

  const result = await chrome.runtime.sendMessage({ type: "GET_RESULT", tabId: tab.id });

  // show cached result only if same profile
  if (result && result.status === "success" && result.profile === activeProfile) {
    applyResult(result);
    return;
  }

  if (result && result.status === "loading") {
    showState("state-loading");
    const storageKey = `result_${tab.id}`;
    const listener = (changes, area) => {
      if (area !== "session" || !changes[storageKey]) return;
      chrome.storage.onChanged.removeListener(listener);
      applyResult(changes[storageKey].newValue);
    };
    chrome.storage.onChanged.addListener(listener);
    return;
  }

  // show idle screen — let user pick profile then click Analyze
  showState("state-idle");
  initIdleProfilePicker();

  document.getElementById("analyze-btn").addEventListener("click", () => startAnalysis(tab));
}

async function retryExtract(tab) {
  const delays = [1500, 2500, 4000];
  for (const delay of delays) {
    showState("state-loading");
    await new Promise(r => setTimeout(r, delay));
    const tosResponse = await new Promise((resolve) => {
      chrome.tabs.sendMessage(tab.id, { type: "GET_TOS_TEXT", force: true }, (resp) => {
        if (chrome.runtime.lastError) resolve(null);
        else resolve(resp);
      });
    });
    if (tosResponse && tosResponse.text) {
      await chrome.runtime.sendMessage({
        type: "TOS_TEXT_FROM_POPUP",
        text: tosResponse.text,
        domain: tosResponse.domain,
        tabId: tab.id,
        profile: activeProfile,
      });
      const storageKey = `result_${tab.id}`;
      const listener = (changes, area) => {
        if (area !== "session" || !changes[storageKey]) return;
        chrome.storage.onChanged.removeListener(listener);
        applyResult(changes[storageKey].newValue);
      };
      chrome.storage.onChanged.addListener(listener);
      return;
    }
  }
  showState("state-no-tos");
}

document.addEventListener("DOMContentLoaded", async () => {
  await init();
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const retryBtn = document.getElementById("retry-btn");
  if (retryBtn) retryBtn.addEventListener("click", () => retryExtract(tab));
});
