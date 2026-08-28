from sqlmodel import SQLModel, Field
from typing import Optional
from sqlalchemy import UniqueConstraint

class RagChunk(SQLModel, table=True):
    __tablename__ = "rag_chunks"
    __table_args__ = (
        UniqueConstraint("source", "chunk_index", name="uq_source_chunk_index"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    source: str = Field(nullable=False, index=True)
    chunk_index: int = Field(nullable=False, index=True)
    content: str = Field(nullable=False)
    embedding: str = Field(nullable=False)