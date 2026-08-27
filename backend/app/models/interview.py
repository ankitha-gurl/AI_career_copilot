from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    target_role = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    user = relationship("User", back_populates="interview_sessions")
    questions = relationship("InterviewQuestion", back_populates="session", cascade="all, delete-orphan")


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False, index=True)

    question_type = Column(String(30), nullable=False)
    question_text = Column(Text, nullable=False)
    expected_concepts = Column(Text, nullable=True)
    model_answer = Column(Text, nullable=True)
    explanation = Column(Text, nullable=True)
    follow_up_questions = Column(Text, nullable=True)

    user_answer = Column(Text, nullable=True)
    evaluation_json = Column(Text, nullable=True)

    session = relationship("InterviewSession", back_populates="questions")
