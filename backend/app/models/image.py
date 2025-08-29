import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, LargeBinary, DateTime, ForeignKey, CheckConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base


class Image(Base):
    """Image statistics and choice tracking by SHA256."""
    
    __tablename__ = "images"
    
    sha256 = Column(String(64), primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Stats tracking
    exposures = Column(Integer, default=0, server_default=text('0'), nullable=False)
    likes = Column(Integer, default=0, server_default=text('0'), nullable=False)
    unlikes = Column(Integer, default=0, server_default=text('0'), nullable=False)
    skips = Column(Integer, default=0, server_default=text('0'), nullable=False)
    next_eligible_round = Column(Integer, nullable=True)
    
    # Relationships - portfolio relationship temporarily disabled for new architecture