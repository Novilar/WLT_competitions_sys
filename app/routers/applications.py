from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.application.ApplicationOut)
def create_application(app_data: schemas.application.ApplicationCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    comp = db.query(models.competition.Competition).filter(models.competition.Competition.id == app_data.competition_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    db_app = models.application.Application(
        competition_id=app_data.competition_id,
        user_id=user.id,
        profile=str(app_data.profile),
        status="pending"
    )
    db.add(db_app)
    db.commit()
    db.refresh(db_app)
    return db_app

@router.get("/{competition_id}", response_model=list[schemas.application.ApplicationOut])
def list_applications(competition_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(models.application.Application).filter(models.application.Application.competition_id == competition_id).all()
