from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid

from sqlalchemy.orm import relationship

from app.database import Base


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    competition_id = Column(UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=False)

    # 🔴 ВАЖНО: ссылка на жеребьёвку
    draw_entry_id = Column(
        UUID(as_uuid=True),
        ForeignKey("competition_draw_entries.id"),
        nullable=False
    )

    lift_type = Column(String, nullable=False)   # snatch / clean_and_jerk
    weight = Column(Integer, nullable=False)

    status = Column(String, default="active")      # open / closed
    result = Column(String, nullable=True)       # passed / failed

    created_at = Column(DateTime, default=datetime.utcnow)

    votes = relationship(
        "Vote",
        back_populates="attempt",
        cascade="all, delete-orphan"
    )
    draw_entry = relationship("CompetitionDrawEntry")
