const API = "http://localhost:8000";

if (typeof pdfjsLib !== "undefined") {
  pdfjsLib.GlobalWorkerOptions.workerSrc =
    "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js";
}

const $ = (id) => document.getElementById(id);

const analyzeBtn   = $("analyze-btn");
const btnText      = $("btn-text");
const btnLoading   = $("btn-loading");
const tosInput     = $("tos-input");
const domainInput  = $("domain-input");
const profileInput = $("profile-input");
const fileInput       = $("file-input");
const fileUploadBtn   = $("file-upload-btn");
const fileUploadLabel = $("file-upload-label");
const fileClearBtn    = $("file-clear-btn");
const fileTypeHint    = $("file-type-hint");

function resetFileUpload() {
  tosInput.value = "";
  fileUploadLabel.textContent = "Upload file (.txt, .pdf, .docx, .html)";
  fileClearBtn.classList.add("hidden");
  fileTypeHint.classList.remove("hidden");
  fileInput.value = "";
}

fileClearBtn.addEventListener("click", resetFileUpload);

async function extractText(file) {
  const ext = file.name.split(".").pop().toLowerCase();

  if (ext === "txt") {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => resolve(e.target.result);
      reader.onerror = () => reject(new Error("Failed to read file"));
      reader.readAsText(file);
    });
  }

  if (ext === "html" || ext === "htm") {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const parser = new DOMParser();
        const doc = parser.parseFromString(e.target.result, "text/html");
        ["script","style","noscript","nav","header","footer","aside"].forEach(tag => {
          doc.querySelectorAll(tag).forEach(el => el.remove());
        });
        const main = doc.querySelector("main, article, [role='main']") || doc.body;
        resolve(main.textContent.replace(/\s+/g, " ").trim());
      };
      reader.onerror = () => reject(new Error("Failed to read file"));
      reader.readAsText(file);
    });
  }

  if (ext === "pdf") {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const typedArray = new Uint8Array(e.target.result);
          const pdf = await pdfjsLib.getDocument({ data: typedArray }).promise;
          let text = "";
          for (let i = 1; i <= pdf.numPages; i++) {
            const page = await pdf.getPage(i);
            const content = await page.getTextContent();
            text += content.items.map(item => item.str).join(" ") + "\n";
          }
          resolve(text.trim());
        } catch (err) {
          reject(new Error("Failed to parse PDF: " + err.message));
        }
      };
      reader.onerror = () => reject(new Error("Failed to read file"));
      reader.readAsArrayBuffer(file);
    });
  }

  if (ext === "docx") {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = async (e) => {
        try {
          const result = await mammoth.extractRawText({ arrayBuffer: e.target.result });
          resolve(result.value.trim());
        } catch (err) {
          reject(new Error("Failed to parse DOCX: " + err.message));
        }
      };
      reader.onerror = () => reject(new Error("Failed to read file"));
      reader.readAsArrayBuffer(file);
    });
  }

  throw new Error(`Unsupported file type: .${ext}`);
}

fileUploadBtn.addEventListener("click", () => fileInput.click());

fileInput.addEventListener("change", async () => {
  const file = fileInput.files[0];
  if (!file) return;

  fileUploadLabel.textContent = "Reading…";
  fileUploadBtn.disabled = true;

  try {
    const text = await extractText(file);
    tosInput.value = text;
    fileUploadLabel.textContent = `✓ ${file.name}`;
    fileClearBtn.classList.remove("hidden");
    fileTypeHint.classList.add("hidden");
  } catch (err) {
    fileUploadLabel.textContent = "Upload file (.txt, .pdf, .docx, .html)";
    fileClearBtn.classList.add("hidden");
    fileTypeHint.classList.remove("hidden");
    errorText.textContent = err.message;
    showResult(resultError);
  } finally {
    fileUploadBtn.disabled = false;
    fileInput.value = "";
  }
});

const resultEmpty = $("result-empty");
const resultError = $("result-error");
const resultData  = $("result-data");
const errorText   = $("error-text");

function showResult(which) {
  resultEmpty.classList.add("hidden");
  resultError.classList.add("hidden");
  resultData.classList.add("hidden");
  which.classList.remove("hidden");
}

function setLoading(on) {
  analyzeBtn.disabled = on;
  btnText.classList.toggle("hidden", on);
  btnLoading.classList.toggle("hidden", !on);
}

function renderRisk(risk) {
  const badge = $("web-risk-badge");
  const score = $("web-risk-score");
  const label = $("web-risk-label");
  const label_lc = risk.label.toLowerCase();
  badge.className = `web-risk-badge risk-${label_lc}`;
  score.textContent = `${risk.score}/10`;
  label.textContent = risk.label;
}

function renderAlternatives(alts) {
  const section = $("web-alts");
  const list = $("web-alts-list");
  list.replaceChildren();
  if (!alts || !alts.length) { section.classList.add("hidden"); return; }
  section.classList.remove("hidden");
  alts.forEach((alt) => {
    const card = document.createElement("div");
    card.className = "web-alt-card";
    const name = document.createElement("div");
    name.className = "web-alt-name";
    name.textContent = alt.name + (alt.url ? ` · ${alt.url}` : "");
    const reason = document.createElement("p");
    reason.className = "web-alt-reason";
    reason.textContent = alt.reason;
    card.appendChild(name);
    card.appendChild(reason);
    list.appendChild(card);
  });
}

function renderClauses(clauses) {
  const list = $("web-clauses-list");
  list.replaceChildren();
  clauses.forEach((clause) => {
    const card = document.createElement("div");
    card.className = `web-clause-card severity-${clause.severity}`;

    const plain = document.createElement("p");
    plain.className = "web-clause-plain";
    plain.textContent = clause.plain_english;

    const meta = document.createElement("div");
    meta.className = "web-clause-meta";

    const makeBadge = (text) => {
      const span = document.createElement("span");
      span.className = "web-badge";
      span.textContent = text;
      return span;
    };

    meta.appendChild(makeBadge(clause.category.replaceAll("_", " ")));
    meta.appendChild(makeBadge(clause.severity.toUpperCase()));
    if (clause.concept) meta.appendChild(makeBadge(clause.concept));

    card.appendChild(plain);
    card.appendChild(meta);
    list.appendChild(card);
  });
}

analyzeBtn.addEventListener("click", async () => {
  const text = tosInput.value.trim();
  if (!text) { tosInput.focus(); return; }

  setLoading(true);

  try {
    const res = await fetch(`${API}/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        domain: domainInput.value.trim() || null,
        profile: profileInput.value,
      }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail ?? "Analysis failed");
    }

    const data = await res.json();

    renderRisk(data.risk);
    $("web-tldr-text").textContent = data.tldr;

    const cached = $("web-cached");
    data.cached ? cached.classList.remove("hidden") : cached.classList.add("hidden");

    renderAlternatives(data.alternatives);
    renderClauses(data.clauses);

    showResult(resultData);
  } catch (err) {
    errorText.textContent = err.message;
    showResult(resultError);
  } finally {
    setLoading(false);
  }
});
