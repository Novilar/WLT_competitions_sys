from pydantic import BaseModel

class DrawResult(BaseModel):
    user_id: int
    number: int

    class Config:
        orm_mode = True
