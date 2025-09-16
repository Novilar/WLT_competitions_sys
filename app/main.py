from fastapi import FastAPI
from app.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from app.routers import competition_roles



#Импортируем роутеры
from app.routers import auth, competitions, applications, draw, attempts

# Создаём экземпляр FastAPI с указанием заголовка приложения
app = FastAPI(title="Weightlifting Competition MVP")

# Настройка CORS
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["Auth"]) # Роуты для аутентификации
app.include_router(competitions.router, prefix="/aboba", tags=["Aboba"]) # Роуты для соревнований
app.include_router(applications.router, prefix="/applications", tags=["Applications"]) # Роуты для заявок
app.include_router(draw.router, prefix="/draw", tags=["Draw"]) # Роуты для жеребьёвки
app.include_router(attempts.router, prefix="/attempts", tags=["Attempts"]) # Роуты для попыток спортсменов
app.include_router(competition_roles.router)


# Событие при старте приложения
@app.on_event("startup")
def on_startup():
    init_db()
