import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base


class Choice(Base):
    """User choice between two images."""
    
    __tablename__ = "choices"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    round = Column(Integer, nullable=False, index=True)
    left_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=False)
    right_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=False)
    selection = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User")
    left_image = relationship("Image", foreign_keys=[left_id])
    right_image = relationship("Image", foreign_keys=[right_id])
    
    __table_args__ = (
        CheckConstraint(
            "selection IN ('LEFT', 'RIGHT', 'SKIP')",
            name="selection_constraint"
        ),
    )