import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base


# Association table for many-to-many relationship between portfolios and images
portfolio_images = Table(
    'portfolio_images',
    Base.metadata,
    Column('portfolio_id', UUID(as_uuid=True), ForeignKey('portfolios.id'), primary_key=True),
    Column('image_sha256', String(64), ForeignKey('images.sha256'), primary_key=True)
)


class Portfolio(Base):
    """Portfolio model for organizing collections of images per user."""
    
    __tablename__ = "portfolios"
    
    # Primary key - UUID
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Portfolio metadata
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # User ownership (references users table)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    images = relationship("Image", secondary=portfolio_images, back_populates="portfolios")