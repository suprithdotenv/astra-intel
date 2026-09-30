import os

from sqlalchemy import select
from sentence_transformers import CrossEncoder

from app.database import SessionLocal
from app.models.document import DocumentChunk
from app.services.embedding_service import create_embedding


reranker = CrossEncoder(
    "cross-encoder/ms-marco-MiniLM-L-6-v2"
)


def vector_search(query: str, limit: int = 12):
    db = SessionLocal()

    try:
        query_embedding = create_embedding(query)

        distance = DocumentChunk.embedding.cosine_distance(
            query_embedding
        )

        results = db.execute(
            select(DocumentChunk)
            .where(distance <= 0.8)
            .order_by(distance)
            .limit(limit)
        ).scalars().all()

        return results

    finally:
        db.close()


def rerank(query: str, chunks, limit: int = 5):
    if not chunks:
        return []

    pairs = [
        (query, chunk.content)
        for chunk in chunks
    ]

    scores = reranker.predict(
        pairs,
        batch_size=16
        )

    ranked_chunks = sorted(
        zip(chunks, scores),
        key=lambda item: item[1],
        reverse=True
    )

    return [
        chunk
        for chunk, score in ranked_chunks[:limit]
    ]


def search_documents(query: str, limit: int = 5):
    candidates = vector_search(
        query,
        limit=12
    )

    return rerank(
        query,
        candidates,
        limit=limit
    )