from sqlalchemy import Column,Integer,Text,String


from pgvector.sqlalchemy import Vector


from app.database import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id = Column(Integer, primary_key=True, index=True)

    document_name = Column(String, nullable=False)

    page_number = Column(Integer, nullable=False)

    content = Column(Text, nullable=False)

    embedding = Column(Vector(384), nullable=False)