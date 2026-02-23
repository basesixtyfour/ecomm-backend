from datetime import datetime
from enum import Enum

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
    func,
    Enum as SQLEnum,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class ChatRoomStatus(str, Enum):
    active = "active"
    closed = "closed"


class MessageSenderType(str, Enum):
    user = "user"
    agent = "agent"
    system = "system"


class ChatRoom(Base):
    __tablename__ = "chat_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("auth_user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    agent_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("auth_user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[ChatRoomStatus] = mapped_column(
        SQLEnum(ChatRoomStatus, name="chat_room_status"),
        nullable=False,
        default=ChatRoomStatus.active,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )

    def __repr__(self) -> str:
        return (
            f"<ChatRoom id={self.id} user_id={self.user_id} "
            f"agent_id={self.agent_id} status={self.status}>"
        )
