from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app import models, schemas
from app.database import get_db
from app.core.deps import require_superadmin_or_own_competition

router = APIRouter(
    prefix="/competition_roles",
    tags=["competition_roles"]
)

# ---- Назначение роли ----
@router.post("/{competition_id}", response_model=schemas.competition_role.CompetitionRoleOut)
def assign_role(
    competition_id: UUID,
    role_in: schemas.competition_role.CompetitionRoleCreate,
    db: Session = Depends(get_db),
    user=Depends(require_superadmin_or_own_competition(["organizer"]))
):
    # опция — проверить, если роль в теле вдруг передали competition_id, что они совпадают
    new_role = models.competition_role.CompetitionRole(
        competition_id=competition_id,
        user_id=role_in.user_id,
        role=role_in.role
    )
    db.add(new_role)
    db.commit()
    db.refresh(new_role)
    return new_role


# ---- Удаление роли ----
@router.delete("/{competition_id}/{role_id}", status_code=204)
def delete_role(
    competition_id: str,
    role_id: str,
    db: Session = Depends(get_db),
    user=Depends(require_superadmin_or_own_competition(["organizer"]))
):
    role = db.query(models.competition_role.CompetitionRole).filter_by(
        id=role_id, competition_id=competition_id
    ).first()

    if not role:
        raise HTTPException(status_code=404, detail="Роль не найдена")

    # 🔒 Защита: организатор не может удалить сам себя, если он последний
    if role.role == "organizer" and role.user_id == user.id:
        organizers_count = db.query(models.competition_role.CompetitionRole).filter_by(
            competition_id=competition_id, role="organizer"
        ).count()

        if organizers_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Нельзя удалить последнего организатора соревнования"
            )

    db.delete(role)
    db.commit()
    return None



# ---- Получить роли по соревнованию ----
@router.get("/by_competition/{competition_id}", response_model=list[schemas.competition_role.CompetitionRoleOut])
def get_roles_for_competition(
    competition_id: UUID,
    db: Session = Depends(get_db)
):
    return db.query(models.competition_role.CompetitionRole).filter(
        models.competition_role.CompetitionRole.competition_id == competition_id
    ).all()


# ---- Получить роли по пользователю ----
@router.get("/by_user/{user_id}", response_model=list[schemas.competition_role.CompetitionRoleOut])
def get_roles_for_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    return db.query(models.competition_role.CompetitionRole).filter(
        models.competition_role.CompetitionRole.user_id == user_id
    ).all()
