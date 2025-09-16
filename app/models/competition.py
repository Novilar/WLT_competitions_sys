import uuid
from sqlalchemy import Column, String, Date
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base

class Competition(Base):
    __tablename__ = "competitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    location = Column(String, nullable=False)

    # связь с CompetitionRole
    competition_roles = relationship(
        "CompetitionRole",
        back_populates="competition",
        cascade="all, delete-orphan"
    )
