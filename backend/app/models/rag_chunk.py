from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class RAGChunk(Base):
    __tablename__ = "rag_chunks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String(36), nullable=False)  # scene_id or character_id
    source_type = Column(String(20), nullable=False)  # 'scene', 'character'
    chunk_text = Column(Text, nullable=False)
    faiss_index = Column(Integer)  # Row index in FAISS
    created_at = Column(DateTime, default=func.now())

    # Relationships
    story = relationship("Story", back_populates="rag_chunks")
