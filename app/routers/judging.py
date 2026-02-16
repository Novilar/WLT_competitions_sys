from fastapi import (
    APIRouter,
    Depends,
    WebSocket,
    WebSocketDisconnect,
    HTTPException,
    BackgroundTasks,
)
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app import models
from app.core.security import get_current_user
from app.schemas.vote import VoteIn

router = APIRouter(
    prefix="/judging",
    tags=["judging"]
)


# =====================
# WEBSOCKET MANAGER
# =====================
class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, competition_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(competition_id, []).append(websocket)

    def disconnect(self, competition_id: str, websocket: WebSocket):
        if competition_id in self.active_connections:
            self.active_connections[competition_id].remove(websocket)

    async def broadcast(self, competition_id: str, message: dict):
        for ws in self.active_connections.get(competition_id, []):
            await ws.send_json(message)


manager = ConnectionManager()


# =====================
# WEBSOCKET ENDPOINT
# =====================
@router.websocket("/competitions/{competition_id}/ws")
async def competition_ws(websocket: WebSocket, competition_id: UUID):
    await manager.connect(str(competition_id), websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(str(competition_id), websocket)


# =====================
# START ATTEMPT
# =====================
@router.post("/attempts/{attempt_id}/start")
def start_attempt(
    attempt_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    role = (
        db.query(models.competition_role.CompetitionRole)
        .filter_by(user_id=user.id, role="secretary")
        .first()
    )
    if not role:
        raise HTTPException(403, "Недостаточно прав")

    attempt = db.query(models.Attempt).get(attempt_id)
    if not attempt:
        raise HTTPException(404, "Попытка не найдена")

    attempt.status = "active"
    db.commit()

    draw = attempt.draw_entry
    athlete = draw.athlete

    athlete_name = " ".join(
        filter(None, [
            athlete.last_name,
            athlete.first_name,
            athlete.middle_name,
        ])
    )

    background_tasks.add_task(
        manager.broadcast,
        str(attempt.competition_id),
        {
            "type": "attempt_started",
            "attempt": {
                "id": str(attempt.id),
                "weight": attempt.weight,
                "lift_type": attempt.lift_type,
                "draw_entry": {
                    "group": draw.group_letter,
                    "weight_category": draw.weight_category,
                    "lot": draw.lot_number,
                    "athlete_name": athlete_name,
                },
            },
        },
    )

    return {"status": "started"}


# =====================
# CURRENT ATTEMPT
# =====================
@router.get("/competitions/{competition_id}/current_attempt")
def get_current_attempt(
    competition_id: UUID,
    db: Session = Depends(get_db),
):
    attempt = (
        db.query(models.Attempt)
        .filter(
            models.Attempt.competition_id == competition_id,
            models.Attempt.status == "active",
        )
        .order_by(models.Attempt.created_at.desc())
        .first()
    )

    if not attempt:
        return None

    draw = attempt.draw_entry
    athlete = draw.athlete

    athlete_name = " ".join(
        filter(None, [
            athlete.last_name,
            athlete.first_name,
            athlete.middle_name,
        ])
    )

    return {
        "id": str(attempt.id),
        "weight": attempt.weight,
        "lift_type": attempt.lift_type,
        "draw_entry": {
            "group": draw.group_letter,
            "weight_category": draw.weight_category,
            "lot": draw.lot_number,
            "athlete_name": athlete_name,
        },
    }


# =====================
# SUBMIT VOTE (AUTO CLOSE)
# =====================
@router.post("/attempts/{attempt_id}/vote")
def submit_vote(
    attempt_id: UUID,
    data: VoteIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    role = (
        db.query(models.competition_role.CompetitionRole)
        .filter_by(user_id=user.id, role="judge")
        .first()
    )
    if not role:
        raise HTTPException(403, "Недостаточно прав")

    attempt = db.query(models.Attempt).get(attempt_id)
    if not attempt:
        raise HTTPException(404, "Попытка не найдена")

    if attempt.status != "active":
        raise HTTPException(400, "Попытка неактивна")

    existing_vote = (
        db.query(models.Vote)
        .filter_by(
            attempt_id=attempt_id,
            user_id=user.id,
            role="judge",
        )
        .first()
    )
    if existing_vote:
        raise HTTPException(409, "Вы уже голосовали")

    vote = models.Vote(
        attempt_id=attempt_id,
        user_id=user.id,
        role="judge",
        vote=data.vote,
    )
    db.add(vote)
    db.commit()

    votes = (
        db.query(models.Vote)
        .filter_by(attempt_id=attempt_id, role="judge")
        .all()
    )

    judges_count = (
        db.query(models.competition_role.CompetitionRole)
        .filter_by(
            competition_id=attempt.competition_id,
            role="judge",
        )
        .count()
    )

    if len(votes) == judges_count:
        white = sum(v.vote is True for v in votes)
        red = sum(v.vote is False for v in votes)

        attempt.result = "passed" if white > red else "failed"
        attempt.status = "closed"
        db.commit()

        background_tasks.add_task(
            manager.broadcast,
            str(attempt.competition_id),
            {
                "type": "attempt_closed",
                "attempt_id": str(attempt.id),
                "result": attempt.result,
                "white": white,
                "red": red,
            },
        )

    background_tasks.add_task(
        manager.broadcast,
        str(attempt.competition_id),
        {
            "type": "vote_submitted",
            "attempt_id": str(attempt.id),
            "user_id": str(user.id),
            "vote": data.vote,
        },
    )

    return {"status": "ok"}
