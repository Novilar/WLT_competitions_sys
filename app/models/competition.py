from sqlalchemy import Column, String, Date
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

# Определяем модель Competition, которая соответствует таблице "competitions" в базе данных
class Competition(Base):
    __tablename__ = "competitions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    location = Column(String, nullable=False)
