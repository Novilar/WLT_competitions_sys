from fastapi import FastAPI
from app.database import init_db
from fastapi.middleware.cors import CORSMiddleware

# Import routers here
from app.routers import auth, competitions, applications, draw, attempts


app = FastAPI(title="Weightlifting Competition MVP")

# CORS setup
origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(competitions.router, prefix="/competitions", tags=["Competitions"])
app.include_router(applications.router, prefix="/applications", tags=["Applications"])
app.include_router(draw.router, prefix="/draw", tags=["Draw"])
app.include_router(attempts.router, prefix="/attempts", tags=["Attempts"])

@app.on_event("startup")
def on_startup():
    init_db()
