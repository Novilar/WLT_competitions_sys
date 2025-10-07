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
    user=Depends(get_current_user),
):
    db_attempt = models.attempt.Attempt(
        competition_id=competition_id,
        athlete_name=attempt_in.athlete_name,
        weight=attempt_in.weight,
        lift_type=attempt_in.lift_type,
        status="open",
    )
    db.add(db_attempt)
    db.commit()
    db.refresh(db_attempt)

    # 🔥 async/await, вместо create_task
    await manager.broadcast(str(competition_id), {
        "type": "attempt_started",
        "attempt": {
            "id": str(db_attempt.id),
            "athlete_name": db_attempt.athlete_name,
            "weight": db_attempt.weight,
            "lift_type": db_attempt.lift_type,
        }
    })
    return db_attempt

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
    return (
        db.query(models.attempt.Attempt)
        .filter(models.attempt.Attempt.competition_id == competition_id)
        .all()
    )

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
