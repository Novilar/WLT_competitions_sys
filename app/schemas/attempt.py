from pydantic import BaseModel

class AttemptCreate(BaseModel):
    competition_id: int
    weight: int
    result: str  # "success" or "fail"

class AttemptOut(BaseModel):
    id: int
    competition_id: int
    user_id: int
    weight: int
    result: str

    class Config:
        orm_mode = True
