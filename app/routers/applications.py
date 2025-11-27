from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app.models import Application, ApplicationAthlete, Competition, Federation, ApplicationType, ApplicationStatus
from app.schemas import application as schemas
from app.core.deps import get_current_user

router = APIRouter(prefix="/competitions/{competition_id}/applications", tags=["Applications"])

# ============================================================
# Вспомогательная функция
# ============================================================

def check_submission_window(comp: Competition, app_type: str):
    today = datetime.utcnow().date()
    delta = (comp.date - today).days
    if app_type == "preliminary":
        if delta <= 14:
            raise HTTPException(400, "Срок подачи предварительных заявок истёк.")
    elif app_type == "final":
        if delta <= 14:
            raise HTTPException(400, "Срок подачи окончательных заявок истёк.")


# ============================================================
# 🟢 Создание или возврат федерации
# ============================================================

def get_or_create_federation(db: Session, name: str) -> Federation:
    name = name.strip()
    # Проверяем существующую федерацию
    fed = db.query(Federation).filter(Federation.name.ilike(name)).first()
    if fed:
        return fed

    # Создаем новую
    fed = Federation(name=name)
    db.add(fed)
    db.commit()
    db.refresh(fed)
    return fed
# ============================================================
# 🟦 Создание ПРЕДВАРИТЕЛЬНОЙ заявки
# ============================================================

@router.post("/preliminary", response_model=schemas.ApplicationOut)
def create_preliminary_application(competition_id: UUID, app_in: schemas.ApplicationCreate,
                                   db: Session = Depends(get_db), user=Depends(get_current_user),
                                   ):
    comp = db.query(Competition).filter_by(id=competition_id).first()
    if not comp:
        raise HTTPException(404, "Соревнование не найдено")
    check_submission_window(comp, "preliminary")

    # Создаём или находим федерацию
    federation = get_or_create_federation(db, app_in.federation_name)

    # Проверка дублирования заявок
    existing = (
        db.query(Application)
        .filter_by(competition_id=competition_id, federation_id=federation.id, type="preliminary")
        .first()
    )
    if existing:
        raise HTTPException(400, "Предварительная заявка уже подана.")

    # Проверка лимитов
    male = len([a for a in app_in.athletes if a.gender == "male"])
    female = len([a for a in app_in.athletes if a.gender == "female"])
    if male > 10 or female > 10:
        raise HTTPException(400, "Максимум 10 мужчин и 10 женщин.")

    # Создаём заявку
    application = Application(
        competition_id=competition_id,
        federation_id=federation.id,
        user_id=user.id,  # ← обязательно
        submitted_by=user.id,
        submitted_at=datetime.utcnow(),
        type=ApplicationType.preliminary,  # ← лучше enum
        status=ApplicationStatus.draft,  # ← enum
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

    db.commit()

    return application


# ============================================================
# 🟨 Создание ОКОНЧАТЕЛЬНОЙ заявки
# ============================================================

@router.post("/final", response_model=schemas.ApplicationOut)
def create_final_application(competition_id: UUID, app_in: schemas.ApplicationCreate,
                             db: Session = Depends(get_db), user=Depends(get_current_user),
                             ):
    comp = db.query(Competition).filter_by(id=competition_id).first()
    if not comp:
        raise HTTPException(404, "Соревнование не найдено")
    check_submission_window(comp, "final")

    # Создаём или находим федерацию
    federation = get_or_create_federation(db, app_in.federation_name)

    # Проверка, что предварительная заявка существует
    prelim = (
        db.query(Application)
        .filter_by(competition_id=competition_id, federation_id=federation.id, type="preliminary")
        .first()
    )
    if not prelim:
        raise HTTPException(400, "Сначала нужно подать предварительную заявку.")

    # Проверка 8 основных
    male_main = len([a for a in app_in.athletes if a.gender == "male" and a.is_main])
    female_main = len([a for a in app_in.athletes if a.gender == "female" and a.is_main])
    if male_main != 8 or female_main != 8:
        raise HTTPException(400, "Должно быть ровно 8 основных мужчин и 8 основных женщин.")

    application = Application(
        competition_id=competition_id,
        federation_id=federation.id,
        user_id=user.id,  # ← обязательно
        submitted_by=user.id,
        submitted_at=datetime.utcnow(),
        type=ApplicationType.final,  # ← лучше enum
        # status=ApplicationStatus.draft,  # ← enum
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

    db.commit()

    return application


# ============================================================
# 🟧 Получение своей заявки
# ============================================================

@router.get("/my", response_model=schemas.ApplicationOut | None)
def get_my_application(competition_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user),):
    app = (db.query(Application).filter_by(competition_id=competition_id, submitted_by=user.id)
           .order_by(Application.submitted_at.desc()).first())
    if not app:
        raise HTTPException(404, "Заявка не найдена")
    return app

# ============================================================
# 🟩 Обновление заявки
# ============================================================

@router.put("/{application_id}", response_model=schemas.ApplicationOut)
def update_application(competition_id: UUID, application_id: UUID,
                       app_in: schemas.ApplicationUpdate, db: Session = Depends(get_db),
                       user=Depends(get_current_user),
                       ):
    application = (db.query(Application).filter_by(id=application_id, competition_id=competition_id).first())
    if not application:
        raise HTTPException(404, "Заявка не найдена")
    comp = db.query(Competition).filter_by(id=competition_id).first()
    delta = (comp.date - datetime.utcnow().date()).days
    if delta <= 14:
        raise HTTPException(400, "Редактирование запрещено менее чем за 14 дней.")

    if application.submitted_by != user.id:
        raise HTTPException(403, "Вы не можете редактировать чужую заявку.")

    # Удаляем всех предыдущих спортсменов
    db.query(ApplicationAthlete).filter_by(application_id=application.id).delete()

    # Добавляем новых
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

    db.commit()
    db.refresh(application)

    return application


# ============================================================
# 🟥 Удаление заявки
# ============================================================

@router.delete("/{application_id}")
def delete_application(competition_id: UUID, application_id: UUID,
                       db: Session = Depends(get_db), user=Depends(get_current_user),):
    app = (
        db.query(Application)
        .filter_by(id=application_id, competition_id=competition_id)
        .first())
    if not app:
        raise HTTPException(404, "Заявка не найдена")
    if app.submitted_by != user.id:
        raise HTTPException(403, "Удалять заявку может только её автор")

    comp = db.query(Competition).filter_by(id=competition_id).first()
    delta = (comp.date - datetime.utcnow().date()).days
    if delta <= 14:
        raise HTTPException(400, "Удаление запрещено за 14 дней до старта.")

    db.query(ApplicationAthlete).filter_by(application_id=app.id).delete()
    db.delete(app)
    db.commit()

    return {"status": "deleted"}
