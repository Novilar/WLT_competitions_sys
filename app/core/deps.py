from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
from app import models
from sqlalchemy.orm import Session
from app.database import get_db


def require_global_role(required_roles: list[str]):
    """
    Проверяет глобальную роль пользователя (super_admin, athlete).
    """
    def role_checker(user: models.user.User = Depends(get_current_user)):
        if user.global_role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав (глобальная роль)"
            )
        return user
    return role_checker


def require_competition_role(required_roles: list[str]):
    """
    Проверяет роль пользователя в конкретном соревновании.
    """
    def role_checker(
        competition_id: str,
        db: Session = Depends(get_db),
        user: models.user.User = Depends(get_current_user)
    ):
        roles = db.query(models.competition_role.CompetitionRole).filter_by(
            user_id=user.id, competition_id=competition_id
        ).all()

        if not any(r.role in required_roles for r in roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав (роль в соревновании)"
            )
        return user
    return role_checker


def require_superadmin_or_own_competition(required_roles: list[str]):
    """
    Разрешает доступ:
    - если пользователь super_admin (ко всем соревнованиям)
    - если organizer И он назначен в это соревнование
    """
    def role_checker(
        competition_id: str,
        db: Session = Depends(get_db),
        user: models.user.User = Depends(get_current_user)
    ):
        # супер-админ имеет полный доступ
        if user.global_role == "super_admin":
            return user

        # проверяем, что пользователь organizer именно этого соревнования
        role = db.query(models.competition_role.CompetitionRole).filter_by(
            user_id=user.id, competition_id=competition_id, role="organizer"
        ).first()

        if not role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав (не organizer этого соревнования)"
            )
        return user
    return role_checker
