from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from datetime import datetime, timezone

from fastapi import FastAPI, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from rodet.api.schemas import PredictRequest, PredictResponse, TopPrediction, TrainResponse
from rodet.recommend.dataset import build_training_dataframe
from rodet.recommend.model import load_model, train_and_save
from rodet.storage.db import connect, init_db
from rodet.recommend.model import MODEL_PATH

FRONTEND_DIR = Path(__file__).resolve().parents[2] / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    conn = connect()
    init_db(conn)
    conn.close()
    yield


app = FastAPI(title="rodet", lifespan=lifespan)


@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.get("/api/model/info")
def model_info():
    if not MODEL_PATH.exists():
        return {"trained": False, "path": str(MODEL_PATH), "classes": []}

    model = load_model()
    mtime = datetime.fromtimestamp(MODEL_PATH.stat().st_mtime, tz=timezone.utc).isoformat()
    size_bytes = MODEL_PATH.stat().st_size

    classes = [str(c) for c in getattr(model, "classes_", [])]
    return {
        "trained": True,
        "path": str(MODEL_PATH),
        "updated_utc": mtime,
        "size_bytes": size_bytes,
        "classes": classes,
    }

@app.post("/api/train", response_model=TrainResponse)
def train():
    df = build_training_dataframe(min_label_count=1)
    if df.empty:
        return TrainResponse(ok=False, n_samples=0, n_classes=0, classes=[])

    n_classes = df["label"].nunique()
    if n_classes < 2:
        # Evita 500 y te muestra el problema
        classes = sorted(df["label"].unique().tolist())
        return TrainResponse(ok=False, n_samples=int(df.shape[0]), n_classes=int(n_classes), classes=classes)

    res = train_and_save(df["text"].tolist(), df["label"].tolist())
    return TrainResponse(ok=True, n_samples=res.n_samples, n_classes=res.n_classes, classes=res.classes)


@app.post("/api/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    model = load_model()
    proba = model.predict_proba([req.text])[0]
    classes = model.classes_

    pairs = sorted(zip(classes, proba), key=lambda x: x[1], reverse=True)[:5]
    top5 = [TopPrediction(label=lbl, probability=float(p)) for lbl, p in pairs]
    return PredictResponse(ok=True, top5=top5)


@app.get("/api/posts")
def list_posts(
    query: str | None = Query(default=None, description="Texto a buscar en title/body"),
    limit: int = Query(default=50, ge=1, le=200),
):
    conn = connect()
    init_db(conn)

    sql = """
      SELECT post_id, created_utc, subreddit, title, body, url, score, num_comments
      FROM posts
    """
    params: list[object] = []
    if query:
        sql += " WHERE (title LIKE ? OR body LIKE ?)"
        q = f"%{query}%"
        params.extend([q, q])

    sql += " ORDER BY created_utc DESC LIMIT ?"
    params.append(limit)

    rows = conn.execute(sql, params).fetchall()
    conn.close()

    return {"count": len(rows), "data": [dict(r) for r in rows]}


@app.get("/api/posts/{post_id}/comments")
def list_comments(
    post_id: str,
    limit: int = Query(default=100, ge=1, le=500),
):
    conn = connect()
    init_db(conn)

    post = conn.execute(
        "SELECT post_id, title, url FROM posts WHERE post_id = ?",
        (post_id,),
    ).fetchone()

    if post is None:
        conn.close()
        return {"post": None, "count": 0, "data": [], "error": "post_not_found"}

    rows = conn.execute(
        """
        SELECT comment_id, post_id, created_utc, parent_id, body, score
        FROM comments
        WHERE post_id = ?
        ORDER BY score DESC, created_utc DESC
        LIMIT ?
        """,
        (post_id, limit),
    ).fetchall()

    conn.close()
    return {"post": dict(post), "count": len(rows), "data": [dict(r) for r in rows]}


app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def index():
    return FileResponse(FRONTEND_DIR / "index.html")