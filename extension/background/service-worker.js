const API_URL = "http://localhost:8000/analyze";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const tabId = sender.tab?.id;

  if (message.type === "NO_TOS_DETECTED") {
    if (tabId) setResult(tabId, { status: "no_tos", data: null });
    return;
  }

  if (message.type === "TOS_TEXT") {
    if (tabId) {
      setResult(tabId, { status: "loading", data: null });
      analyzeText(message.text, message.domain, tabId);
    }
    return;
  }

  if (message.type === "TOS_TEXT_FROM_POPUP") {
    const { text, domain, tabId } = message;
    setResult(tabId, { status: "loading", data: null });
    analyzeText(text, domain, tabId);
    sendResponse({ ok: true });
    return true;
  }

  if (message.type === "GET_RESULT") {
    const key = `result_${message.tabId}`;
    chrome.storage.session.get(key, (items) => {
      sendResponse(items[key] ?? { status: "pending", data: null });
    });
    return true; // keep message channel open for async response
  }
});

function setResult(tabId, value) {
  chrome.storage.session.set({ [`result_${tabId}`]: value });
}

const RISK_BADGE_COLORS = {
  SAFE:      "#065f46",
  CAUTION:   "#92400e",
  RISKY:     "#9a3412",
  DANGEROUS: "#991b1b",
};

async function analyzeText(text, domain, tabId) {
  try {
    const stored = await chrome.storage.local.get("profile");
    const profile = stored.profile ?? "general";

    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, domain, profile }),
    });

    if (!response.ok) throw new Error(`API error: ${response.status}`);

    const data = await response.json();
    setResult(tabId, { status: "success", data, domain });

    if (data.diff?.has_changes && domain) {
      const { subscriptions = [] } = await chrome.storage.local.get("subscriptions");
      if (subscriptions.includes(domain)) {
        const count = data.diff.changed_clauses.length;
        chrome.notifications.create(`tos-change-${domain}`, {
          type: "basic",
          iconUrl: "../icons/icon48.png",
          title: "ToS Changed",
          message: `${domain} updated their Terms of Service. ${count} clause${count !== 1 ? "s" : ""} changed.`,
          priority: 1,
        });
      }
    }

    if (data.risk) {
      chrome.action.setBadgeText({ text: String(data.risk.score), tabId });
      chrome.action.setBadgeBackgroundColor({
        color: RISK_BADGE_COLORS[data.risk.label] ?? "#555",
        tabId,
      });
    }
  } catch (err) {
    setResult(tabId, { status: "error", data: { message: err.message } });
    chrome.action.setBadgeText({ text: "!", tabId });
    chrome.action.setBadgeBackgroundColor({ color: "#555", tabId });
  }
}
