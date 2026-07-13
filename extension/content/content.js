const TOS_URL_KEYWORDS = ["terms", "tos", "privacy", "legal", "conditions", "eula", "agreement"];
const TOS_HEADING_PHRASES = ["terms of service", "terms and conditions", "privacy policy", "user agreement", "end user license"];
const MAX_TEXT_LENGTH = 15000;

const REMOVE_SELECTORS = [
  "nav", "header", "footer", "aside",
  "script", "style", "noscript",
  ".cookie-banner", "[role='banner']", "[role='navigation']",
  "svg", "img", "button",
];

function isTosPage() {
  const url = window.location.href.toLowerCase();
  if (TOS_URL_KEYWORDS.some((kw) => url.includes(kw))) return true;

  const title = document.title.toLowerCase();
  if (TOS_HEADING_PHRASES.some((phrase) => title.includes(phrase))) return true;

  const headings = [...document.querySelectorAll("h1, h2")];
  return headings.some((h) =>
    TOS_HEADING_PHRASES.some((phrase) => h.textContent?.toLowerCase().includes(phrase))
  );
}

function extractText() {
  const clone = document.body.cloneNode(true);

  REMOVE_SELECTORS.forEach((sel) => {
    clone.querySelectorAll(sel).forEach((el) => el.remove());
  });

  let main =
    clone.querySelector("main") ||
    clone.querySelector("article") ||
    clone.querySelector("[role='main']");

  if (!main) {
    const divs = [...clone.querySelectorAll("div")].sort(
      (a, b) => (b.textContent?.length || 0) - (a.textContent?.length || 0)
    );
    main = divs[0] || clone;
  }

  const text = main.textContent || "";
  return text.replace(/\s+/g, " ").trim().slice(0, MAX_TEXT_LENGTH);
}

const HIGHLIGHT_NAME = "tos-reader-highlight";
let activeHighlightMark = null;

function normalizeForMatch(s) {
  return s.replace(/\s+/g, " ").trim();
}

const REMOVE_SELECTOR_STRING = REMOVE_SELECTORS.join(", ");

function collectTextNodes(root) {
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT, {
    acceptNode(node) {
      const parent = node.parentElement;
      if (!parent) return NodeFilter.FILTER_REJECT;
      if (parent.closest(REMOVE_SELECTOR_STRING)) return NodeFilter.FILTER_REJECT;
      if (!node.nodeValue || !node.nodeValue.trim()) return NodeFilter.FILTER_REJECT;
      return NodeFilter.FILTER_ACCEPT;
    },
  });
  const nodes = [];
  let n;
  while ((n = walker.nextNode())) nodes.push(n);
  return nodes;
}

// Builds a normalized (whitespace-collapsed) version of the page text alongside a
// per-character map back to the original (node, offset) so a normalized substring
// match can be translated into a real DOM Range, even when it spans several nodes.
function findQuoteRange(quote) {
  const root =
    document.querySelector("main") ||
    document.querySelector("article") ||
    document.querySelector("[role='main']") ||
    document.body;

  const segments = [];
  let fullText = "";

  for (const node of collectTextNodes(root)) {
    const raw = node.nodeValue;
    let normText = "";
    const rawOffsets = [];
    let i = 0;
    while (i < raw.length) {
      if (/\s/.test(raw[i])) {
        let j = i;
        while (j < raw.length && /\s/.test(raw[j])) j++;
        const lastChar = normText.length ? normText[normText.length - 1] : fullText.slice(-1);
        if (lastChar !== " ") {
          normText += " ";
          rawOffsets.push(i);
        }
        i = j;
      } else {
        normText += raw[i];
        rawOffsets.push(i);
        i++;
      }
    }
    if (normText.length) {
      segments.push({ node, normStart: fullText.length, rawOffsets });
      fullText += normText;
    }
  }

  const normalizedQuote = normalizeForMatch(quote);
  if (!normalizedQuote) return null;

  const startIdx = fullText.indexOf(normalizedQuote);
  if (startIdx === -1) return null;
  const endIdx = startIdx + normalizedQuote.length - 1; // inclusive

  const locate = (pos) => {
    for (const seg of segments) {
      const segLen = seg.rawOffsets.length;
      if (pos >= seg.normStart && pos < seg.normStart + segLen) {
        return { node: seg.node, offset: seg.rawOffsets[pos - seg.normStart] };
      }
    }
    return null;
  };

  const startLoc = locate(startIdx);
  const endLoc = locate(endIdx);
  if (!startLoc || !endLoc) return null;

  const range = document.createRange();
  range.setStart(startLoc.node, startLoc.offset);
  range.setEnd(endLoc.node, endLoc.offset + 1);
  return range;
}

function ensureHighlightStyle() {
  if (document.getElementById("tos-reader-highlight-style")) return;
  const style = document.createElement("style");
  style.id = "tos-reader-highlight-style";
  style.textContent = `
    ::highlight(${HIGHLIGHT_NAME}) { background-color: #fde047; color: #1a1a1a; }
    mark.tos-reader-highlight-fallback { background-color: #fde047; color: #1a1a1a; }
  `;
  document.head.appendChild(style);
}

function clearHighlight() {
  if (window.CSS?.highlights) CSS.highlights.delete(HIGHLIGHT_NAME);
  if (activeHighlightMark?.parentNode) {
    const parent = activeHighlightMark.parentNode;
    while (activeHighlightMark.firstChild) parent.insertBefore(activeHighlightMark.firstChild, activeHighlightMark);
    parent.removeChild(activeHighlightMark);
    parent.normalize();
  }
  activeHighlightMark = null;
}

function highlightQuote(quote) {
  clearHighlight();

  const range = findQuoteRange(quote);
  if (!range) return false;

  ensureHighlightStyle();

  if (window.Highlight && window.CSS?.highlights) {
    CSS.highlights.set(HIGHLIGHT_NAME, new Highlight(range));
  } else {
    try {
      const mark = document.createElement("mark");
      mark.className = "tos-reader-highlight-fallback";
      range.surroundContents(mark);
      activeHighlightMark = mark;
    } catch {
      // Range crosses element boundaries in a way surroundContents can't handle.
      // We still scroll to it below even though we can't visually mark it.
    }
  }

  const scrollTarget =
    range.startContainer.nodeType === Node.TEXT_NODE
      ? range.startContainer.parentElement
      : range.startContainer;
  scrollTarget?.scrollIntoView({ behavior: "smooth", block: "center" });
  return true;
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "GET_TOS_TEXT") {
    const force = message.force || false;
    if (!force && !isTosPage()) {
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

  if (message.type === "HIGHLIGHT_QUOTE") {
    const found = highlightQuote(message.quote || "");
    sendResponse({ found });
    return true;
  }
});

function run() {
  if (!isTosPage()) return;
  const text = extractText();
  if (!text || text.length < 100) {
    console.log("[ToS Reader] Text too short or missing, retrying...");
    return false;
  }
  console.log("[ToS Reader] Auto-detected and extracted ToS text");
  chrome.runtime.sendMessage({ type: "TOS_TEXT", text, domain: window.location.hostname });
  return true;
}

let attempts = 0;
const maxAttempts = 5;
const interval = setInterval(() => {
  if (run() || attempts >= maxAttempts) {
    clearInterval(interval);
  }
  attempts++;
}, 2000);

const observer = new MutationObserver(() => {
  if (run()) {
    observer.disconnect();
    clearInterval(interval);
  }
});

observer.observe(document.body, {
  childList: true,
  subtree: true,
  characterData: false,
});
