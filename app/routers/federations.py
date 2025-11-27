from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from app.database import get_db
from app.models.federation import Federation
from app.schemas.federation import FederationCreate, FederationOut

router = APIRouter(prefix="/federations", tags=["Federations"])


# Получить список всех федераций
@router.get("/", response_model=list[FederationOut])
def get_federations(db: Session = Depends(get_db)):
    return db.query(Federation).all()


# Получить по имени
@router.get("/search", response_model=FederationOut | None)
def find_federation(name: str, db: Session = Depends(get_db)):
    fed = db.query(Federation).filter(Federation.name == name).first()
    if not fed:
        raise HTTPException(404, "Федерация не найдена")
    return fed


# Создать федерацию
@router.post("/", response_model=FederationOut)
def create_federation(fed_in: FederationCreate, db: Session = Depends(get_db)):

    # проверяем, что нет дубликата
    existing = db.query(Federation).filter(Federation.name == fed_in.name).first()
    if existing:
        return existing

    fed = Federation(
        id=uuid4(),
        name=fed_in.name,
        country=fed_in.country,
    )
    db.add(fed)
    db.commit()
    db.refresh(fed)

    return fed
