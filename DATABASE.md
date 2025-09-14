# Kyrios Bot - データベースドキュメント

## データベース設計概要

KyriosはSQLite + SQLModel (FastAPI風) を使用して、型安全で効率的なデータ管理を行っています。

## データベース構成

### 技術スタック
- **SQLite**: 軽量で高性能な埋め込みDB
- **SQLModel**: Pydanticベースの型安全ORM
- **SQLAlchemy**: 低レベルDB操作とマイグレーション

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

## データベースマネージャー

### DatabaseManager クラス

```python
from database.manager import DatabaseManager

# 初期化
db_manager = DatabaseManager("kyrios.db")

# セッション取得
with db_manager.get_session() as session:
    # データベース操作
    pass
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
    features_enabled="tickets,logger,auto_mod"
)
```

## データベーススキーマ

### ER図（簡略版）
```
GuildSettings ||--o{ Ticket : has
GuildSettings ||--o{ Log : has
Ticket ||--o{ TicketMessage : contains

GuildSettings:
- guild_id (PK, UNIQUE)
- log_channel_id
- ticket_category_id
- features_enabled

Ticket:
- id (PK)
- guild_id (FK)
- channel_id
- user_id
- status, priority, category

Log:
- id (PK)
- guild_id (FK)
- log_type
- action, details

TicketMessage:
- id (PK)
- ticket_id (FK)
- user_id
- content
```

### インデックス戦略
```sql
-- パフォーマンス向上のためのインデックス
CREATE INDEX idx_ticket_guild_status ON tickets(guild_id, status);
CREATE INDEX idx_ticket_user ON tickets(guild_id, user_id);
CREATE INDEX idx_log_guild_type ON logs(guild_id, log_type);
CREATE INDEX idx_log_timestamp ON logs(timestamp);
CREATE INDEX idx_guild_settings_guild ON guild_settings(guild_id);
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
    with self.db.get_session() as session:
        statement = select(Ticket).where(
            and_(
                Ticket.guild_id == guild_id,
                Ticket.status == TicketStatus.OPEN,
                Ticket.priority >= TicketPriority.HIGH
            )
        ).order_by(Ticket.priority.desc(), Ticket.created_at)

        return list(session.exec(statement))

async def get_recent_logs(self, guild_id: int, hours: int = 24) -> List[Log]:
    """指定時間内のログを取得"""
    cutoff_time = datetime.now() - timedelta(hours=hours)

    with self.db.get_session() as session:
        statement = select(Log).where(
            and_(
                Log.guild_id == guild_id,
                Log.timestamp >= cutoff_time
            )
        ).order_by(Log.timestamp.desc())

        return list(session.exec(statement))
```

### 3. 統計・集計クエリ

```python
from sqlalchemy import func

async def get_ticket_statistics(self, guild_id: int) -> dict:
    """チケット統計を取得"""
    with self.db.get_session() as session:
        # ステータス別カウント
        status_counts = session.exec(
            select(Ticket.status, func.count(Ticket.id))
            .where(Ticket.guild_id == guild_id)
            .group_by(Ticket.status)
        ).all()

        # 優先度別カウント
        priority_counts = session.exec(
            select(Ticket.priority, func.count(Ticket.id))
            .where(Ticket.guild_id == guild_id)
            .group_by(Ticket.priority)
        ).all()

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

    with self.db.get_session() as session:
        session.add_all(logs)
        session.commit()

        for log in logs:
            session.refresh(log)

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

    with self.db.get_session() as session:
        # データ取得
        statement = (
            select(Log)
            .where(Log.guild_id == guild_id)
            .order_by(Log.timestamp.desc())
            .offset(offset)
            .limit(per_page)
        )
        logs = list(session.exec(statement))

        # 総件数取得
        count_statement = select(func.count(Log.id)).where(Log.guild_id == guild_id)
        total_count = session.exec(count_statement).one()

        return logs, total_count
```

### 3. 接続管理

```python
# 長時間実行される処理での適切な接続管理
async def long_running_process(self):
    for batch in data_batches:
        with self.db.get_session() as session:
            # バッチ処理
            process_batch(session, batch)
            session.commit()
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

    with self.db.get_session() as session:
        statement = select(Log).where(Log.timestamp < cutoff_date)
        old_logs = list(session.exec(statement))

        for log in old_logs:
            session.delete(log)

        session.commit()
        return len(old_logs)
```

このデータベース設計により、Kyriosは高性能で拡張性のあるデータ管理を実現しています。