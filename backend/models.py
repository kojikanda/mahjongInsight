from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    game_id: str


class AnalyzeResponse(BaseModel):
    game_id: str
    analysis: str
