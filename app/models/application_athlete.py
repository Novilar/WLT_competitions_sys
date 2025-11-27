from sqlalchemy import Column, String, Date, Float, Boolean, Enum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
import enum

from app.database import Base

class Gender(str, enum.Enum):
    male = "male"
    female = "female"


class ApplicationAthlete(Base):
    __tablename__ = "application_athletes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)

    gender = Column(Enum(Gender), nullable=False)
    last_name = Column(String, nullable=True)
    first_name = Column(String, nullable=True)
    middle_name = Column(String, nullable=True)
    birth_date = Column(Date, nullable=False)
    weight_category = Column(String, nullable=False)
    entry_total = Column(Float, nullable=True)
    is_main = Column(Boolean, default=False)

    application = relationship("Application", back_populates="athletes")
