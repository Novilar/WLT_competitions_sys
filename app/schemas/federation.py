from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class FederationBase(BaseModel):
    name: str
    country: str | None = None

class FederationCreate(FederationBase):
    pass

class FederationOut(FederationBase):
    id: UUID
    created_at: datetime

    class Config:
        from_attributes = True
