const postsEl = document.getElementById("posts");
const postsMetaEl = document.getElementById("postsMeta");
const commentsEl = document.getElementById("comments");
const commentsMetaEl = document.getElementById("commentsMeta");
const debugEl = document.getElementById("debug");

const searchForm = document.getElementById("searchForm");
const qEl = document.getElementById("q");
const limitEl = document.getElementById("limit");

const predictForm = document.getElementById("predictForm");
const predictTextEl = document.getElementById("predictText");
const predEl = document.getElementById("pred");
const predMetaEl = document.getElementById("predMeta");

function escapeHtml(s) {
  return s
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setDebug(obj) {
  debugEl.textContent = JSON.stringify(obj, null, 2);
}

async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`HTTP ${res.status} ${res.statusText}: ${text}`);
  }
  return await res.json();
}

function renderPosts(posts) {
  postsEl.innerHTML = "";
  for (const p of posts) {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <button class="linklike" data-post-id="${escapeHtml(p.post_id)}">
        ${escapeHtml(p.title)}
      </button>
      <div class="small">
        score: ${p.score} | comments: ${p.num_comments} |
        <a href="${escapeHtml(p.url)}" target="_blank" rel="noreferrer">abrir</a>
      </div>
      <div class="body">${escapeHtml((p.body || "").slice(0, 140))}${(p.body || "").length > 140 ? "…" : ""}</div>
    `;
    postsEl.appendChild(div);
  }

  postsEl.querySelectorAll("button[data-post-id]").forEach((btn) => {
    btn.addEventListener("click", async () => {
      const postId = btn.getAttribute("data-post-id");
      await loadComments(postId);
    });
  });
}

function renderComments(comments) {
  commentsEl.innerHTML = "";
  for (const c of comments) {
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <div class="small">score: ${c.score} | id: ${escapeHtml(c.comment_id)}</div>
      <div class="body">${escapeHtml(c.body)}</div>
    `;
    commentsEl.appendChild(div);
  }
}

async function loadPosts() {
  const q = qEl.value.trim();
  const limit = Number(limitEl.value || 25);
  const url = `/api/posts?query=${encodeURIComponent(q)}&limit=${encodeURIComponent(limit)}`;

  postsMetaEl.textContent = "Cargando…";
  commentsMetaEl.textContent = "Seleccioná un post…";
  commentsEl.innerHTML = "";

  const data = await fetchJSON(url);
  postsMetaEl.textContent = `Encontrados: ${data.count}`;
  renderPosts(data.data);
  setDebug({ last_posts_response: data });
}

async function loadComments(postId) {
  commentsMetaEl.textContent = "Cargando comentarios…";
  commentsEl.innerHTML = "";

  const url = `/api/posts/${encodeURIComponent(postId)}/comments?limit=100`;
  const data = await fetchJSON(url);

  if (data.error) {
    commentsMetaEl.textContent = `Error: ${data.error}`;
    setDebug({ last_comments_response: data });
    return;
  }

  commentsMetaEl.textContent = `${data.post.title} — comentarios: ${data.count}`;
  renderComments(data.data);
  setDebug({ last_comments_response: data });
}

searchForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await loadPosts();
  } catch (err) {
    postsMetaEl.textContent = "Error al buscar.";
    setDebug({ error: String(err) });
  }
});

// Auto-load al abrir
loadPosts().catch((err) => setDebug({ error: String(err) }));



function renderPredictions(top5) {
  predEl.innerHTML = "";
  for (const item of top5) {
    const pct = (item.probability * 100).toFixed(1);
    const div = document.createElement("div");
    div.className = "card";
    div.innerHTML = `
      <div>
        <strong>${escapeHtml(item.label)}</strong>
        <span class="badge">${pct}%</span>
      </div>
    `;
    predEl.appendChild(div);
  }
}

async function predict(text) {
  predMetaEl.textContent = "Predicting…";
  predEl.innerHTML = "";

  const data = await fetchJSON("/api/predict", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });

  predMetaEl.textContent = "Top 5:";
  renderPredictions(data.top5);
  setDebug({ last_predict_response: data });
}

predictForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  try {
    await predict(predictTextEl.value.trim());
  } catch (err) {
    predMetaEl.textContent = "Error al predecir. ¿Entrenaste el modelo?";
    setDebug({ error: String(err) });
  }
});

const modelStatusEl = document.getElementById("modelStatus");
const trainBtn = document.getElementById("trainBtn");

async function loadModelInfo() {
  try {
    const info = await fetchJSON("/api/model/info");
    if (!info.trained) {
      modelStatusEl.textContent = "Modelo: NO entrenado (tocá 'Entrenar modelo').";
      return;
    }
    modelStatusEl.textContent =
      `Modelo: OK | clases: ${info.classes.length} | actualizado: ${info.updated_utc}`;
  } catch (err) {
    modelStatusEl.textContent = "No se pudo leer estado del modelo.";
    setDebug({ error: String(err) });
  }
}

async function trainModel() {
  trainBtn.disabled = true;
  trainBtn.textContent = "Entrenando…";
  try {
    const res = await fetchJSON("/api/train", { method: "POST" });
    setDebug({ last_train_response: res });
    if (res.ok) {
      modelStatusEl.textContent = `Modelo entrenado | samples: ${res.n_samples} | clases: ${res.n_classes}`;
    } else {
      modelStatusEl.textContent =
        `No se pudo entrenar (samples: ${res.n_samples}, clases: ${res.n_classes}).`;
    }
  } finally {
    trainBtn.disabled = false;
    trainBtn.textContent = "Entrenar modelo";
    await loadModelInfo();
  }
}

trainBtn.addEventListener("click", () => {
  trainModel().catch((err) => setDebug({ error: String(err) }));
});

// al iniciar
loadModelInfo();