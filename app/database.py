from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# Настройка движка базы данных
connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(settings.DATABASE_URL, echo=False, connect_args=connect_args)

#Создание сессий
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)
# Базовый класс для моделей
Base = declarative_base()

# Зависимость для FastAPI маршрутов
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Инициализация таблиц
def init_db():
    from app import models
    Base.metadata.create_all(bind=engine)
