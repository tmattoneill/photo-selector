from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, text, Index
from ..core.database import Base


class Choice(Base):
    """User choice between two images as per algo-update.yaml spec."""
    
    __tablename__ = "choices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)  # BIGSERIAL equivalent
    round = Column(Integer, nullable=False)
    left_sha256 = Column(String(64), ForeignKey("images.sha256", ondelete="CASCADE"), nullable=False)
    right_sha256 = Column(String(64), ForeignKey("images.sha256", ondelete="CASCADE"), nullable=False)
    winner_sha256 = Column(String(64), nullable=True)  # NULL if skipped
    skipped = Column(Boolean, nullable=False, default=False, server_default=text('false'))
    decided_at = Column(DateTime, nullable=False, default=datetime.utcnow, server_default=text('NOW()'))
    
    __table_args__ = (
        Index('idx_choices_round', 'round'),
    )