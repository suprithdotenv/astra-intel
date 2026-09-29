from app.database import SessionLocal
from app.models.document import DocumentChunk


from app.services.pdf_service import extract_chunks
from app.services.embedding_service import create_embedding


def process_document(file_path: str, document_name: str):

    db = SessionLocal()

    try:
        chunks = extract_chunks(file_path)

        for chunk in chunks:

            embedding = create_embedding(
                chunk["content"]
            )

            document_chunk = DocumentChunk(
                document_name=document_name,
                page_number=chunk["page_number"],
                content=chunk["content"],
                embedding=embedding
            )

            db.add(document_chunk)

        db.commit()

        return len(chunks)

    finally:
        db.close()