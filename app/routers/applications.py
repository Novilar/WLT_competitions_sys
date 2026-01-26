# app/routers/applications.py
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from uuid import UUID
from sqlalchemy.orm import selectinload

from app.core.application_transitions import STATUS_TRANSITIONS
from app.database import get_db
from app.domain.application_transitions import ROLE_TRANSITIONS
from app.models import (
    Application,
    ApplicationAthlete,
    ApplicationStaff,
    Competition,
    Federation,
    ApplicationType,
    ApplicationStatus, CompetitionRole, User, Notification, application,
)
from app.models.application_event import ApplicationEvent
from app.schemas import application as schemas
from app.core.deps import get_current_user, require_competition_role, can_user_transition
from app.schemas.application import ApplicationListItemOut, ApplicationStatusUpdate

router = APIRouter(
    prefix="/competitions/{competition_id}/applications",
    tags=["Applications"],
)

print("✅ allowed-transitions called")

# Вспомогательная функция
def check_submission_window(comp: Competition, app_type: str):
    today = datetime.utcnow().date()
    delta = (comp.date - today).days
    if app_type == "preliminary":
        if delta <= 14:
            raise HTTPException(400, "Срок подачи предварительных заявок истёк.")
    elif app_type == "final":
        if delta <= 14:
            raise HTTPException(400, "Срок подачи окончательных заявок истёк.")

# Создание или возврат федерации (ищем по имени, case-insensitive)
def get_or_create_federation(db: Session, name: str) -> Federation:
    if not name or not name.strip():
        raise HTTPException(400, "Название федерации не указано")
    name = name.strip()
    fed = db.query(Federation).filter(Federation.name.ilike(name)).first()
    if fed:
        return fed
    fed = Federation(name=name)
    db.add(fed)
    db.commit()
    db.refresh(fed)
    return fed

