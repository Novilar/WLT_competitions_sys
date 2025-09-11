import os
from pydantic_settings import BaseSettings

# Для централизованного хранения конфигурации
class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "dev_secret")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60*24*7))

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
# Объект настроек, который будем использовать по всему приложению
settings = Settings()
