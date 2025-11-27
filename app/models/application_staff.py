from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.database import Base

class ApplicationStaff(Base):
    __tablename__ = "application_staff"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    application_id = Column(UUID(as_uuid=True), ForeignKey("applications.id", ondelete="CASCADE"), nullable=False)

    full_name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    contact_info = Column(String, nullable=True)

    application = relationship("Application", back_populates="staff")
