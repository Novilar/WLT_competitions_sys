import uuid
import enum
from datetime import datetime

from sqlalchemy import Column, String, Integer, DateTime, Enum, ForeignKey, UUID
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class LiftType(str, enum.Enum):
    snatch = "snatch"
    clean_and_jerk = "clean_and_jerk"


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id = Column(UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=False)
    athlete_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    weight = Column(Integer, nullable=False)
    lift_type = Column(String, nullable=False)  # snatch / clean_and_jerk
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)  # ✅ Добавляем это поле
    status = Column(String, default="open")  # open/closed
    result = Column(String, nullable=True)   # passed/failed

    created_at = Column(DateTime, default=datetime.utcnow)
    votes = relationship("Vote", back_populates="attempt", cascade="all, delete-orphan")


