import uuid
from sqlalchemy import Column, Boolean, DateTime, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base


class Vote(Base):
    __tablename__ = "votes"

    id = Column(PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    attempt_id = Column(PGUUID(as_uuid=True), ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(PGUUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    role = Column(String, nullable=False)  # judge / jury
    vote = Column(Boolean, nullable=False)  # True = white, False = red
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    attempt = relationship("Attempt", back_populates="votes")

    __table_args__ = (
        UniqueConstraint("attempt_id", "user_id", "role", name="uq_vote_per_user_attempt"),
    )
