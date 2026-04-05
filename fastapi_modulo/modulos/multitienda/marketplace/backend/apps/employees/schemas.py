from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum


class EmployeeRole(str, Enum):
    manager = "manager"
    seller = "seller"
    cashier = "cashier"
    inventory = "inventory"
    support = "support"


class StoreEmployeeCreate(BaseModel):
    vendor_id: int
    user_id: int
    role: EmployeeRole = EmployeeRole.seller
    position: Optional[str] = ""
    full_name: Optional[str] = ""
    job_title: Optional[str] = ""
    phone: Optional[str] = ""
    department: Optional[str] = ""
    is_active: bool = True


class StoreEmployeeUpdate(BaseModel):
    role: Optional[EmployeeRole] = None
    position: Optional[str] = None
    full_name: Optional[str] = None
    job_title: Optional[str] = None
    phone: Optional[str] = None
    department: Optional[str] = None
    is_active: Optional[bool] = None


class StoreEmployeeRead(BaseModel):
    id: int
    vendor_id: int
    user_id: int
    role: EmployeeRole
    position: Optional[str]
    full_name: Optional[str]
    job_title: Optional[str]
    phone: Optional[str]
    department: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
