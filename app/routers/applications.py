from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.core.security import get_current_user

router = APIRouter()


@router.post("/", response_model=schemas.application.ApplicationOut)
def create_application(app_data: schemas.application.ApplicationCreate, db: Session = Depends(get_db),
                       current_user: models.user.User = Depends(get_current_user)):
    db_app = models.application.Application(
        competition_id=app_data.competition_id,
        user_id=current_user.id,
        status=app_data.status,
        profile=app_data.profile,
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@router.get("/", response_model=list[schemas.application.ApplicationOut])
def get_applications(db: Session = Depends(get_db)):
    return db.query(models.application.Application).all()