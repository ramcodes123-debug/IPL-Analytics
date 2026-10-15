
from typing import Optional
from pydantic import BaseModel, Field


class PlayerComparisonRequest(BaseModel):
    player_1: str = Field(..., min_length=1)
    player_2: str = Field(..., min_length=1)


class TeamComparisonRequest(BaseModel):
    team_1: str = Field(..., min_length=1)
    team_2: str = Field(..., min_length=1)


class PredictionRequest(BaseModel):
    player: Optional[str] = None
    team: Optional[str] = None
