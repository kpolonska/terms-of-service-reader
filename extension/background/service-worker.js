const API_URL = "http://localhost:8000/analyze";

// Keyed by tabId: { status: "loading"|"success"|"error"|"no_tos", data: {...} }
const tabResults = {};

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const tabId = sender.tab?.id;

  if (message.type === "NO_TOS_DETECTED") {
    if (tabId) tabResults[tabId] = { status: "no_tos", data: null };
    return;
  }

  if (message.type === "TOS_TEXT") {
    if (tabId) tabResults[tabId] = { status: "loading", data: null };
    analyzeText(message.text, message.domain, tabId);
    return;
  }

  if (message.type === "GET_RESULT") {
    const activeTab = message.tabId;
    sendResponse(tabResults[activeTab] ?? { status: "no_tos", data: null });
    return true;
  }
});

async function analyzeText(text, domain, tabId) {
  try {
    const response = await fetch(API_URL, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, domain }),
    });

    if (!response.ok) throw new Error(`API error: ${response.status}`);

    const data = await response.json();
    if (tabId) tabResults[tabId] = { status: "success", data };
  } catch (err) {
    if (tabId) tabResults[tabId] = { status: "error", data: { message: err.message } };
  }
}
