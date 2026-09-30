from fastapi import FastAPI, UploadFile, File
from app.database import engine, Base,SessionLocal
from pydantic import BaseModel
from app.services.search_service import search_documents

from sqlalchemy import text

from app.services.ingestion_service import process_document
import os
import shutil

from app.models.conversation import Conversation
from app.models.message import Message

from app.models.document import Document, DocumentChunk
from app.services.llm_service import generate_answer, compare_documents,verify_answer



app = FastAPI()


Base.metadata.create_all(bind=engine)


class SearchRequest(BaseModel):
    query: str
    limit: int = 5
    conversation_id: int | None = None

class CompareRequest(BaseModel):
    document_id_1: int
    document_id_2: int




@app.get("/")
def root():
    return {"message": "Hello World"}



@app.get("/test-db")
def test_db():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": result.scalar()}





@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):

    os.makedirs("uploads", exist_ok=True)

    file_path = f"uploads/{file.filename}"

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    document_id, chunk_count = process_document(
        file_path,
        file.filename
    )
    return {
        "message": "Document processed successfully",
        "document": file.filename,
        "document_id": document_id,
        "chunks": chunk_count
    }





@app.post("/search")
def search(request: SearchRequest):

    results = search_documents(
        request.query,
        request.limit
    )

    return {
        "results": [
            {
                "page": result.page_number,
                "content": result.content,
            }
            for result in results
        ]
    }




@app.post("/ask")
def ask(request: SearchRequest):

    db = SessionLocal()

    try:
        # Use existing conversation or create a new one
        if request.conversation_id:
            conversation = (
                db.query(Conversation)
                .filter(
                    Conversation.id == request.conversation_id
                )
                .first()
            )

            if not conversation:
                return {"error": "Conversation not found"}

        else:
            conversation = Conversation()
            db.add(conversation)
            db.commit()
            db.refresh(conversation)


        previous_messages = (
            db.query(Message)
            .filter(
                Message.conversation_id == conversation.id
            )
            .order_by(Message.created_at)
            .all()
        )

        chunks = search_documents(
            request.query,
            request.limit
        )

        answer = generate_answer(
            request.query,
            chunks,
            previous_messages
        )

        verification = verify_answer(
            request.query,
            answer,
            chunks
        )


        message = Message(
            conversation_id=conversation.id,
            question=request.query,
            answer=answer
        )

        db.add(message)
        db.commit()

        return {
            "conversation_id": conversation.id,
            "question": request.query,
            "answer": answer,
            "verification": verification,
            "sources": [
                {
                    "page": chunk.page_number,
                    "content": chunk.content
                }
                for chunk in chunks
            ]
        }

    finally:
        db.close()






@app.get("/conversations")
def get_conversations():

    db = SessionLocal()

    try:
        conversations = (
            db.query(Conversation)
            .order_by(Conversation.created_at.desc())
            .all()
        )

        return [
            {
                "id": c.id,
                "created_at": c.created_at
            }
            for c in conversations
        ]

    finally:
        db.close()





@app.get("/conversations/{conversation_id}")
def get_conversation(conversation_id: int):

    db = SessionLocal()

    try:
        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .all()
        )

        return [
            {
                "question": message.question,
                "answer": message.answer,
                "created_at": message.created_at
            }
            for message in messages
        ]

    finally:
        db.close()





@app.post("/documents/{document_id}/summary")
def generate_document_summary(document_id: int):
    db = SessionLocal()

    try:
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if not document:
            return {"error": "Document not found"}

        chunks = (
            db.query(DocumentChunk)
            .filter(DocumentChunk.document_id == document_id)
            .order_by(DocumentChunk.page_number)
            .all()
        )

        if not chunks:
            return {"error": "No content found for this document"}




        summary = generate_answer(
            "Provide a concise summary of this document. "
            "Cover the main topic, key points, and important conclusions. "
            "Do not add information that is not present in the document.",
            chunks
        )

        return {
            "document_id": document.id,
            "document": document.filename,
            "summary": summary
        }

    finally:
        db.close()



@app.post("/documents/compare")
def compare_documents_endpoint(request: CompareRequest):

    db = SessionLocal()

    try:
        document1 = (
            db.query(Document)
            .filter(Document.id == request.document_id_1)
            .first()
        )

        document2 = (
            db.query(Document)
            .filter(Document.id == request.document_id_2)
            .first()
        )

        if not document1 or not document2:
            return {"error": "One or both documents not found"}

        chunks1 = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document1.id
            )
            .order_by(DocumentChunk.page_number)
            .all()
        )

        chunks2 = (
            db.query(DocumentChunk)
            .filter(
                DocumentChunk.document_id == document2.id
            )
            .order_by(DocumentChunk.page_number)
            .all()
        )

        if not chunks1 or not chunks2:
            return {"error": "One or both documents contain no content"}

        comparison = compare_documents(
            document1.filename,
            document2.filename,
            chunks1,
            chunks2
        )

        return {
            "document_1": {
                "id": document1.id,
                "name": document1.filename
            },
            "document_2": {
                "id": document2.id,
                "name": document2.filename
            },
            "comparison": comparison
        }

    finally:
        db.close()

