from sqlalchemy import Column, ForeignKey, Integer, String, Text, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class CareerProfile(Base):
    __tablename__ = "career_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)

    phone = Column(String(30), nullable=True)
    location = Column(String(150), nullable=True)

    degree = Column(String(150), nullable=True)
    university = Column(String(150), nullable=True)
    graduation_year = Column(Integer, nullable=True)

    experience_years = Column(Integer, nullable=True)
    preferred_roles = Column(Text, nullable=True)
    preferred_technologies = Column(Text, nullable=True)
    career_goals = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user = relationship("User", back_populates="profile")
