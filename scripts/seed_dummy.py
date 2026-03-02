from __future__ import annotations

import time
import uuid

from rodet.storage.db import connect, init_db


def _id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def main() -> None:
    conn = connect()
    init_db(conn)

    # Limpieza (para regenerar labels)
    conn.execute("DELETE FROM comments")
    conn.execute("DELETE FROM posts")
    conn.commit()

    now = int(time.time())
    subreddit = "ArAutos"

    dominant_models = [
        "Corolla",
        "Etios",
        "Fiesta KD",
        "Onix",
        "Gol Trend",
        "Vento",
        "Fit",
    ]

    posts = []
    for i in range(35):
        post_id = _id("t3")
        posts.append((post_id, dominant_models[i % len(dominant_models)]))

        title = f"Recomendacion: ¿Qué auto compro con presupuesto {8 + (i % 10)} millones?"
        body = "Uso mixto ciudad/ruta. Busco confiable y barato de mantener."
        url = f"https://reddit.com/r/{subreddit}/comments/{post_id}/"

        conn.execute(
            """
            INSERT INTO posts
              (post_id, created_utc, subreddit, title, body, url, score, num_comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (post_id, now - i * 86400, subreddit, title, body, url, 10 + i, 10),
        )

    for post_id, dom in posts:
        for j in range(10):
            comment_id = _id("t1")

            # 7/10 comentarios mencionan el modelo dominante del post
            if j < 7:
                body = f"Para mí lo mejor por esa plata es {dom}. Confiable y reventa."
            else:
                body = [
                    "Depende mucho del estado, revisá historial.",
                    "No te olvides de calcular seguro y patente.",
                    "Si es para ciudad, priorizá consumo.",
                ][j % 3]

            conn.execute(
                """
                INSERT INTO comments
                  (comment_id, post_id, created_utc, parent_id, body, score)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (comment_id, post_id, now - j * 3600, None, body, 1 + (j % 5)),
            )

    conn.commit()
    conn.close()
    print("Seed OK: data/rodet.db regenerada con clases variadas.")
    

if __name__ == "__main__":
    main()