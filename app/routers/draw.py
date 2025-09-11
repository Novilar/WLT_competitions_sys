from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import random
from uuid import UUID
from app import models, schemas
from app.database import get_db
from app.core.security import get_current_user

router = APIRouter()

# Маршрут для проведения жеребьёвки участников соревнования
@router.post("/{competition_id}", response_model=list[schemas.draw.DrawResult])
def run_draw(competition_id: UUID, db: Session = Depends(get_db), user=Depends(get_current_user)):

    # Получаем все заявки с одобренным статусом для данного соревнования
    apps = db.query(models.application.Application).filter(models.application.Application.competition_id == competition_id, models.application.Application.status == "approved").all()
    # Генерируем список последовательных номеров для жеребьёвки
    numbers = list(range(1, len(apps) + 1))
    # Перемешиваем номера случайным образом
    random.shuffle(numbers)
    results = []
    # Присваиваем каждому участнику случайный номер
    for app_obj, num in zip(apps, numbers):
        draw_entry = models.draw.DrawNumber(competition_id=competition_id, user_id=app_obj.user_id, number=num)
        db.add(draw_entry)
        results.append(draw_entry)
    db.commit()
    return results
