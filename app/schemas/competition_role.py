from pydantic import BaseModel
from uuid import UUID
from app.schemas.roles import CompetitionRoleEnum

class CompetitionRoleCreate(BaseModel):
    user_id: UUID
    role: CompetitionRoleEnum

class CompetitionRoleOut(BaseModel):
    id: UUID
    competition_id: UUID
    user_id: UUID
    role: CompetitionRoleEnum

    model_config = {
        "from_attributes": True,
    }
