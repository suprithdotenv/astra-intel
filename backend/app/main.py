from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import text

from app.database import engine, Base, SessionLocal
from app.services.ingestion_service import process_document
from app.services.llm_service import generate_answer, compare_documents, verify_answer
from app.services.search_service import search_documents
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.document import Document, DocumentChunk

import os
import shutil
import time


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

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
    return {"message": "ASTRA INTEL API is running"}


@app.get("/test-db")
def test_db():
    with engine.connect() as connection:
        result = connection.execute(text("SELECT 1"))
        return {"database": result.scalar()}


@app.get("/documents")
def get_documents():
    db = SessionLocal()

    try:
        documents = (
            db.query(Document)
            .order_by(Document.created_at.desc())
            .all()
        )

        return [
            {
                "id": document.id,
                "name": document.filename,
                "created_at": document.created_at
            }
            for document in documents
        ]

    finally:
        db.close()


@app.post("/upload")
def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".pdf"):
        return {"error": "Only PDF files are supported"}

    os.makedirs("uploads", exist_ok=True)

    file_path = os.path.join("uploads", file.filename)

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


@app.delete("/documents/{document_id}")
def delete_document(document_id: int):
    db = SessionLocal()

    try:
        document = (
            db.query(Document)
            .filter(Document.id == document_id)
            .first()
        )

        if not document:
            return {"error": "Document not found"}

        filename = document.filename

        db.query(DocumentChunk).filter(
            DocumentChunk.document_id == document_id
        ).delete(synchronize_session=False)

        db.delete(document)
        db.commit()

        file_path = os.path.join("uploads", filename)

        if os.path.exists(file_path):
            os.remove(file_path)

        return {
            "message": "Document deleted successfully",
            "document_id": document_id
        }

    finally:
        db.close()


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
                "document": result.document_name
            }
            for result in results
        ]
    }


@app.post("/ask")
def ask(request: SearchRequest):
    db = SessionLocal()

    try:
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

        total_start = time.perf_counter()

        retrieval_start = time.perf_counter()
        chunks = search_documents(
            request.query,
            request.limit
        )
        retrieval_time = time.perf_counter() - retrieval_start

        answer_start = time.perf_counter()
        answer = generate_answer(
            request.query,
            chunks,
            previous_messages
        )
        answer_time = time.perf_counter() - answer_start

        verification_start = time.perf_counter()
        verification = verify_answer(
            request.query,
            answer,
            chunks
        )
        verification_time = time.perf_counter() - verification_start

        total_time = time.perf_counter() - total_start

        print(
            f"ASTRA TIMING | Retrieval: {retrieval_time:.2f}s | "
            f"Answer: {answer_time:.2f}s | "
            f"Verification: {verification_time:.2f}s | "
            f"Total: {total_time:.2f}s"
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
                    "content": chunk.content,
                    "document": chunk.document_name
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

        result = []

        for conversation in conversations:
            first_message = (
                db.query(Message)
                .filter(
                    Message.conversation_id == conversation.id
                )
                .order_by(Message.created_at)
                .first()
            )

            result.append(
                {
                    "id": conversation.id,
                    "title": (
                        first_message.question[:70]
                        if first_message
                        else f"Conversation {conversation.id}"
                    ),
                    "created_at": conversation.created_at
                }
            )

        return result

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
                "id": message.id,
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

        summary_chunks = []
        total_characters = 0
        max_characters = 18000

        for chunk in chunks:
            if total_characters + len(chunk.content) > max_characters:
                break

            summary_chunks.append(chunk)
            total_characters += len(chunk.content)

        summary = generate_answer(
            "Provide a concise, grounded summary of this document. "
            "Use only the supplied document evidence. "
            "Cover the main topic, key points, and important conclusions. "
            "Do not invent statistics, facts, names, or conclusions. "
            "If a requested type of information is not present, do not infer it.",
            summary_chunks
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
