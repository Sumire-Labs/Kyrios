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
    # メッセージ関連
    MESSAGE_DELETE = "message_delete"
    MESSAGE_EDIT = "message_edit"

    # メンバー関連
    MEMBER_JOIN = "member_join"
    MEMBER_LEAVE = "member_leave"
    MEMBER_BAN = "member_ban"
    MEMBER_UNBAN = "member_unban"
    MEMBER_KICK = "member_kick"
    MEMBER_TIMEOUT = "member_timeout"
    MEMBER_UPDATE = "member_update"

    # ロール関連
    ROLE_ADD = "role_add"
    ROLE_REMOVE = "role_remove"
    ROLE_CREATE = "role_create"
    ROLE_DELETE = "role_delete"
    ROLE_UPDATE = "role_update"

    # チャンネル関連
    CHANNEL_CREATE = "channel_create"
    CHANNEL_DELETE = "channel_delete"
    CHANNEL_UPDATE = "channel_update"

    # サーバー関連
    GUILD_UPDATE = "guild_update"
    GUILD_EMOJIS_UPDATE = "guild_emojis_update"
    GUILD_STICKERS_UPDATE = "guild_stickers_update"

    # WebSocket関連
    WEBSOCKET_CONNECT = "websocket_connect"
    WEBSOCKET_DISCONNECT = "websocket_disconnect"
    WEBSOCKET_RECONNECT = "websocket_reconnect"
    WEBSOCKET_ERROR = "websocket_error"

    # システム関連
    SYSTEM_EVENT = "system_event"
    BOT_READY = "bot_ready"
    BOT_DISCONNECT = "bot_disconnect"


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


# 音楽システム用モデル
class MusicSource(str, Enum):
    YOUTUBE = "youtube"
    SPOTIFY = "spotify"
    SOUNDCLOUD = "soundcloud"
    URL = "url"


class LoopMode(str, Enum):
    NONE = "none"
    TRACK = "track"
    QUEUE = "queue"


class Track(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int
    title: str
    artist: str
    url: str
    source: MusicSource = MusicSource.YOUTUBE
    duration: int  # 秒
    thumbnail_url: Optional[str] = None
    requested_by: int  # ユーザーID
    created_at: datetime = Field(default_factory=datetime.now)


class Queue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int
    track_id: int
    position: int
    added_by: int
    created_at: datetime = Field(default_factory=datetime.now)


class MusicSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int = Field(unique=True)
    voice_channel_id: int
    text_channel_id: int
    current_track_id: Optional[int] = None
    volume: int = 50
    is_paused: bool = False
    loop_mode: LoopMode = LoopMode.NONE
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)