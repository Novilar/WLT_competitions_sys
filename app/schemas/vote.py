from pydantic import BaseModel


class VoteIn(BaseModel):
    vote: bool  # True = white, False = red
