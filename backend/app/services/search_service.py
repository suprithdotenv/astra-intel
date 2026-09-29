from sqlalchemy import select
from app.database import SessionLocal
from app.models.document import DocumentChunk
from app.services.embedding_service import create_embedding


def search_documents(query: str, limit: int = 5):

    db = SessionLocal()

    try:
        query_embedding = create_embedding(query)

        results = db.execute(
            select(DocumentChunk)
            .order_by(
                DocumentChunk.embedding.cosine_distance(query_embedding)
            )
            .limit(limit)
        ).scalars().all()

        return results

    finally:
        db.close()