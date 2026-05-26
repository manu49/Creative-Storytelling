from sqlalchemy import Column, String, Text, DateTime, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class Story(Base):
    __tablename__ = "stories"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    genre = Column(String(50))  # 'novel', 'screenplay', 'web_series', 'short_story'
    logline = Column(Text)
    status = Column(String(20), default="draft")  # 'draft', 'active', 'archived'
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    scenes = relationship("Scene", back_populates="story", cascade="all, delete-orphan")
    characters = relationship("Character", back_populates="story", cascade="all, delete-orphan")
    agent_tasks = relationship("AgentTask", back_populates="story", cascade="all, delete-orphan")
    rag_chunks = relationship("RAGChunk", back_populates="story", cascade="all, delete-orphan")
