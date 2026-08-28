from sqlmodel import Session, select
from fastapi import  HTTPException
from uuid import UUID
from schemas.database_schema import Message, Conversation

def msg_or_404(msg_id: UUID, session: Session):
    msg = session.get(Message, msg_id)
    if msg is None:
        raise HTTPException(
            status_code=404,
            detail="Message not found"
        )
    return msg

def create_message(item: Message, session: Session):
    db_message = Message(
        id=item.id,
        conversation_id=item.conversation_id,
        role=item.role,
        content=item.content,
        created_at=item.created_at,
    )

    exists = session.exec(
        select(Message)
        .where(Message.id == item.id)
    ).first()

    if exists:
        return exists

    session.add(db_message)
    session.commit()
    session.refresh(db_message)
    return db_message

def get_message(item_id: UUID, session: Session):
    return msg_or_404(item_id, session)

def create_conversation(item: Conversation, session: Session):
    db_conv = Conversation(
        id=item.id,
        phone=item.phone,
    )
    session.add(db_conv)
    session.commit()
    session.refresh(db_conv)
    return db_conv

def get_last_messages(conversation_id, session, limit=40):
    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())    #1785852644????1785852550?????1785852505
        .limit(limit)
    )
    messages = session.exec(statement).all()
    # Eski → Yeni sıralaması
    return list(reversed(messages))

def get_convs(session: Session):
    return session.exec(select(Conversation)).all()