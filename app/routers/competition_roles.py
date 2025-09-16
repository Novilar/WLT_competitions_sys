from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import models, schemas
from app.database import get_db

router = APIRouter(
    prefix="/competition_roles",
    tags=["competition_roles"]
)


@router.post("/", response_model=schemas.competition_role.CompetitionRoleOut)
def assign_role(
    role_in: schemas.competition_role.CompetitionRoleCreate,
    db: Session = Depends(get_db)
):
    # Проверяем, что пользователь существует
    user = db.query(models.user.User).filter(models.user.User.id == role_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем, что соревнование существует
    competition = db.query(models.competition.Competition).filter(models.competition.Competition.id == role_in.competition_id).first()
    if not competition:
        raise HTTPException(status_code=404, detail="Competition not found")

    # Создаем роль
    db_role = models.competition_role.CompetitionRole(
        competition_id=role_in.competition_id,
        user_id=role_in.user_id,
        role=role_in.role.value
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    return db_role


@router.get("/by_competition/{competition_id}", response_model=list[schemas.competition_role.CompetitionRoleOut])
def get_roles_for_competition(
    competition_id: UUID,
    db: Session = Depends(get_db)
):
    return db.query(models.competition_role.CompetitionRole).filter(
        models.competition_role.CompetitionRole.competition_id == competition_id
    ).all()


@router.get("/by_user/{user_id}", response_model=list[schemas.competition_role.CompetitionRoleOut])
def get_roles_for_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    return db.query(models.competition_role.CompetitionRole).filter(
        models.competition_role.CompetitionRole.user_id == user_id
    ).all()
