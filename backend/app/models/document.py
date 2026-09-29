from sqlalchemy import Column,Integer,Text,String,ForeignKey


from pgvector.sqlalchemy import Vector


from app.database import Base

from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)
    filename = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)





class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id"),
        nullable=False
    )

    document_name = Column(String, nullable=False)

    page_number = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)

    embedding = Column(Vector(384), nullable=False)