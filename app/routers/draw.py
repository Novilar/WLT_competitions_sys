import random
from collections import defaultdict
from datetime import datetime, date
from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session
from uuid import UUID

from app import schemas
from app.database import get_db
from app.models import (
    Application,
    ApplicationAthlete,
    Competition,
    ApplicationStatus
)

from app.core.deps import get_current_user
from app.models.draw import CompetitionDrawEntry


router = APIRouter()


def chunk(lst, size):
    for i in range(0, len(lst), size):
        yield lst[i:i + size]


@router.post("/{competition_id}/draw")
def run_draw(
    competition_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    comp = db.query(Competition).filter_by(id=competition_id).first()
    if not comp:
        raise HTTPException(404, "Соревнование не найдено")

    if date.today() < comp.date:
        raise HTTPException(400, "Жеребьёвка доступна только в день соревнований")

    if comp.draw_done:
        raise HTTPException(400, "Жеребьёвка уже проведена")

    # Берём всех атлетов из verified-заявок
    athletes = (
        db.query(ApplicationAthlete)
        .join(Application)
        .filter(
            Application.competition_id == competition_id,
            Application.status == ApplicationStatus.verified,
        )
        .all()
    )

    if not athletes:
        raise HTTPException(400, "Нет атлетов для жеребьёвки")

    # Группируем по полу + категории
    buckets: dict[tuple[str, str], list[ApplicationAthlete]] = defaultdict(list)

    for a in athletes:
        key = (a.gender, a.weight_category)
        buckets[key].append(a)

    MAX_GROUP_SIZE = 12

    for (gender, cat), group_athletes in buckets.items():
        # сортировка по заявленному тоталу
        group_athletes.sort(key=lambda x: x.entry_total or 0, reverse=True)

        groups = list(chunk(group_athletes, MAX_GROUP_SIZE))

        for idx, group in enumerate(groups):
            letter = chr(ord("A") + idx)

            random.shuffle(group)

            for lot, a in enumerate(group, start=1):
                entry = CompetitionDrawEntry(
                    competition_id=competition_id,
                    athlete_id=a.id,
                    gender=gender,
                    weight_category=cat,
                    group_letter=letter,
                    lot_number=lot,
                    entry_total=a.entry_total,
                )
                db.add(entry)

    comp.draw_at = datetime.utcnow()

    comp.draw_done = True
    db.commit()

    return {"status": "ok"}


@router.get("/{competition_id}/draw", response_model=schemas.DrawResultOut)
def get_draw(
    competition_id: UUID,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    entries = (
        db.query(CompetitionDrawEntry)
        .join(ApplicationAthlete)
        .filter(CompetitionDrawEntry.competition_id == competition_id)
        .order_by(
            CompetitionDrawEntry.gender,
            CompetitionDrawEntry.weight_category,
            CompetitionDrawEntry.group_letter,
            CompetitionDrawEntry.lot_number,
        )
        .all()
    )

    if not entries:
        raise HTTPException(404, "Жеребьёвка ещё не проведена")

    groups_map: dict[tuple[str, str, str], list[CompetitionDrawEntry]] = defaultdict(list)

    for e in entries:
        key = (e.gender, e.weight_category, e.group_letter)
        groups_map[key].append(e)

    groups_out = []

    for (gender, cat, letter), items in groups_map.items():
        athletes_out = []

        for e in items:
            a = e.athlete
            athletes_out.append(
                schemas.DrawAthleteOut(
                    athlete_id=a.id,
                    last_name=a.last_name,
                    first_name=a.first_name,
                    gender=gender,
                    weight_category=cat,
                    entry_total=e.entry_total,
                    group_letter=letter,
                    lot_number=e.lot_number,
                )
            )

        groups_out.append(
            schemas.DrawGroupOut(
                gender=gender,
                weight_category=cat,
                group_letter=letter,
                athletes=athletes_out,
            )
        )

    return schemas.DrawResultOut(
        competition_id=competition_id,
        groups=groups_out,
    )
