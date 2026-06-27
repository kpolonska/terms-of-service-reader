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
  const REMOVE_SELECTORS = ["nav", "header", "footer", "aside", ".cookie-banner", "[role='banner']", "[role='navigation']"];
  const clone = document.body.cloneNode(true);

  REMOVE_SELECTORS.forEach((sel) => {
    clone.querySelectorAll(sel).forEach((el) => el.remove());
  });

  const main =
    clone.querySelector("main") ||
    clone.querySelector("article") ||
    clone.querySelector("[role='main']") ||
    clone;

  const text = main.innerText || main.textContent || "";
  return text.replace(/\s+/g, " ").trim().slice(0, MAX_TEXT_LENGTH);
}

function run() {
  if (!isTosPage()) {
    chrome.runtime.sendMessage({ type: "NO_TOS_DETECTED" });
    return;
  }

  const text = extractText();
  if (!text || text.length < 100) {
    chrome.runtime.sendMessage({ type: "NO_TOS_DETECTED" });
    return;
  }

  chrome.runtime.sendMessage({
    type: "TOS_TEXT",
    text,
    domain: window.location.hostname,
  });
}

run();
