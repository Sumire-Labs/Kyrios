from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field  # type: ignore
from enum import Enum


class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    ARCHIVED = "archived"


class TicketCategory(str, Enum):
    TECHNICAL = "technical"
    MODERATION = "moderation"
    GENERAL = "general"
    OTHER = "other"


class TicketPriority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


class LogType(str, Enum):
    MESSAGE_DELETE = "message_delete"
    MESSAGE_EDIT = "message_edit"
    MEMBER_JOIN = "member_join"
    MEMBER_LEAVE = "member_leave"
    MEMBER_BAN = "member_ban"
    MEMBER_UNBAN = "member_unban"
    MEMBER_KICK = "member_kick"
    MEMBER_TIMEOUT = "member_timeout"
    ROLE_ADD = "role_add"
    ROLE_REMOVE = "role_remove"
    CHANNEL_CREATE = "channel_create"
    CHANNEL_DELETE = "channel_delete"
    SYSTEM_EVENT = "system_event"


class Ticket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int
    channel_id: int
    user_id: int
    assigned_to: Optional[int] = None
    category: TicketCategory = TicketCategory.GENERAL
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    title: str
    description: Optional[str] = None


class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int
    log_type: LogType
    user_id: Optional[int] = None
    moderator_id: Optional[int] = None
    channel_id: Optional[int] = None
    action: str
    details: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class GuildSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int = Field(unique=True)
    log_channel_id: Optional[int] = None
    ticket_category_id: Optional[int] = None
    ticket_archive_category_id: Optional[int] = None
    auto_role_id: Optional[int] = None
    prefix: str = "!"
    features_enabled: str = "tickets,logger"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class TicketMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int
    user_id: int
    message_id: int
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    is_system_message: bool = False


class AvatarHistoryType(str, Enum):
    AVATAR_CHANGE = "avatar_change"
    BANNER_CHANGE = "banner_change"
    SERVER_AVATAR_CHANGE = "server_avatar_change"


class AvatarHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int
    guild_id: Optional[int] = None  # None for global avatar/banner
    history_type: AvatarHistoryType
    old_avatar_url: Optional[str] = None
    new_avatar_url: Optional[str] = None
    dominant_color: Optional[str] = None  # Hex color code
    image_format: Optional[str] = None  # png, jpg, gif, webp
    image_size: Optional[int] = None  # File size in bytes
    timestamp: datetime = Field(default_factory=datetime.now)


class UserAvatarStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(unique=True)
    total_avatar_changes: int = 0
    total_banner_changes: int = 0
    first_seen: datetime = Field(default_factory=datetime.now)
    last_avatar_change: Optional[datetime] = None
    last_banner_change: Optional[datetime] = None
    most_used_format: Optional[str] = None
    average_change_frequency: Optional[float] = None  # Days between changes