# Создание предварительной заявки
@router.post("/preliminary", response_model=schemas.ApplicationOut)
def create_preliminary_application(
    competition_id: UUID,
    app_in: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    comp = db.query(Competition).filter_by(id=competition_id).first()
    if not comp:
        raise HTTPException(404, "Соревнование не найдено")
    check_submission_window(comp, "preliminary")

    federation = get_or_create_federation(db, app_in.federation_name)

    # Проверка дублирования
    existing = (
        db.query(Application)
        .filter_by(competition_id=competition_id, federation_id=federation.id, type=ApplicationType.preliminary)
        .first()
    )
    if existing:
        raise HTTPException(400, "Предварительная заявка уже подана.")

    # Проверка лимитов
    male = len([a for a in app_in.athletes if a.gender == "male"])
    female = len([a for a in app_in.athletes if a.gender == "female"])
    if male > 10 or female > 10:
        raise HTTPException(400, "Максимум 10 мужчин и 10 женщин.")

    # Создаём заявку (используем enum-значения)
    application = Application(
        competition_id=competition_id,
        federation_id=federation.id,
        user_id=user.id,
        submitted_by=user.id,
        submitted_at=datetime.utcnow(),
        type=ApplicationType.preliminary,
        status=ApplicationStatus.submitted,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    # Добавляем спортсменов
    for a in app_in.athletes:
        athlete = ApplicationAthlete(
            application_id=application.id,
            last_name=a.last_name,
            first_name=a.first_name,
            middle_name=a.middle_name,
            gender=a.gender,
            birth_date=a.birth_date,
            weight_category=a.weight_category,
            entry_total=a.entry_total,
            is_main=a.is_main,
        )
        db.add(athlete)

    # Добавляем staff, если есть
    for s in getattr(app_in, "staff", []) or []:
        staff_row = ApplicationStaff(
            application_id=application.id,
            full_name=s.full_name,
            role=s.role,
            contact_info=s.contact_info,
        )
        db.add(staff_row)

    db.commit()
    db.refresh(application)

    # Подготовим дополнительные поля для удобства фронта
    # (pydantic with orm_mode прочитает их)
    setattr(application, "federation_name", federation.name)
    setattr(application, "submission_date", application.submitted_at)

    return application

# Создание окончательной заявки
@router.post("/final", response_model=schemas.ApplicationOut)
def create_final_application(
    competition_id: UUID,
    app_in: schemas.ApplicationCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    comp = db.query(Competition).filter_by(id=competition_id).first()
    if not comp:
        raise HTTPException(404, "Соревнование не найдено")
    check_submission_window(comp, "final")

    federation = get_or_create_federation(db, app_in.federation_name)

    # Проверяем наличие предварительной заявки
    prelim = (
        db.query(Application)
        .filter_by(competition_id=competition_id, federation_id=federation.id, type=ApplicationType.preliminary)
        .first()
    )
    if not prelim:
        raise HTTPException(400, "Сначала нужно подать предварительную заявку.")

    male_main = len([a for a in app_in.athletes if a.gender == "male" and a.is_main])
    female_main = len([a for a in app_in.athletes if a.gender == "female" and a.is_main])
    if male_main > 8 or female_main > 8:
        raise HTTPException(400, "Должно быть ровно 8 основных мужчин и 8 основных женщин.")

    application = Application(
        competition_id=competition_id,
        federation_id=federation.id,
        user_id=user.id,
        submitted_by=user.id,
        submitted_at=datetime.utcnow(),
        type=ApplicationType.final,
        status=ApplicationStatus.final_submitted,
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    for a in app_in.athletes:
        athlete = ApplicationAthlete(
            application_id=application.id,
            last_name=a.last_name,
            first_name=a.first_name,
            middle_name=a.middle_name,
            gender=a.gender,
            birth_date=a.birth_date,
            weight_category=a.weight_category,
            entry_total=a.entry_total,
            is_main=a.is_main,
        )
        db.add(athlete)

    for s in getattr(app_in, "staff", []) or []:
        staff_row = ApplicationStaff(
            application_id=application.id,
            full_name=s.full_name,
            role=s.role,
            contact_info=s.contact_info,
        )
        db.add(staff_row)

    db.commit()
    db.refresh(application)

    setattr(application, "federation_name", federation.name)
    setattr(application, "submission_date", application.submitted_at)

    return application





@router.get("/my", response_model=schemas.ApplicationOut | None)
def get_my_application(
    competition_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    app = (
        db.query(Application)
        .options(
            selectinload(Application.athletes),
            selectinload(Application.staff),
            selectinload(Application.events),
            selectinload(Application.federation),
        )
        .filter(
            Application.competition_id == competition_id,
            Application.submitted_by == user.id,
        )
        .order_by(Application.submitted_at.desc())
        .first()
    )

    if not app:
        return None

    # поля для фронта
    app.federation_name = app.federation.name if app.federation else None
    app.submission_date = app.submitted_at

    # 🔹 последнее событие (для needs_correction)
    last_event = (
        db.query(ApplicationEvent)
        .filter_by(application_id=app.id)
        .order_by(ApplicationEvent.timestamp.desc())
        .first()
    )

    app.last_comment = last_event.comment if last_event else None
    app.last_action = last_event.action if last_event else None

    return app




@router.get("", response_model=list[schemas.ApplicationListItemOut])
def list_applications(
    competition_id: UUID,
    type: ApplicationType | None = None,
    status: ApplicationStatus | None = None,
    federation_id: UUID | None = None,
    db: Session = Depends(get_db),
    _user = Depends(
        require_competition_role(
            ("secretary", "organizer", "super_admin"),
        )
    ),
):
    q = db.query(Application).filter(
        Application.competition_id == competition_id
    )

    if type:
        q = q.filter(Application.type == type)
    if status:
        q = q.filter(Application.status == status)
    if federation_id:
        q = q.filter(Application.federation_id == federation_id)

    applications = q.order_by(Application.created_at.desc()).all()

    result = []

    for app in applications:
        male_count = sum(1 for a in app.athletes if a.gender == "male")
        female_count = sum(1 for a in app.athletes if a.gender == "female")

        result.append(
            schemas.ApplicationListItemOut(
                id=app.id,
                type=app.type,
                status=app.status,
                federation_id=app.federation_id,
                federation_name=app.federation.name if app.federation else None,
                submission_date=app.submitted_at,
                submitted_by=app.submitted_by,
                male_count=male_count,
                female_count=female_count,
            )
        )

    return result


@router.get("/admin/{application_id}", response_model=schemas.ApplicationOut)
def get_application_admin(
    competition_id: UUID,
    application_id: UUID,
    db: Session = Depends(get_db),
    _user = Depends(
        require_competition_role(
            ("secretary", "organizer", "super_admin"),
        )
    ),
):
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.competition_id == competition_id,
        )
        .first()
    )

    if not application:
        raise HTTPException(404, "Заявка не найдена")

    setattr(application, "federation_name", application.federation.name if application.federation else None)
    setattr(application, "submission_date", application.submitted_at)

    return application




# Получение заявки по ID (для редактирования)
@router.get("/{application_id}", response_model=schemas.ApplicationOut)
def get_application_owner(
    competition_id: UUID,
    application_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    app = (
        db.query(Application)
        .filter_by(id=application_id, competition_id=competition_id)
        .first()
    )
    if not app:
        raise HTTPException(404, "Заявка не найдена")

    # Только автор может видеть свою заявку для редактирования
    if app.submitted_by != user.id:
        raise HTTPException(403, "Вы не можете просматривать чужую заявку")

    # Подготовка полей
    setattr(app, "federation_name", app.federation.name if app.federation else None)
    setattr(app, "submission_date", app.submitted_at)

    return app


@router.put("/{application_id}", response_model=schemas.ApplicationOut)
def update_application(
    competition_id: UUID,
    application_id: UUID,
    app_in: schemas.ApplicationUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    application = db.query(Application).filter_by(
        id=application_id,
        competition_id=competition_id
    ).first()

    if not application:
        raise HTTPException(404, "Заявка не найдена")

    if application.submitted_by != user.id:
        raise HTTPException(403, "Вы не можете редактировать чужую заявку.")

    if application.status in (
        ApplicationStatus.verified,
        ApplicationStatus.rejected,
    ):
        raise HTTPException(400, "Заявка не может быть изменена после финальной подачи")

    comp = db.query(Competition).filter_by(id=competition_id).first()
    delta = (comp.date - datetime.utcnow().date()).days

    if delta <= 14:
        if app_in.type != "final":
            raise HTTPException(400, "Можно редактировать только окончательную заявку")

        old_ids = {
            (a.last_name, a.first_name, a.middle_name, a.birth_date)
            for a in application.athletes
        }

        new_ids = {
            (a.last_name, a.first_name, a.middle_name, a.birth_date)
            for a in app_in.athletes
        }

        if old_ids != new_ids:
            raise HTTPException(400, "Нельзя менять состав атлетов после дедлайна")

    # обновляем тип
    application.type = app_in.type

    # пересоздаём спортсменов
    db.query(ApplicationAthlete).filter_by(
        application_id=application.id
    ).delete()

    for a in app_in.athletes:
        ath = ApplicationAthlete(
            application_id=application.id,
            last_name=a.last_name,
            first_name=a.first_name,
            middle_name=a.middle_name,
            gender=a.gender,
            birth_date=a.birth_date,
            weight_category=a.weight_category,
            entry_total=a.entry_total,
            is_main=a.is_main,
        )
        db.add(ath)

    if application.status == ApplicationStatus.needs_correction:
        application.status = ApplicationStatus.submitted

        event = ApplicationEvent(
            application_id=application.id,
            user_id=user.id,
            action="resubmitted_after_correction",
            comment="Заявка повторно отправлена после доработки",
        )
        db.add(event)

    # финальная подача после дедлайна
    if delta <= 14:
        application.status = ApplicationStatus.final_submitted

        event = ApplicationEvent(
            application_id=application.id,
            user_id=user.id,
            action="final_submitted",
            comment="Заявка подана как окончательная",
        )
        db.add(event)

    db.commit()
    db.refresh(application)

    setattr(application, "federation_name",
            application.federation.name if application.federation else None)
    setattr(application, "submission_date", application.submitted_at)

    return application



@router.post("/{application_id}/status")
def transition_application(
    competition_id: UUID,
    application_id: UUID,
    payload: ApplicationStatusUpdate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    application = db.query(Application).filter_by(
        id=application_id,
        competition_id=competition_id,
    ).first()

    if not application:
        raise HTTPException(404, "Заявка не найдена")


    if application.status in (
        ApplicationStatus.verified,
        ApplicationStatus.rejected,
    ):
        raise HTTPException(
            400,
            "Заявка не может быть изменена после финальной подачи",
        )


    from_status = application.status
    to_status = payload.status

    if to_status not in STATUS_TRANSITIONS.get(from_status, set()):
        raise HTTPException(403, "Недопустимый переход")

    #days_left = (application.competition.date - date.today()).days

    #if not can_user_transition(
    #    user.competition_roles,
    #    from_status,
    #    to_status,
    #    days_left,
    #):
    #    raise HTTPException(403, "Недостаточно прав")

    application.status = to_status

    if to_status == ApplicationStatus.needs_correction:
        db.add(
            Notification(
                user_id=application.submitted_by,
                application_id=application.id,
                message="Заявка возвращена на доработку",
            )
        )

    if to_status == ApplicationStatus.verified:
        db.add(
            Notification(
                user_id=application.submitted_by,
                application_id=application.id,
                message="Заявка подтверждена",
            )
        )

    event = ApplicationEvent(
        application_id=application.id,
        user_id=user.id,
        action=payload.action or f"transition_to_{to_status.value}",
        comment=payload.comment,
    )

    db.add(event)
    db.commit()

    db.refresh(application)

    return application



# Удаление заявки
@router.delete("/{application_id}")
def delete_application(competition_id: UUID, application_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):
    app = db.query(Application).filter_by(id=application_id, competition_id=competition_id).first()
    if not app:
        raise HTTPException(404, "Заявка не найдена")
    if app.submitted_by != user.id:
        raise HTTPException(403, "Удалять заявку может только её автор")

    if app.status in (
        ApplicationStatus.verified,
        ApplicationStatus.rejected,
    ):
        raise HTTPException(
            400,
            "Заявка не может быть изменена после финальной подачи",
        )

    comp = db.query(Competition).filter_by(id=competition_id).first()
    delta = (comp.date - datetime.utcnow().date()).days
    if delta <= 14:
        raise HTTPException(400, "Удаление запрещено за 14 дней до старта.")

    db.query(ApplicationAthlete).filter_by(application_id=app.id).delete()
    db.query(ApplicationStaff).filter_by(application_id=app.id).delete()
    db.delete(app)
    db.commit()

    return {"status": "deleted"}


@router.get(
    "/{application_id}/allowed-transitions",
    response_model=list[ApplicationStatus],
)
def get_allowed_transitions(
    competition_id: UUID,
    application_id: UUID,
    db: Session = Depends(get_db),
    user = Depends(get_current_user),
):
    print("llowed-transitions")
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.competition_id == competition_id,
        )
        .first()
    )

    if not application:
        raise HTTPException(404, "Заявка не найдена")

    # определяем роль пользователя
    role = (
        db.query(CompetitionRole)
        .filter_by(
            competition_id=competition_id,
            user_id=user.id,
        )
        .first()
    )

    if not role:
        return []

    current_status = application.status
    role_name = role.role

    print("STATUS:", application.status)
    print("ROLE:", role_name)
    print("RAW:", ROLE_TRANSITIONS.get(application.status))

    return ROLE_TRANSITIONS.get(current_status, {}).get(role_name, [])

@router.get(
    "/{application_id}/events",
    response_model=list[schemas.ApplicationEventOut],
)
def get_application_events(
    competition_id: UUID,
    application_id: UUID,
    db: Session = Depends(get_db),
    _user = Depends(
        require_competition_role(
            ("secretary", "organizer", "super_admin"),
        )
    ),
):
    events = (
        db.query(ApplicationEvent)
        .filter(ApplicationEvent.application_id == application_id)
        .order_by(ApplicationEvent.timestamp.asc())
        .all()
    )

    return events

