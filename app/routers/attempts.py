from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.core.security import get_current_user
from uuid import UUID

router = APIRouter()


@router.post("/", response_model=schemas.attempt.AttemptOut)
def record_attempt(
    data: schemas.attempt.AttemptCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    # Проверяем, что пользователь — секретарь соревнования
    role = (
        db.query(models.competition_role.CompetitionRole)
        .filter_by(user_id=user.id, competition_id=data.competition_id)
        .first()
    )
    if not role or role.role != "secretary":
        raise HTTPException(status_code=403, detail="Недостаточно прав для создания попытки")

    # Проверяем, что выбранный участник имеет роль athlete на этом соревновании
    athlete_role = (
        db.query(models.competition_role.CompetitionRole)
        .filter_by(user_id=data.athlete_id, competition_id=data.competition_id, role="athlete")
        .first()
    )
    if not athlete_role:
        raise HTTPException(status_code=400, detail="Указанный пользователь не является участником этого соревнования")

    # Создаем новую попытку для выбранного участника
    attempt = models.attempt.Attempt(
        competition_id=data.competition_id,
        user_id=data.athlete_id,  # <-- теперь участник
        weight=data.weight,
        lift_type=data.lift_type,
        status="open"
    )

    db.add(attempt)
    db.commit()
    db.refresh(attempt)

    return attempt


@router.get("/{competition_id}", response_model=list[schemas.attempt.AttemptOut])
def list_attempts(competition_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(models.attempt.Attempt)
        .filter(models.attempt.Attempt.competition_id == competition_id)
        .all()
    )

@router.get("/participants")
def get_participants(competition_id: UUID, db: Session = Depends(get_db)):
    roles = (
        db.query(models.competition_role.CompetitionRole)
        .filter_by(competition_id=competition_id, role="athlete")
        .all()
    )
    return [r.user for r in roles]

@router.get("/my_roles")
def get_my_roles(db: Session = Depends(get_db), user=Depends(get_current_user)):
    roles = (
        db.query(models.competition_role.CompetitionRole)
        .filter(models.competition_role.CompetitionRole.user_id == user.id)
        .all()
    )
    return [
        {
            "role": r.role,
            "competition": {
                "id": str(r.competition.id),
                "name": r.competition.name,
                "date": str(r.competition.date),
            },
        }
        for r in roles
    ]

