const TOS_URL_KEYWORDS = ["terms", "tos", "privacy", "legal", "conditions", "eula", "agreement"];
const TOS_HEADING_PHRASES = ["terms of service", "terms and conditions", "privacy policy", "user agreement", "end user license"];
const MAX_TEXT_LENGTH = 15000;

function isTosPage() {
  const url = window.location.href.toLowerCase();
  if (TOS_URL_KEYWORDS.some((kw) => url.includes(kw))) return true;

  const title = document.title.toLowerCase();
  if (TOS_HEADING_PHRASES.some((phrase) => title.includes(phrase))) return true;

  const headings = [...document.querySelectorAll("h1, h2")];
  return headings.some((h) =>
    TOS_HEADING_PHRASES.some((phrase) => h.innerText?.toLowerCase().includes(phrase))
  );
}

function extractText() {
  const REMOVE_SELECTORS = [
    "nav", "header", "footer", "aside",
    "script", "style", "noscript",
    ".cookie-banner", "[role='banner']", "[role='navigation']",
  ];
  const clone = document.body.cloneNode(true);

  REMOVE_SELECTORS.forEach((sel) => {
    clone.querySelectorAll(sel).forEach((el) => el.remove());
  });

  const main =
    clone.querySelector("main") ||
    clone.querySelector("article") ||
    clone.querySelector("[role='main']") ||
    clone;

  const text = main.textContent || "";
  return text.replace(/\s+/g, " ").trim().slice(0, MAX_TEXT_LENGTH);
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_TOS_TEXT") {
    if (!isTosPage()) {
      sendResponse({ text: null });
      return true;
    }
    const text = extractText();
    if (!text || text.length < 100) {
      sendResponse({ text: null });
      return true;
    }
    sendResponse({ text, domain: window.location.hostname });
    return true;
  }
});

function run() {
  if (!isTosPage()) return;
  const text = extractText();
  if (!text || text.length < 100) return;
  console.log("[ToS Reader] Auto-detected and extracted ToS text");
  chrome.runtime.sendMessage({ type: "TOS_TEXT", text, domain: window.location.hostname });
}

setTimeout(run, 6000);
