from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class Scene(Base):
    __tablename__ = "scenes"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    order_index = Column(Integer, default=0)
    content = Column(Text, default="")  # Markdown content
    scene_type = Column(String(20), default="scene")  # 'scene', 'chapter', 'act'
    location = Column(String(255))
    time_of_day = Column(String(50))
    characters_present = Column(Text)  # JSON array of character IDs
    notes = Column(Text)
    version = Column(Integer, default=1)  # Increments on accept
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    # Relationships
    story = relationship("Story", back_populates="scenes")
