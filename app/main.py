from fastapi import FastAPI
from app.database import init_db
from fastapi.middleware.cors import CORSMiddleware
from app.routers import competition_roles
from app.routers import users
from app.routers import judging
from app.routers import federations
#Импортируем роутеры
from app.routers import auth, competitions, applications, draw, attempts

# Создаём экземпляр FastAPI с указанием заголовка приложения
app = FastAPI(title="Weightlifting Competition MVP")

origins = [
    "http://localhost:5173",   # фронт в dev
    "http://127.0.0.1:5173",
    "http://10.194.145.224::8000",
    "http://10.194.145.224::5173",
]
# Настройка CORS
#origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router, prefix="/auth", tags=["Auth"]) # Роуты для аутентификации
app.include_router(competitions.router, prefix="/competitions", tags=["Competitions"]) # Роуты для соревнований
app.include_router(applications.router)
app.include_router(draw.router, prefix="/draw", tags=["Draw"]) # Роуты для жеребьёвки
app.include_router(attempts.router, prefix="/attempts", tags=["Attempts"]) # Роуты для попыток спортсменов
app.include_router(competition_roles.router)
app.include_router(users.router)
app.include_router(judging.router)
app.include_router(federations.router)






# Событие при старте приложения
@app.on_event("startup")
def on_startup():
    init_db()

