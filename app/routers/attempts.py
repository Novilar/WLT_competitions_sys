from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from datetime import date

from app import models, schemas
from app.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/attempts", tags=["Attempts"])


@router.post("/", response_model=schemas.attempt.AttemptOut)
def create_attempt(
    data: schemas.attempt.AttemptCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # 1. Проверка роли секретаря
    role = (
        db.query(models.competition_role.CompetitionRole)
        .filter_by(
            competition_id=data.competition_id,
            user_id=user.id,
            role="secretary",
        )
        .first()
    )
    if not role:
        raise HTTPException(403, "Недостаточно прав")

    # 2. Проверка соревнования и даты
    competition = db.query(models.Competition).get(data.competition_id)
    if not competition:
        raise HTTPException(404, "Соревнование не найдено")

    if competition.date != date.today():
        raise HTTPException(
            400, "Попытки можно создавать только в день соревнования"
        )

    # 3. Проверка записи жеребьёвки
    draw_entry = (
        db.query(models.CompetitionDrawEntry)
        .filter_by(
            id=data.draw_entry_id,
            competition_id=data.competition_id,
        )
        .first()
    )
    if not draw_entry:
        raise HTTPException(404, "Участник жеребьёвки не найден")

    # 4. Создание попытки
    attempt = models.Attempt(
        competition_id=data.competition_id,
        draw_entry_id=data.draw_entry_id,
        weight=data.weight,
        lift_type=data.lift_type,
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt


@router.get(
    "/draw_entries/{competition_id}",
    response_model=list[schemas.attempt.DrawEntryOut]
)
def get_draw_entries(
    competition_id: UUID,
    db: Session = Depends(get_db)
):
    return (
        db.query(models.CompetitionDrawEntry)
        .filter(models.CompetitionDrawEntry.competition_id == competition_id)
        .order_by(
            models.CompetitionDrawEntry.group_letter,
            models.CompetitionDrawEntry.weight_category,
            models.CompetitionDrawEntry.lot_number,
        )
        .all()
    )



@router.get(
    "/competition/{competition_id}",
    response_model=list[schemas.attempt.AttemptOut],
)
def list_attempts(
    competition_id: UUID,
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Attempt)
        .filter(models.Attempt.competition_id == competition_id)
        .all()
    )
