from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app import models, schemas
from app.database import get_db
from app.core.deps import get_current_user
from app.models import Competition
from app.schemas.competition import CompetitionOut

router = APIRouter()


# ============================================================
# 🟢 СОЗДАНИЕ СОРЕВНОВАНИЯ (только супер-админ или организатор)
# ============================================================
@router.post("/", response_model=schemas.competition.CompetitionOut)
def create_competition(
    comp: schemas.competition.CompetitionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    if current_user.global_role not in ("super_admin", "organizer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания соревнования",
        )

    db_comp = models.competition.Competition(
        name=comp.name,
        date=comp.date,
        location=comp.location,
    )
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)

    if current_user.global_role == "organizer":
        organizer_role = models.competition_role.CompetitionRole(
            competition_id=db_comp.id,
            user_id=current_user.id,
            role="organizer",
        )
        db.add(organizer_role)
        db.commit()

    return db_comp


# ============================================================
# 🟦 ПОЛУЧИТЬ ВСЕ СОРЕВНОВАНИЯ
# ============================================================
@router.get("/", response_model=list[schemas.competition.CompetitionOut])
def get_competitions(db: Session = Depends(get_db)):
    return db.query(models.competition.Competition).all()


# ============================================================
# 🟩 ПОЛУЧИТЬ ОДНО СОРЕВНОВАНИЕ (важно! используется фронтом)
# ============================================================
@router.get("/{competition_id}", response_model=CompetitionOut)
def get_competition(competition_id: UUID, db: Session = Depends(get_db)):
    comp = db.query(Competition).filter_by(id=competition_id).first()
    if not comp:
        raise HTTPException(status_code=404, detail="Competition not found")
    return comp


# ============================================================
# 🟨 ПОЛУЧИТЬ ВСЕХ УЧАСТНИКОВ СОРЕВНОВАНИЯ
# ============================================================
@router.get("/{competition_id}/participants")
def get_competition_participants(competition_id: UUID, db: Session = Depends(get_db)):
    roles = db.query(models.CompetitionRole).filter(
        models.CompetitionRole.competition_id == competition_id,
        models.CompetitionRole.role == "athlete"
    ).all()

    if not roles:
        return []  # ⚠ лучше вернуть пустой список, а не 404

    user_ids = [r.user_id for r in roles]
    users = db.query(models.User).filter(models.User.id.in_(user_ids)).all()

    return [
        {
            "id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
        }
        for u in users
    ]
