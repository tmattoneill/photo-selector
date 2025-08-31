from sqlalchemy import Column, Integer, CheckConstraint, text
from ..core.database import Base


class AppState(Base):
    """Application state with round counter as per algo-update.yaml spec."""
    
    __tablename__ = "app_state_new"  # Using new table for now
    
    id = Column(Integer, primary_key=True)
    round = Column(Integer, nullable=False, default=0, server_default=text('0'))
    
    __table_args__ = (
        CheckConstraint('id = 1', name='app_state_singleton'),
    )