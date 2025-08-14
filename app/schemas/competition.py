from pydantic import BaseModel

class CompetitionCreate(BaseModel):
    title: str

class CompetitionOut(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True
