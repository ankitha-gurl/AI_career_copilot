from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.conversation import Conversation, Message
from app.models.user import User
from app.schemas.chat import ChatRequest
from app.services.ai_service import AIService, AIServiceError
from app.services.career_service import build_user_context

router = APIRouter(prefix="/copilot", tags=["AI Career Copilot"])


@router.post("/chat")
def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not payload.message.strip():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Message cannot be empty.")

    if payload.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == payload.conversation_id, Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    else:
        conversation = Conversation(user_id=current_user.id, title=payload.message[:50])
        db.add(conversation)
        db.flush()

    history = [{"role": m.role, "content": m.content} for m in conversation.messages]
    context = build_user_context(db, current_user)

    try:
        reply = AIService.career_chat(payload.message, context, history)
    except AIServiceError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    db.add(Message(conversation_id=conversation.id, role="user", content=payload.message))
    db.add(Message(conversation_id=conversation.id, role="assistant", content=reply))
    db.commit()

    return {"conversation_id": conversation.id, "reply": reply}


@router.get("/conversations")
def list_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.id.desc()).all()
    return [{"id": c.id, "title": c.title, "created_at": c.created_at.isoformat()} for c in conversations]


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter(
        Conversation.id == conversation_id, Conversation.user_id == current_user.id
    ).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return {
        "id": conversation.id, "title": conversation.title,
        "messages": [{"role": m.role, "content": m.content} for m in conversation.messages],
    }
