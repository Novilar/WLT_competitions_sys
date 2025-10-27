from typing import List
from fastapi import APIRouter, Depends,HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from uuid import UUID
from app.schemas.user import UserPublic

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



@router.get("/competitions/{competition_id}/participants")
def get_competition_participants(competition_id: UUID, db: Session = Depends(get_db)):
    roles = db.query(models.CompetitionRole).filter(
        models.CompetitionRole.competition_id == competition_id,
        models.CompetitionRole.role == "athlete"
    ).all()

    if not roles:
        raise HTTPException(status_code=404, detail="Участники не найдены")

    user_ids = [r.user_id for r in roles]
    users = db.query(models.User).filter(models.User.id.in_(user_ids)).all()

    # возвращаем как словари (чтобы JSON сериализовался)
    return [
        {
            "id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
        }
        for u in users
    ]

