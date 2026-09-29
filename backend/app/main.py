from fastapi import FastAPI, UploadFile, File
from app.database import engine, Base
from app.models.document import DocumentChunk

from sqlalchemy import text

from app.services.ingestion_service import process_document

import os
import shutil



app = FastAPI()


Base.metadata.create_all(bind=engine)



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
