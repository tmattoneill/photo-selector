import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from ..core.database import Base


# Association table for many-to-many relationship between portfolios and images
portfolio_images = Table(
    'portfolio_images',
    Base.metadata,
    Column('portfolio_id', UUID(as_uuid=True), ForeignKey('portfolios.id'), primary_key=True),
    Column('image_id', UUID(as_uuid=True), ForeignKey('images.id'), primary_key=True),
    Column('added_at', DateTime, default=datetime.utcnow)
)


class Portfolio(Base):
    """Named collection of images selected by the user."""
    
    __tablename__ = "portfolios"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    images = relationship("Image", secondary=portfolio_images, back_populates="portfolios")