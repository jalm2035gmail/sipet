from pydantic import BaseModel
from typing import Optional

class StrategicObjectiveBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None

class StrategicObjectiveCreate(StrategicObjectiveBase):
    pass

class StrategicObjectiveResponse(StrategicObjectiveBase):
    id: int
    class Config:
        orm_mode = True
