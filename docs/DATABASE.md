# Kyrios Bot - データベースドキュメント

## データベース設計概要

KyriosはSQLite + SQLModel (FastAPI風) を使用して、型安全で効率的なデータ管理を行っています。

## データベース構成

### 技術スタック
- **aiosqlite**: 非同期SQLiteドライバーによる真の非ブロッキング操作
- **SQLModel**: Pydanticベースの型安全ORM
- **SQLAlchemy[asyncio]**: 非同期DB操作とマイグレーション

## データモデル設計

### 1. Ticket モデル

```python
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Optional

class Ticket(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int                           # Discord サーバーID
    channel_id: int                         # チケット専用チャンネルID
    user_id: int                           # チケット作成ユーザーID
    assigned_to: Optional[int] = None       # 担当者のユーザーID
    category: TicketCategory                # チケットのカテゴリ
    priority: TicketPriority = TicketPriority.MEDIUM
    status: TicketStatus = TicketStatus.OPEN
    created_at: datetime = Field(default_factory=datetime.now)
    closed_at: Optional[datetime] = None
    title: str                             # チケットのタイトル
    description: Optional[str] = None       # 詳細説明
```

**Enum定義:**
```python
class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    CLOSED = "closed"
    ARCHIVED = "archived"

class TicketCategory(str, Enum):
    TECHNICAL = "technical"      # 技術的問題
    MODERATION = "moderation"    # モデレーション報告
    GENERAL = "general"          # 一般的な質問
    OTHER = "other"             # その他

class TicketPriority(int, Enum):
    LOW = 1      # 低優先度
    MEDIUM = 2   # 中優先度
    HIGH = 3     # 高優先度
    URGENT = 4   # 緊急
```

### 2. Log モデル

```python
class Log(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int                          # Discord サーバーID
    log_type: LogType                      # ログの種類
    user_id: Optional[int] = None          # 対象ユーザーID
    moderator_id: Optional[int] = None     # 実行者ID（モデレーション用）
    channel_id: Optional[int] = None       # 対象チャンネルID
    action: str                           # 実行されたアクション
    details: Optional[str] = None          # 詳細情報（JSON文字列）
    timestamp: datetime = Field(default_factory=datetime.now)
```

**LogType定義:**
```python
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

    # ロール関連
    ROLE_ADD = "role_add"
    ROLE_REMOVE = "role_remove"

    # チャンネル関連
    CHANNEL_CREATE = "channel_create"
    CHANNEL_DELETE = "channel_delete"

    # システム関連
    SYSTEM_EVENT = "system_event"
```

### 3. GuildSettings モデル

```python
class GuildSettings(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int = Field(unique=True)      # Discord サーバーID（ユニーク）
    log_channel_id: Optional[int] = None    # ログ出力チャンネルID
    ticket_category_id: Optional[int] = None # チケットカテゴリID
    ticket_archive_category_id: Optional[int] = None # アーカイブカテゴリID
    auto_role_id: Optional[int] = None      # 自動付与ロールID
    prefix: str = "!"                       # コマンドプレフィックス
    features_enabled: str = "tickets,logger" # 有効機能（CSV形式）
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

### 4. TicketMessage モデル

```python
class TicketMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ticket_id: int                          # 関連するチケットID
    user_id: int                           # メッセージ送信者ID
    message_id: int                        # DiscordメッセージID
    content: str                           # メッセージ内容
    timestamp: datetime = Field(default_factory=datetime.now)
    is_system_message: bool = False        # システムメッセージフラグ
```

### 5. AvatarHistory モデル

```python
class AvatarHistory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int                           # Discord ユーザーID
    guild_id: Optional[int] = None          # サーバーID（None=グローバル）
    history_type: AvatarHistoryType        # 変更タイプ
    old_avatar_url: Optional[str] = None    # 変更前URL
    new_avatar_url: Optional[str] = None    # 変更後URL
    dominant_color: Optional[str] = None    # 主要色（16進）
    image_format: Optional[str] = None      # 画像形式
    image_size: Optional[int] = None        # ファイルサイズ
    timestamp: datetime = Field(default_factory=datetime.now)
```

**AvatarHistoryType定義:**
```python
class AvatarHistoryType(str, Enum):
    AVATAR_CHANGE = "avatar_change"        # アバター変更
    BANNER_CHANGE = "banner_change"        # バナー変更
    SERVER_AVATAR_CHANGE = "server_avatar_change"  # サーバー専用アバター変更
