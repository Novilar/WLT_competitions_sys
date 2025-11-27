from sqlalchemy import Column, String, DateTime
from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
from datetime import datetime

class Federation(Base):
    __tablename__ = "federations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String, unique=True, nullable=False, index=True)
    country = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
