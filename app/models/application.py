from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.database import Base


class ApplicationType(str, enum.Enum):
    preliminary = "preliminary"
    final = "final"


class ApplicationStatus(str, enum.Enum):
    draft = "draft"
    submitted = "submitted"
    verified = "verified"
    rejected = "rejected"


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id = Column(UUID(as_uuid=True), ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False)
    federation_id = Column(UUID(as_uuid=True), ForeignKey("federations.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 🔥 Добавляем!
    submitted_by = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    submitted_at = Column(DateTime, nullable=True)

    type = Column(Enum(ApplicationType), default=ApplicationType.preliminary)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.draft)

    submission_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    federation = relationship("Federation", backref="applications")
    athletes = relationship("ApplicationAthlete", cascade="all, delete-orphan")
    staff = relationship("ApplicationStaff", cascade="all, delete-orphan")

    user = relationship("User", back_populates="applications", foreign_keys=[user_id])
    submitted_by_user = relationship("User", foreign_keys=[submitted_by])

    # 🔥 back_populates на competition
    competition = relationship("Competition", back_populates="applications")

