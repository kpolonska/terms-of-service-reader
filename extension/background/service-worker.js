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

  if (message.type === "GET_RESULT") {
    const key = `result_${message.tabId}`;
    chrome.storage.session.get(key, (items) => {
      sendResponse(items[key] ?? { status: "no_tos", data: null });
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
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, domain }),
    });

    if (!response.ok) throw new Error(`API error: ${response.status}`);

    const data = await response.json();
    setResult(tabId, { status: "success", data });

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
