from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app import models, schemas
from app.database import get_db
from app.core.deps import get_current_user   # ✅ добавлено
from app.schemas.user import UserPublic

router = APIRouter()

# ✅ создание соревнования только супер-админом или организатором
@router.post("/", response_model=schemas.competition.CompetitionOut)
def create_competition(
    comp: schemas.competition.CompetitionCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 🔒 Проверяем права
    if current_user.global_role not in ("super_admin", "organizer"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для создания соревнования",
        )

    # ✅ Создаём соревнование
    db_comp = models.competition.Competition(
        name=comp.name,
        date=comp.date,
        location=comp.location,
    )
    db.add(db_comp)
    db.commit()
    db.refresh(db_comp)

    # ✅ Если это организатор — присваиваем ему роль "organizer" на это соревнование
    if current_user.global_role == "organizer":
        organizer_role = models.competition_role.CompetitionRole(
            competition_id=db_comp.id,
            user_id=current_user.id,
            role="organizer",
        )
        db.add(organizer_role)
        db.commit()

    return db_comp


# ✅ Получить все соревнования
@router.get("/", response_model=list[schemas.competition.CompetitionOut])
def get_competitions(db: Session = Depends(get_db)):
    return db.query(models.competition.Competition).all()


# ✅ Получить участников конкретного соревнования
@router.get("/{competition_id}/participants")
def get_competition_participants(competition_id: UUID, db: Session = Depends(get_db)):
    roles = db.query(models.CompetitionRole).filter(
        models.CompetitionRole.competition_id == competition_id,
        models.CompetitionRole.role == "athlete"
    ).all()

    if not roles:
        raise HTTPException(status_code=404, detail="Участники не найдены")

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


'''@router.get("/competitions/{competition_id}/results")
def get_competition_results(competition_id: UUID, db: Session = Depends(get_db)):
    # Получаем всех участников
    athlete_roles = db.query(models.CompetitionRole).filter_by(
        competition_id=competition_id, role="athlete"
    ).all()
    athlete_ids = [r.user_id for r in athlete_roles]

    # Загружаем пользователей
    users = db.query(models.User).filter(models.User.id.in_(athlete_ids)).all()
    users_map = {u.id: u.full_name for u in users}

    # Загружаем все попытки
    attempts = db.query(models.Attempt).filter_by(competition_id=competition_id).all()

    # Формируем результаты по каждому участнику
    results = []
    for athlete_id in athlete_ids:
        athlete_attempts = [a for a in attempts if a.athlete_id == athlete_id and a.result == "passed"]

        snatch_attempts = [a.weight for a in athlete_attempts if a.lift_type == "snatch"]
        cj_attempts = [a.weight for a in athlete_attempts if a.lift_type == "clean_jerk"]

        best_snatch = max(snatch_attempts, default=0)
        best_cj = max(cj_attempts, default=0)
        total = best_snatch + best_cj if best_snatch and best_cj else 0

        results.append({
            "athlete_id": str(athlete_id),
            "athlete_name": users_map.get(athlete_id, "—"),
            "snatch_attempts": sorted(snatch_attempts, reverse=True),
            "clean_jerk_attempts": sorted(cj_attempts, reverse=True),
            "best_snatch": best_snatch,
            "best_clean_jerk": best_cj,
            "total": total
        })

    # Сортируем по общему результату (total)
    results = sorted(results, key=lambda x: x["total"], reverse=True)

    # Добавляем место
    for i, r in enumerate(results, start=1):
        r["place"] = i if r["total"] > 0 else None

    return results '''
