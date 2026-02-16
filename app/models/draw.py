from uuid import uuid4

from sqlalchemy import Column, String, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime

from app.database import Base




class CompetitionDrawEntry(Base):
    __tablename__ = "competition_draw_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    competition_id = Column(UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=False)
    athlete_id = Column(UUID(as_uuid=True), ForeignKey("application_athletes.id"), nullable=False)

    gender = Column(String(10), nullable=False)
    weight_category = Column(String(10), nullable=False)

    group_letter = Column(String(2), nullable=False)
    lot_number = Column(Integer, nullable=False)

    entry_total = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    competition = relationship("Competition")
    athlete = relationship("ApplicationAthlete")
