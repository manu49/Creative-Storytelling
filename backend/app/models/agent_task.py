from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, func
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base
import uuid


class AgentTask(Base):
    __tablename__ = "agent_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String(36), ForeignKey("stories.id", ondelete="CASCADE"), nullable=False)
    scene_id = Column(String(36), ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True)
    task_type = Column(String(50), nullable=False)  # grammar_fix, coherence_check, etc
    status = Column(String(20), default="pending")  # pending, running, completed, failed
    priority = Column(Integer, default=5)  # 1 (high) to 10 (low)
    input_context = Column(Text)  # JSON: what triggered this task
    suggestion = Column(Text)  # Agent's output
    tool_calls_log = Column(Text)  # JSON array of tool_use interactions
    error_message = Column(Text)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    story = relationship("Story", back_populates="agent_tasks")
