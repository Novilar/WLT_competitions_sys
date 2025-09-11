from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db
from app.core.security import get_current_user
from uuid import UUID

router = APIRouter()

# Создание новой попытки на соревновании
@router.post("/", response_model=schemas.attempt.AttemptOut)
def record_attempt(data: schemas.attempt.AttemptCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # Создаем ORM-объект Attempt, связываем с текущим пользователем
    attempt = models.attempt.Attempt(
        competition_id=data.competition_id,
        user_id=user.id,
        weight=data.weight,
        result=data.result
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    # Возвращаем созданную попытку в формате Pydantic (AttemptOut)
    return attempt

# Получение списка всех попыток для конкретного соревнования
@router.get("/{competition_id}", response_model=list[schemas.attempt.AttemptOut])
def list_attempts(competition_id: UUID, db: Session = Depends(get_db)):
    # Возвращаем все попытки на указанное соревнование
    return db.query(models.attempt.Attempt).filter(models.attempt.Attempt.competition_id == competition_id).all()
