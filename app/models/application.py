from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.core.security import get_current_user  # берем юзера из токена

router = APIRouter()

@router.post("/", response_model=schemas.application.ApplicationOut)
def create_application(
    app_data: schemas.application.ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: models.user.User = Depends(get_current_user) # <-- текущий юзер
):
    db_app = models.application.Application(
        competition_id=app_data.competition_id,
        user_id=current_user.id,  # <-- автоматом из токена
        status=app_data.status,
        profile=app_data.profile,
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app
