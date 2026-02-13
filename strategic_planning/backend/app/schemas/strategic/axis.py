from pydantic import BaseModel
from typing import Optional

class StrategicAxisBase(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    weight: Optional[float] = 0.0
    color: Optional[str] = None

class StrategicAxisCreate(StrategicAxisBase):
    pass

class StrategicAxisResponse(StrategicAxisBase):
    id: int
    class Config:
        orm_mode = True
