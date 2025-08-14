from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import schemas, models
from app.database import get_db
from app.core.security import get_current_user

router = APIRouter()

@router.post("/", response_model=schemas.competition.CompetitionOut)
def create_competition(comp: schemas.competition.CompetitionCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    db_comp = models.competition.Competition(title=comp.title)
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)
    return db_comp

@router.get("/", response_model=list[schemas.competition.CompetitionOut])
def list_competitions(db: Session = Depends(get_db)):
    return db.query(models.competition.Competition).all()
