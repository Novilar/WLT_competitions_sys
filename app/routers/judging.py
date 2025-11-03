from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, List



from app.database import get_db
from app.core.deps import get_current_user
from app import models
from app.schemas import attempt, vote

router = APIRouter(
    prefix="/competitions/{competition_id}",
    tags=["Judging"]
)

# ----------------- WebSocket Manager -----------------
class ConnectionManager:
    def __init__(self):
        self.rooms: Dict[str, List[WebSocket]] = {}

    async def connect(self, competition_id: str, ws: WebSocket):
        await ws.accept()
        self.rooms.setdefault(competition_id, []).append(ws)

    def disconnect(self, competition_id: str, ws: WebSocket):
        if competition_id in self.rooms and ws in self.rooms[competition_id]:
            self.rooms[competition_id].remove(ws)

    async def broadcast(self, competition_id: str, message: dict):
        for ws in list(self.rooms.get(competition_id, [])):
            try:
                await ws.send_json(message)
            except Exception:
                self.disconnect(competition_id, ws)


manager = ConnectionManager()

@router.websocket("/ws")
async def ws_endpoint(websocket: WebSocket, competition_id: str):
    await manager.connect(competition_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(competition_id, websocket)

# ----------------- REST API -----------------
@router.post("/attempts", response_model=attempt.AttemptOut)
async def create_attempt(
    competition_id: UUID,
    attempt_in: attempt.AttemptCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    # 🛑 Проверка: есть ли уже активная попытка
    active_attempt = (
        db.query(models.attempt.Attempt)
        .filter_by(competition_id=competition_id, status="open")
        .first()
    )
    if active_attempt:
        raise HTTPException(
            status_code=400,
            detail="Нельзя создать новую попытку, пока предыдущая не завершена."
        )

    # 🛑 Проверка: не превышено ли число попыток (максимум 3)
    existing_attempts = (
        db.query(models.attempt.Attempt)
        .filter(
            models.attempt.Attempt.competition_id == competition_id,
            models.attempt.Attempt.athlete_id == attempt_in.athlete_id,
            models.attempt.Attempt.lift_type == attempt_in.lift_type,
        )
        .count()
    )

    if existing_attempts >= 3:
        raise HTTPException(
            status_code=400,
            detail=f"Нельзя добавить более трёх попыток для упражнения '{attempt_in.lift_type}'.",
        )

    # ✅ Создаем новую попытку
    db_attempt = models.attempt.Attempt(
        competition_id=competition_id,
        athlete_id=attempt_in.athlete_id,
        weight=attempt_in.weight,
        lift_type=attempt_in.lift_type,
        status="open",
        user_id=current_user.id,
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)

    await manager.broadcast(str(competition_id), {
        "type": "attempt_started",
        "attempt": {
            "id": str(db_attempt.id),
            "athlete_id": str(db_attempt.athlete_id),
            "weight": db_attempt.weight,
            "lift_type": db_attempt.lift_type,
            "user_id": str(db_attempt.user_id),
        }
    })

    # 🟢 возвращаем с именем спортсмена
    from app.models.user import User
    athlete = db.query(User).filter(User.id == attempt_in.athlete_id).first()

    return attempt.AttemptOut.from_orm(db_attempt).copy(
        update={"athlete_name": athlete.full_name if athlete else None}
    )




@router.get("/attempts/current", response_model=attempt.AttemptOut | None)
async def get_current_attempt(competition_id: UUID, db: Session = Depends(get_db)):
    return (
        db.query(models.attempt.Attempt)
        .filter_by(competition_id=competition_id, status="open")
        .order_by(models.attempt.Attempt.created_at.desc())
        .first()
    )

# после существующего кода import'ов — ничего доп. не нужно

@router.post("/attempts/{attempt_id}/vote")
async def submit_vote(
    competition_id: UUID,
    attempt_id: UUID,
    vote_in: vote.VoteIn,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    attempt_obj = (
        db.query(models.attempt.Attempt)
        .filter_by(id=attempt_id, competition_id=competition_id)
        .first()
    )
    if not attempt_obj:
        raise HTTPException(404, "Attempt not found")
    if attempt_obj.status not in ("open", "review"):
        raise HTTPException(400, "Attempt is not open for voting")

    # Проверка роли
    cr = (
        db.query(models.competition_role.CompetitionRole)
        .filter_by(competition_id=competition_id, user_id=user.id)
        .first()
    )
    if not cr:
        raise HTTPException(403, "No role on this competition")
    if cr.role not in ("judge", "jury"):
        raise HTTPException(403, "User is not judge or jury")

    role = cr.role

    # Проверка дубликата
    existing = (
        db.query(models.vote.Vote)
        .filter_by(attempt_id=attempt_id, user_id=user.id, role=role)
        .first()
    )
    if existing:
        raise HTTPException(400, "User already voted for this attempt")

    v = models.vote.Vote(
        attempt_id=attempt_id,
        user_id=user.id,
        role=role,
        vote=vote_in.vote,
    )
    db.add(v)
    db.commit()

    # ---- NEW: broadcast single vote update to all clients ----
    # приводи id к строке, чтобы на фронте ключи были строками
    await manager.broadcast(str(competition_id), {
        "type": "vote_update",
        "attempt_id": str(attempt_id),
        "user_id": str(user.id),
        "role": role,
        "vote": bool(vote_in.vote),
    })
    # ---------------------------------------------------------

    # Подсчёт голосов (как было)
    judge_votes = (
        db.query(models.vote.Vote)
        .filter_by(attempt_id=attempt_id, role="judge")
        .all()
    )
    if len(judge_votes) >= 3 and attempt_obj.status == "open":
        yes = sum(1 for vv in judge_votes if vv.vote)
        result = "passed" if yes >= 2 else "failed"
        attempt_obj.status = "decided"
        attempt_obj.result = result
        db.add(attempt_obj)
        db.commit()

        await manager.broadcast(str(competition_id), {
            "type": "attempt_result",
            "result": result,
            "by": "judges",
            "counts": {"yes": yes, "no": len(judge_votes) - yes}
        })

    return {"status": "ok"}



@router.get("/attempts", response_model=list[attempt.AttemptOut])
async def get_attempts(competition_id: UUID, db: Session = Depends(get_db)):
    from app.models.user import User  # импорт внутри, чтобы не было циклов

    attempts = (
        db.query(
            models.attempt.Attempt,
            User.full_name.label("athlete_name")
        )
        .join(User, User.id == models.attempt.Attempt.athlete_id)
        .filter(models.attempt.Attempt.competition_id == competition_id)
        .all()
    )

    # превращаем результат в список Pydantic-схем
    return [
        attempt.AttemptOut(
            **a.Attempt.__dict__,
            athlete_name=a.athlete_name
        )
        for a in attempts
    ]

@router.get("/attempts/{attempt_id}/votes")
def get_attempt_votes(
    competition_id: UUID,
    attempt_id: UUID,
    db: Session = Depends(get_db),
):
    votes = db.query(models.vote.Vote).filter_by(attempt_id=attempt_id).all()
    return [
        {"user_id": str(v.user_id), "vote": bool(v.vote), "role": v.role}
        for v in votes
    ]

# ----------------- РЕЗУЛЬТАТЫ СОРЕВНОВАНИЙ -----------------
@router.get("/results")
async def get_competition_results(competition_id: UUID, db: Session = Depends(get_db)):
    """
    Возвращает таблицу результатов:
    - 3 попытки рывка и толчка
    - лучший результат
    - сумма
    - место
    """

    from app.models.user import User

    # 1️⃣ Загружаем все попытки соревнования
    attempts = (
        db.query(models.attempt.Attempt)
        .filter(models.attempt.Attempt.competition_id == competition_id)
        .order_by(models.attempt.Attempt.created_at)
        .all()
    )

    if not attempts:
        return []

    # 2️⃣ Группируем попытки по атлету
    athletes: dict[UUID, dict] = {}

    for a in attempts:
        athlete = athletes.setdefault(a.athlete_id, {
            "athlete_id": str(a.athlete_id),
            "athlete_name": None,
            "snatch_attempts": [],
            "clean_jerk_attempts": [],
        })

        # добавляем вес и успешность (если решено)
        if a.lift_type == "snatch":
            athlete["snatch_attempts"].append({
                "weight": a.weight,
                "result": a.result
            })
        elif a.lift_type in ("clean_jerk", "clean_and_jerk"):
            athlete["clean_jerk_attempts"].append({
                "weight": a.weight,
                "result": a.result
            })

    # 3️⃣ Подставляем имена атлетов
    user_ids = [a for a in athletes.keys() if a]
    users = db.query(User).filter(User.id.in_(user_ids)).all()
    for u in users:
        if u.id in athletes:
            athletes[u.id]["athlete_name"] = u.full_name

    # 4️⃣ Подсчёт лучших результатов и суммы
    for athlete in athletes.values():
        snatch_best = max(
            [a["weight"] for a in athlete["snatch_attempts"] if a["result"] == "passed"],
            default=0,
        )
        cj_best = max(
            [a["weight"] for a in athlete["clean_jerk_attempts"] if a["result"] == "passed"],
            default=0,
        )

        athlete["snatch_best"] = snatch_best
        athlete["clean_jerk_best"] = cj_best
        athlete["total"] = snatch_best + cj_best

    # 5️⃣ Сортировка и присвоение мест
    sorted_athletes = sorted(
        athletes.values(),
        key=lambda x: x["total"],
        reverse=True
    )

    for i, a in enumerate(sorted_athletes, start=1):
        a["place"] = i

    return sorted_athletes
