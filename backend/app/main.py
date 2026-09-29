from fastapi import FastAPI, UploadFile, File
from app.database import engine, Base,SessionLocal
from pydantic import BaseModel
from app.services.search_service import search_documents

from sqlalchemy import text

from app.services.ingestion_service import process_document
from app.services.llm_service import generate_answer
import os
import shutil

from app.models.conversation import Conversation
from app.models.message import Message




app = FastAPI()


Base.metadata.create_all(bind=engine)


class SearchRequest(BaseModel):
    query: str
    limit: int = 5



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

    chunk_count = process_document(
        file_path,
        file.filename
    )

    return {
        "message": "Document processed successfully",
        "document": file.filename,
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
        conversation = Conversation()
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

        chunks = search_documents(
            request.query,
            request.limit
        )

        answer = generate_answer(
            request.query,
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








