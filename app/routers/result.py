from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.database import get_db
from app import models

router = APIRouter(
    prefix="/competitions",
    tags=["results"]
)


@router.get("/{competition_id}/results")
def get_competition_results(
    competition_id: UUID,
    db: Session = Depends(get_db),
):
    """
    Итоговая таблица результатов соревнования.
    Берём ТОЛЬКО закрытые попытки.
    """

    attempts = (
        db.query(models.Attempt)
        .filter(
            models.Attempt.competition_id == competition_id,
            models.Attempt.status == "closed",
        )
        .order_by(
            models.Attempt.created_at
        )
        .all()
    )

    if not attempts:
        return []

    results = []

    for attempt in attempts:
        draw = attempt.draw_entry
        athlete = draw.athlete

        athlete_name = " ".join(
            filter(
                None,
                [
                    athlete.last_name,
                    athlete.first_name,
                    athlete.middle_name,
                ],
            )
        )

        results.append({
            "attempt_id": str(attempt.id),
            "lift_type": attempt.lift_type,
            "weight": attempt.weight,
            "result": attempt.result,  # passed / failed
            "athlete": {
                "name": athlete_name,
                "group": draw.group_letter,
                "weight_category": draw.weight_category,
                "lot": draw.lot_number,
            },
        })

    return results
