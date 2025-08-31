from sqlalchemy import Column, String, ForeignKey, CheckConstraint
from ..core.database import Base


class Duplicate(Base):
    """Duplicate image mapping to canonical as per algo-update.yaml spec."""
    
    __tablename__ = "duplicates"
    
    duplicate_sha256 = Column(String(64), ForeignKey("images.sha256", ondelete="CASCADE"), primary_key=True)
    canonical_sha256 = Column(String(64), ForeignKey("images.sha256", ondelete="CASCADE"), nullable=False)
    
    __table_args__ = (
        CheckConstraint('duplicate_sha256 <> canonical_sha256', name='dup_not_self'),
    )