from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import JSONB
from ..core.database import Base


class AppState(Base):
    """Application state storage."""
    
    __tablename__ = "app_state"
    
    key = Column(String, primary_key=True)
    val = Column(JSONB, nullable=False)