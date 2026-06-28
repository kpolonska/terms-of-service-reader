const API = "http://localhost:8000";

const $ = (id) => document.getElementById(id);

const analyzeBtn  = $("analyze-btn");
const btnText     = $("btn-text");
const btnLoading  = $("btn-loading");
const tosInput    = $("tos-input");
const domainInput = $("domain-input");
const profileInput= $("profile-input");

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
