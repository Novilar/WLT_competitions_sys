from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.attempt.AttemptOut)
def record_attempt(data: schemas.attempt.AttemptCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    attempt = models.attempt.Attempt(
        competition_id=data.competition_id,
        user_id=user.id,
        weight=data.weight,
        result=data.result
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt

@router.get("/{competition_id}", response_model=list[schemas.attempt.AttemptOut])
def list_attempts(competition_id: int, db: Session = Depends(get_db)):
    return db.query(models.attempt.Attempt).filter(models.attempt.Attempt.competition_id == competition_id).all()
