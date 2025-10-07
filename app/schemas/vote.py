from pydantic import BaseModel


class VoteIn(BaseModel):
    vote: bool  # True = белая, False = красная
