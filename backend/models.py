from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

Base = declarative_base()

class Repo(Base):
    __tablename__ = "repos"

    id = Column(Integer, primary_key=True)
    owner = Column(String, nullable=False)
    repo = Column(String, nullable=False)
    status = Column(String, default="pending")  # pending, indexing, done, failed
    total_files = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

class CodeChunk(Base):
    __tablename__ = "code_chunks"

    id = Column(Integer, primary_key=True)
    repo_id = Column(Integer, ForeignKey("repos.id"), nullable=False)
    file_path = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    embedding = Column(Vector(768))
    created_at = Column(DateTime, server_default=func.now())