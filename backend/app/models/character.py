from sqlalchemy import Column, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class Character(Base):
    __tablename__ = "characters"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    role = Column(String(50))  # 'protagonist', 'antagonist', 'supporting'
    traits = Column(Text)  # JSON array
    backstory = Column(Text)
    arc_summary = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    story = relationship("Story", back_populates="characters")
