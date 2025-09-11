from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

router = APIRouter()


@router.post("/", response_model=schemas.application.ApplicationOut)
def create_application(app_data: schemas.application.ApplicationCreate, db: Session = Depends(get_db)):
    db_app = models.application.Application(
        competition_id=app_data.competition_id,
        user_id=app_data.user_id,
        status=app_data.status,
        profile=app_data.profile,
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app
