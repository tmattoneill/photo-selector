import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, LargeBinary, DateTime, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base


class Image(Base):
    """Image model storing canonical images and duplicates."""
    
    __tablename__ = "images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    sha256 = Column(String(64), unique=True, nullable=False, index=True)
    file_path = Column(String, nullable=False)
    mime_type = Column(String, nullable=False)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(Integer)
    base64_data = Column(LargeBinary, nullable=False)
    is_canonical = Column(Boolean, default=True, nullable=False)
    canonical_id = Column(UUID(as_uuid=True), ForeignKey("images.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Stats tracking
    exposures = Column(Integer, default=0, nullable=False)
    likes = Column(Integer, default=0, nullable=False)
    unlikes = Column(Integer, default=0, nullable=False)
    skips = Column(Integer, default=0, nullable=False)
    next_eligible_round = Column(Integer, nullable=True)
    
    # Relationships
    canonical = relationship("Image", remote_side=[id])
    duplicates = relationship("Image", back_populates="canonical")
    
    __table_args__ = (
        CheckConstraint(
            "(is_canonical = true AND canonical_id IS NULL) OR (is_canonical = false AND canonical_id IS NOT NULL)",
            name="canonical_constraint"
        ),
    )