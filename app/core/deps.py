from uuid import UUID

from fastapi import Depends, HTTPException, status
from starlette.requests import Request

from app.core.security import get_current_user
from app import models
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import CompetitionRole, User, ApplicationStatus


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


def require_competition_role(allowed_roles: tuple[str, ...]):
    def dependency(
        request: Request,
        db = Depends(get_db),
        user = Depends(get_current_user),
    ):
        competition_id = request.path_params.get("competition_id")

        if not competition_id:
            raise HTTPException(400, "competition_id not found in path")
        role = (
            db.query(CompetitionRole)
            .filter_by(
                competition_id=competition_id,
                user_id=user.id,
            )
            .first()
        )

        if not role or role.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Недостаточно прав")

        return user

    return dependency


def can_user_transition(
    user_role: str,
    from_status: ApplicationStatus,
    to_status: ApplicationStatus,
    days_before_competition: int | None = None,
) -> bool:
    if user_role == "representative":
        if from_status in (
            ApplicationStatus.draft,
            ApplicationStatus.needs_correction,
        ) and to_status == ApplicationStatus.submitted:
            return True

        if (
            from_status == ApplicationStatus.prelim_verified
            and to_status == ApplicationStatus.final_submitted
            and days_before_competition is not None
            and days_before_competition <= 14
        ):
            return True

    if user_role in ("secretary", "organizer", "super_admin"):
        if (
            from_status == ApplicationStatus.submitted
            and to_status
            in (
                ApplicationStatus.prelim_verified,
                ApplicationStatus.needs_correction,
            )
        ):
            return True

        if (
            from_status == ApplicationStatus.final_submitted
            and to_status
            in (
                ApplicationStatus.verified,
                ApplicationStatus.rejected,
            )
        ):
            return True

    return False
