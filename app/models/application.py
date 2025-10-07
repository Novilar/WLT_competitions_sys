import uuid
from sqlalchemy import Column, String, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id = Column(UUID(as_uuid=True), ForeignKey("competitions.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.pending)
    profile = Column(String)

    # связи
    competition = relationship("Competition", back_populates="applications")
    user = relationship("User", back_populates="applications")