```

### 6. UserAvatarStats モデル

```python
class UserAvatarStats(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(unique=True)       # Discord ユーザーID（ユニーク）
    total_avatar_changes: int = 0           # アバター変更回数
    total_banner_changes: int = 0           # バナー変更回数
    first_seen: datetime = Field(default_factory=datetime.now)
    last_avatar_change: Optional[datetime] = None
    last_banner_change: Optional[datetime] = None
    most_used_format: Optional[str] = None  # よく使う画像形式
    average_change_frequency: Optional[float] = None  # 平均変更頻度（日）
```

### 7. 音楽システムモデル

#### Track モデル
```python
class Track(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int                          # Discord サーバーID
    title: str                             # 楽曲タイトル
    artist: str                            # アーティスト名
    url: str                              # 楽曲URL
    source: MusicSource = MusicSource.YOUTUBE  # 音楽ソース
    duration: int                          # 再生時間（秒）
    thumbnail_url: Optional[str] = None     # サムネイルURL
    requested_by: int                      # リクエストユーザーID
    created_at: datetime = Field(default_factory=datetime.now)
```

#### Queue モデル
```python
class Queue(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int                          # Discord サーバーID
    track_id: int                          # 楽曲ID（Track外部キー）
    position: int                          # キュー内位置
    added_by: int                          # 追加者ユーザーID
    created_at: datetime = Field(default_factory=datetime.now)
```

#### MusicSession モデル
```python
class MusicSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int = Field(unique=True)      # Discord サーバーID（ユニーク）
    voice_channel_id: int                   # ボイスチャンネルID
    text_channel_id: int                    # テキストチャンネルID
    current_track_id: Optional[int] = None  # 現在再生中楽曲ID
    is_paused: bool = False                # 一時停止状態
    loop_mode: LoopMode = LoopMode.NONE    # ループモード
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
```

**音楽システム Enum定義:**
```python
class MusicSource(str, Enum):
    YOUTUBE = "youtube"                     # YouTube
    SPOTIFY = "spotify"                     # Spotify（未対応）
    SOUNDCLOUD = "soundcloud"               # SoundCloud（未対応）
    URL = "url"                            # 直接URL

class LoopMode(str, Enum):
    NONE = "none"                          # リピートなし
    TRACK = "track"                        # 楽曲リピート
    QUEUE = "queue"                        # キューリピート
```

## データベースマネージャー

### DatabaseManager クラス

```python
from database.manager import DatabaseManager

# 初期化（非同期）
db_manager = DatabaseManager("kyrios.db")
await db_manager.initialize()

# 非同期トランザクション（推奨）
async with db_manager.transaction() as session:
    # 非同期データベース操作
    result = await session.execute(statement)

# 非推奨：get_session()は下位互換性のためのみ残存
# async with db_manager.async_session() as session:
#     # 直接セッション使用
#     pass
```

### 主要メソッド

#### チケット操作
```python
# チケット作成
ticket = await db_manager.create_ticket(
    guild_id=123456789,
    channel_id=987654321,
    user_id=555666777,
    title="サーバーエラーについて",
    description="サーバーにログインできません"
)

# チケット取得
ticket = await db_manager.get_ticket(ticket_id=1)

# ユーザーのチケット一覧
tickets = await db_manager.get_tickets_by_user(
    guild_id=123456789,
    user_id=555666777
)

# オープンチケット一覧
open_tickets = await db_manager.get_open_tickets(guild_id=123456789)

# チケット更新
updated_ticket = await db_manager.update_ticket(
    ticket_id=1,
    assigned_to=999888777,
    priority=TicketPriority.HIGH,
    status=TicketStatus.IN_PROGRESS
)

# チケットクローズ
closed_ticket = await db_manager.close_ticket(ticket_id=1)
```

#### ログ操作
```python
# ログ作成
log_entry = await db_manager.create_log(
    guild_id=123456789,
    log_type=LogType.MESSAGE_DELETE,
    action="Message Deleted",
    user_id=555666777,
    channel_id=987654321,
    details='{"content": "Hello World", "attachments": []}'
)

# ログ取得
logs = await db_manager.get_logs(
    guild_id=123456789,
    log_type=LogType.MESSAGE_DELETE,
    limit=50
)
```

#### サーバー設定操作
```python
# 設定取得
settings = await db_manager.get_guild_settings(guild_id=123456789)

# 設定作成・更新
settings = await db_manager.create_or_update_guild_settings(
    guild_id=123456789,
    log_channel_id=111222333,
    ticket_category_id=444555666,
    features_enabled="tickets,logger,music"
)
```

#### 音楽システム操作
```python
# 楽曲作成
track = await db_manager.create_track(
    guild_id=123456789,
    title="Never Gonna Give You Up",
    artist="Rick Astley",
    url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    duration=212,
    thumbnail_url="https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg",
    requested_by=555666777,
    source=MusicSource.YOUTUBE
)

# キューに追加
queue_item = await db_manager.add_to_queue(
    guild_id=123456789,
    track_id=track.id,
    added_by=555666777
)

# 音楽セッション作成・更新
session = await db_manager.create_session(
    guild_id=123456789,
    voice_channel_id=888999000,
    text_channel_id=111222333
)

# 現在再生中の楽曲を設定
await db_manager.update_session_current_track(
    guild_id=123456789,
    track_id=track.id
)

# キューから次の楽曲を取得
next_item = await db_manager.get_next_in_queue(guild_id=123456789)

# キューをクリア
cleared_count = await db_manager.clear_queue(guild_id=123456789)

# セッション削除
await db_manager.delete_session(guild_id=123456789)
```

#### アバターシステム操作
```python
# アバター履歴記録
history = await db_manager.record_avatar_change(
    user_id=555666777,
    guild_id=123456789,  # None でグローバル
    history_type=AvatarHistoryType.AVATAR_CHANGE,
    old_avatar_url="https://old-avatar-url.com",
    new_avatar_url="https://new-avatar-url.com",
    dominant_color="#ff0000",
    image_format="png",
    image_size=45231
)

# ユーザー統計取得
stats = await db_manager.get_user_avatar_stats(user_id=555666777)

# アバター履歴取得
history_list = await db_manager.get_avatar_history(
    user_id=555666777,
    limit=10
)
```

## データベーススキーマ

### ER図（簡略版）
```
GuildSettings ||--o{ Ticket : has
GuildSettings ||--o{ Log : has
GuildSettings ||--o{ Track : has
GuildSettings ||--|| MusicSession : has
Ticket ||--o{ TicketMessage : contains
Track ||--o{ Queue : queued
UserAvatarStats ||--o{ AvatarHistory : has

GuildSettings:
- guild_id (PK, UNIQUE)
- log_channel_id
- ticket_category_id
- features_enabled

Ticket:
- id (PK)
- guild_id (FK)
- channel_id, user_id
- status, priority, category

Log:
- id (PK)
- guild_id (FK)
- log_type, action, details

Track:
- id (PK)
- guild_id (FK)
- title, artist, url
- source, duration

Queue:
- id (PK)
- guild_id (FK)
- track_id (FK)
- position, added_by

MusicSession:
- guild_id (PK, UNIQUE, FK)
- voice_channel_id, text_channel_id
- current_track_id, loop_mode

AvatarHistory:
- id (PK)
- user_id, guild_id
- history_type, urls, metadata

UserAvatarStats:
- user_id (PK, UNIQUE)
- change_counts, timestamps
```

### インデックス戦略
```sql
-- 既存インデックス
CREATE INDEX idx_ticket_guild_status ON tickets(guild_id, status);
CREATE INDEX idx_ticket_user ON tickets(guild_id, user_id);
CREATE INDEX idx_log_guild_type ON logs(guild_id, log_type);
CREATE INDEX idx_log_timestamp ON logs(timestamp);
CREATE INDEX idx_guild_settings_guild ON guild_settings(guild_id);

-- 音楽システム用インデックス
CREATE INDEX idx_track_guild ON tracks(guild_id);
CREATE INDEX idx_track_source ON tracks(source);
CREATE INDEX idx_queue_guild_position ON queues(guild_id, position);
CREATE INDEX idx_queue_track ON queues(track_id);
CREATE INDEX idx_music_session_guild ON music_sessions(guild_id);

-- アバターシステム用インデックス
CREATE INDEX idx_avatar_history_user ON avatar_histories(user_id);
CREATE INDEX idx_avatar_history_type ON avatar_histories(history_type);
CREATE INDEX idx_avatar_history_timestamp ON avatar_histories(timestamp);
CREATE INDEX idx_avatar_stats_user ON user_avatar_stats(user_id);
```

## データベース操作パターン

### 1. 基本的なCRUD操作

```python
from database.models import Ticket, TicketStatus
from database.manager import DatabaseManager

class TicketService:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    async def create_ticket(self, guild_id: int, user_id: int, title: str) -> Ticket:
        return await self.db.create_ticket(
            guild_id=guild_id,
            channel_id=0,  # 後で設定
            user_id=user_id,
            title=title
        )

    async def assign_ticket(self, ticket_id: int, assignee_id: int) -> Optional[Ticket]:
        return await self.db.update_ticket(ticket_id, assigned_to=assignee_id)

    async def get_user_tickets(self, guild_id: int, user_id: int) -> List[Ticket]:
        return await self.db.get_tickets_by_user(guild_id, user_id)
```

### 2. 複合クエリ操作

```python
from sqlmodel import select, and_, or_

async def get_priority_tickets(self, guild_id: int) -> List[Ticket]:
    """高優先度のオープンチケットを取得"""
    async with self.db.async_session() as session:
        statement = select(Ticket).where(
            and_(
                Ticket.guild_id == guild_id,
                Ticket.status == TicketStatus.OPEN,
                Ticket.priority >= TicketPriority.HIGH
            )
        ).order_by(Ticket.priority.desc(), Ticket.created_at)

        result = await session.execute(statement)
        return list(result.scalars().all())

async def get_recent_logs(self, guild_id: int, hours: int = 24) -> List[Log]:
    """指定時間内のログを取得"""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    async with self.db.async_session() as session:
        statement = select(Log).where(
            and_(
                Log.guild_id == guild_id,
                Log.timestamp >= cutoff_time
            )
        ).order_by(Log.timestamp.desc())

        result = await session.execute(statement)
        return list(result.scalars().all())
```

### 3. 統計・集計クエリ

```python
from sqlalchemy import func

async def get_ticket_statistics(self, guild_id: int) -> dict:
    """チケット統計を取得"""
    async with self.db.async_session() as session:
        # ステータス別カウント
        status_result = await session.execute(
            select(Ticket.status, func.count(Ticket.id))
            .where(Ticket.guild_id == guild_id)
            .group_by(Ticket.status)
        )
        status_counts = status_result.all()

        # 優先度別カウント
        priority_result = await session.execute(
            select(Ticket.priority, func.count(Ticket.id))
            .where(Ticket.guild_id == guild_id)
            .group_by(Ticket.priority)
        )
        priority_counts = priority_result.all()

        return {
            "status_distribution": dict(status_counts),
            "priority_distribution": dict(priority_counts),
            "total_tickets": sum(count for _, count in status_counts)
        }
```

## テスト用データベース

### インメモリデータベース

```python
# テスト用の設定
test_db = DatabaseManager(":memory:")

@pytest.fixture
async def sample_ticket():
    """テスト用サンプルチケット"""
    return await test_db.create_ticket(
        guild_id=123456789,
        channel_id=987654321,
        user_id=555666777,
        title="Test Ticket"
    )

@pytest.mark.asyncio
async def test_ticket_creation(sample_ticket):
    assert sample_ticket.id is not None
    assert sample_ticket.title == "Test Ticket"
    assert sample_ticket.status == TicketStatus.OPEN
```

### モックデータ生成

```python
import factory
from factory import Faker

class TicketFactory(factory.Factory):
    class Meta:
        model = Ticket

    guild_id = 123456789
    channel_id = Faker('random_int', min=100000000, max=999999999)
    user_id = Faker('random_int', min=100000000, max=999999999)
    title = Faker('sentence', nb_words=4)
    description = Faker('text', max_nb_chars=200)
    category = Faker('random_element', elements=list(TicketCategory))
    priority = Faker('random_element', elements=list(TicketPriority))

# 使用例
test_tickets = TicketFactory.create_batch(10)
```

## パフォーマンス最適化

### 1. バッチ操作

```python
async def create_multiple_logs(self, log_data_list: List[dict]) -> List[Log]:
    """複数ログの効率的な作成"""
    logs = [Log(**data) for data in log_data_list]

    async with self.db.async_session() as session:
        session.add_all(logs)
        await session.commit()

        for log in logs:
            await session.refresh(log)

        return logs
```

### 2. ページネーション

```python
async def get_logs_paginated(
    self,
    guild_id: int,
    page: int = 1,
    per_page: int = 50
) -> Tuple[List[Log], int]:
    """ページネーション付きログ取得"""
    offset = (page - 1) * per_page

    async with self.db.async_session() as session:
        # データ取得
        statement = (
            select(Log)
            .where(Log.guild_id == guild_id)
            .order_by(Log.timestamp.desc())
            .offset(offset)
            .limit(per_page)
        )
        result = await session.execute(statement)
        logs = list(result.scalars().all())

        # 総件数取得
        count_statement = select(func.count(Log.id)).where(Log.guild_id == guild_id)
        count_result = await session.execute(count_statement)
        total_count = count_result.scalar_one()

        return logs, total_count
```

### 3. 接続管理

```python
# 長時間実行される処理での適切な接続管理
async def long_running_process(self):
    for batch in data_batches:
        async with self.db.async_session() as session:
            # バッチ処理
            await process_batch(session, batch)
            await session.commit()
        # セッション自動クローズ
```

## メンテナンス操作

### データベースバックアップ
```python
import shutil
from pathlib import Path

async def backup_database(self) -> Path:
    """データベースのバックアップ作成"""
    backup_path = Path(f"backup_kyrios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
    shutil.copy2(self.database_path, backup_path)
    return backup_path
```

### 古いデータのクリーンアップ
```python
async def cleanup_old_logs(self, days: int = 30) -> int:
    """古いログエントリの削除"""
    cutoff_date = datetime.now() - timedelta(days=days)

    async with self.db.async_session() as session:
        statement = select(Log).where(Log.timestamp < cutoff_date)
        result = await session.execute(statement)
        old_logs = list(result.scalars().all())

        for log in old_logs:
            await session.delete(log)

        await session.commit()
        return len(old_logs)
```

## トランザクション管理

### データ整合性の確保

Kyriosでは、複数のテーブルにまたがる操作でデータ整合性を保証するため、適切なトランザクション管理を実装しています。

#### 問題のあるパターン（非推奨）
```python
# ❌ トランザクションが分離されている（データ不整合のリスク）
async def bad_record_avatar_change(self, user_id: int):
    # 1. 履歴を保存
    with self.get_session() as session:
        history = AvatarHistory(user_id=user_id, ...)
        session.add(history)
        session.commit()  # ✅ 履歴は保存完了

    # 2. 統計を更新（別のトランザクション）
    with self.get_session() as session:
        stats = session.get(UserAvatarStats, user_id)
        stats.total_changes += 1
        session.commit()  # 💥 ここでエラーが発生すると統計だけ失敗
```

#### 正しいパターン（推奨）
```python
# ✅ 単一トランザクションでアトミック操作
async def record_avatar_change(self, user_id: int, ...):
    async with self.transaction() as session:
        # 1. 履歴を作成
        history = AvatarHistory(user_id=user_id, ...)
        session.add(history)
        session.flush()  # IDを取得（コミットはしない）

        # 2. 統計を同じトランザクション内で更新
        self._update_user_avatar_stats_sync(user_id, history_type, session)

        # トランザクション終了時に自動コミット
        # エラーが発生した場合は自動ロールバック
```

### トランザクション管理の基本パターン

#### 1. シンプルなトランザクション
```python
async with self.transaction() as session:
    # 複数の操作を実行
    user = User(name="test")
    session.add(user)

    log = Log(user_id=user.id, action="created")
    session.add(log)

    # context manager終了時に自動コミット
```

#### 2. 複雑な操作の管理
```python
async def complex_ticket_operation(self, ticket_data):
    operations = [
        lambda session: self._create_ticket_sync(session, ticket_data),
        lambda session: self._create_initial_message_sync(session, ticket_data),
        lambda session: self._update_guild_stats_sync(session, ticket_data.guild_id),
        lambda session: self._create_audit_log_sync(session, ticket_data)
    ]

    results = await self.execute_in_transaction(operations)
    return results[0]  # チケット情報を返す
```

#### 3. エラーハンドリング
```python
async def safe_operation(self, data):
    try:
        async with self.transaction() as session:
            # 操作実行
            result = perform_complex_operation(session, data)
            return result
    except IntegrityError as e:
        self.logger.error(f"Data integrity violation: {e}")
        raise ValueError("操作に失敗しました：データの整合性エラー")
    except Exception as e:
        self.logger.error(f"Transaction failed: {e}")
        raise
```

### ベストプラクティス

#### 1. 一貫性が必要な操作は必ずトランザクション内で実行
```python
# ✅ 関連するデータの更新は同じトランザクション内
async with self.transaction() as session:
    ticket.status = TicketStatus.CLOSED
    ticket.closed_at = datetime.now()

    log = Log(action="ticket_closed", ticket_id=ticket.id)
    session.add(log)
```

#### 2. 長時間実行される処理はバッチ化
```python
async def process_large_dataset(self, items):
    batch_size = 100
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]

        async with self.transaction() as session:
            for item in batch:
                process_item(session, item)
        # 各バッチ後にトランザクション完了
```

#### 3. 読み取り専用操作は通常のセッション使用
```python
# 読み取り専用はトランザクション不要
async def get_user_tickets(self, user_id: int):
    async with self.async_session() as session:
        result = await session.execute(select(Ticket).where(Ticket.user_id == user_id))
        return list(result.scalars().all())
```

このトランザクション管理により、Kyriosは高いデータ整合性と信頼性を確保しています。