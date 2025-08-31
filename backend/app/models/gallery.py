from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, text, Index
from sqlalchemy.dialects.postgresql import JSONB
from ..core.database import Base


class Gallery(Base):
    """Named gallery with selection policy as per algo-update.yaml spec."""
    
    __tablename__ = "galleries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # BIGSERIAL equivalent
    name = Column(String, unique=True, nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text('NOW()'))
    selection_policy = Column(String, nullable=False)  # e.g., top_k / threshold_mu / threshold_ci / manual
    selection_params = Column(JSONB, nullable=False)
    duplicates_policy = Column(String, nullable=False)  # include_duplicates / collapse_to_canonical / exclude_duplicates
    engine_version = Column(String, nullable=False, default='duel-engine Elo+σ v1', server_default=text("'duel-engine Elo+σ v1'"))
    app_round_at_creation = Column(Integer, nullable=True)


class GalleryImage(Base):
    """Images within a gallery with ranking as per algo-update.yaml spec."""
    
    __tablename__ = "gallery_images"
    
    gallery_id = Column(Integer, ForeignKey("galleries.id", ondelete="CASCADE"), primary_key=True)
    sha256 = Column(String(64), ForeignKey("images.sha256", ondelete="CASCADE"), primary_key=True)
    rank = Column(Integer, nullable=False)
    
    __table_args__ = (
        Index('idx_gallery_images_rank', 'gallery_id', 'rank'),
    )