from typing import Optional
from pydantic import BaseModel


class ProfileUpdate(BaseModel):
    phone: Optional[str] = None
    location: Optional[str] = None
    degree: Optional[str] = None
    university: Optional[str] = None
    graduation_year: Optional[int] = None
    experience_years: Optional[int] = None
    preferred_roles: Optional[str] = None
    preferred_technologies: Optional[str] = None
    career_goals: Optional[str] = None


class ProfileOut(ProfileUpdate):
    id: int
    user_id: int

    class Config:
        from_attributes = True
