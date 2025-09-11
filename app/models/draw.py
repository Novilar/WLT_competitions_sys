from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.database import Base

# Определяем модель DrawNumber, которая соответствует таблице "draw_numbers" в базе данных
class DrawNumber(Base):
    __tablename__ = "draw_numbers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    competition_id = Column(UUID(as_uuid=True), ForeignKey("competitions.id"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    number = Column(Integer, nullable=False)
