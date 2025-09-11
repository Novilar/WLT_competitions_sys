from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

# убираем prefix, он задается в main.py
router = APIRouter()

@router.post("/", response_model=schemas.competition.CompetitionOut)
def create_competition(comp: schemas.competition.CompetitionCreate,
                       db: Session = Depends(get_db)):
    db_comp = models.competition.Competition(
        name=comp.name,
        date=comp.date,
        location=comp.location
    )
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.get("/", response_model=list[schemas.competition.CompetitionOut])
def get_competitions(db: Session = Depends(get_db)):
    return db.query(models.competition.Competition).all()
