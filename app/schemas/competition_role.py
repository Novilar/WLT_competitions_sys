from pydantic import BaseModel
from uuid import UUID
from app.schemas.roles import CompetitionRoleEnum


class CompetitionRoleBase(BaseModel):
    competition_id: UUID
    user_id: UUID
    role: CompetitionRoleEnum


class CompetitionRoleCreate(CompetitionRoleBase):
    pass


class CompetitionRoleOut(CompetitionRoleBase):
    id: UUID

    model_config = {
        "from_attributes": True,
    }
