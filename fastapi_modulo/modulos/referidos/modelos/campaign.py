from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, func
from sqlalchemy.orm import relationship
from fastapi_modulo.core.db import MAIN

class RefCampaign(MAIN):
    __tablename__ = "ref_campaign"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(String(500))
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    business_id = Column(Integer, ForeignKey("ref_program_assignment.id"), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    business = relationship("RefProgramAssignment", backref="campaigns")
