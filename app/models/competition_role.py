import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class CompetitionRole(Base):
    __tablename__ = "competition_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id = Column(UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)

    # роль в рамках соревнования
    role = Column(String, nullable=False)

    # связи
    user = relationship("User", back_populates="competition_roles")
    competition = relationship("Competition", back_populates="competition_roles")
