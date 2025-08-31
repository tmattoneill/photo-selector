from sqlalchemy import Column, String, Integer, Boolean, Float, text, Index
from sqlalchemy.orm import relationship
from ..core.database import Base


class Image(Base):
    """Image with Elo+σ rating system as per algo-update.yaml spec."""
    
    __tablename__ = "images"
    
    # Primary key
    sha256 = Column(String(64), primary_key=True)
    
    # Elo+σ rating fields
    mu = Column(Float, nullable=False, default=1500.0, server_default=text('1500.0'))
    sigma = Column(Float, nullable=False, default=350.0, server_default=text('350.0'))
    
    # Statistics counters
    exposures = Column(Integer, nullable=False, default=0, server_default=text('0'))
    likes = Column(Integer, nullable=False, default=0, server_default=text('0'))
    unlikes = Column(Integer, nullable=False, default=0, server_default=text('0'))
    skips = Column(Integer, nullable=False, default=0, server_default=text('0'))
    
    # Round tracking
    last_seen_round = Column(Integer, nullable=True)
    next_eligible_round = Column(Integer, nullable=True)  # for skip resurfacing window
    
    # Archive flag
    is_archived_hard_no = Column(Boolean, nullable=False, default=False, server_default=text('false'))
    
    __table_args__ = (
        Index('idx_images_mu_sigma', 'mu', 'sigma'),
        Index('idx_images_exposures', 'exposures'),
    )
    
    # Relationships
    portfolios = relationship("Portfolio", secondary="portfolio_images", back_populates="images")