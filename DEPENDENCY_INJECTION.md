# Kyrios Bot - 依存性注入 (DI) システム

## DI システム概要

KyriosはPython用の高機能DIライブラリ`dependency-injector`を使用して、依存関係の管理を行っています。

## DIコンテナ構成

### メインコンテナ (`di/container.py`)

```python
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # 設定プロバイダー
    config = providers.Singleton(Settings)

    # データベースプロバイダー
    database_manager = providers.Singleton(
        DatabaseManager,
        database_path=config.provided.database_path
    )

    # イベントバスプロバイダー
    event_bus = providers.Singleton(EventBus)

    # ファクトリープロバイダー
    cog_factory = providers.Singleton(KyriosCogFactory)
```

## プロバイダーの種類

### 1. Singleton Provider
**用途**: アプリケーション全体で1つのインスタンスを共有

```python
# 設定管理 - 全体で共有される単一インスタンス
config = providers.Singleton(Settings)

# データベース管理 - コネクションプールを共有
database_manager = providers.Singleton(DatabaseManager)
```

### 2. Factory Provider
**用途**: 呼び出しごとに新しいインスタンスを作成

```python
# 一時的なオブジェクトの作成
temp_object = providers.Factory(TemporaryClass)
```

### 3. Resource Provider
**用途**: ライフサイクル管理が必要なリソース

```python
# セットアップと切断が必要なリソース
wired_event_bus = providers.Resource(
    _setup_event_bus,
    event_bus=event_bus,
    logging_observer=logging_observer,
    metrics_observer=metrics_observer
)
```

## 依存関係注入の使用方法

### 1. 関数への注入

```python
from di import ConfigDep, DatabaseDep, EventBusDep
from dependency_injector.wiring import inject

@inject
async def some_function(
    config=ConfigDep,
    database=DatabaseDep,
    event_bus=EventBusDep
):
    # 自動的に依存関係が注入される
    print(f"Bot token: {config.bot_token}")
    tickets = await database.get_open_tickets(guild_id)
    await event_bus.emit_event("function_called", {})
```

### 2. クラスコンストラクターへの注入

```python
class TicketService:
    @inject
    def __init__(
        self,
        database=DatabaseDep,
        event_bus=EventBusDep
    ):
        self.database = database
        self.event_bus = event_bus

    async def create_ticket(self, guild_id: int, user_id: int):
        ticket = await self.database.create_ticket(guild_id, user_id)
        await self.event_bus.emit_event("ticket_created", {
            "ticket_id": ticket.id
        })
```

### 3. Cogへの注入

```python
from discord.ext import commands

class TicketsCog(commands.Cog):
    @inject
    def __init__(
        self,
        bot,
        database=DatabaseDep,
        event_bus=EventBusDep
    ):
        self.bot = bot
        self.database = database
        self.event_bus = event_bus

    @app_commands.command()
    async def create_ticket(self, interaction):
        # 注入された依存関係を使用
        await self.database.create_ticket(...)
```

## 利用可能な依存関係エイリアス

### 設定関連
```python
from di import ConfigDep

@inject
def function(config=ConfigDep):
    token = config.bot_token
    prefix = config.bot_prefix
    db_path = config.database_path
```

### データベース関連
```python
from di import DatabaseDep

@inject
async def function(database=DatabaseDep):
    tickets = await database.get_open_tickets(guild_id)
    await database.create_log(guild_id, LogType.SYSTEM_EVENT, "Test")
```

### イベントシステム関連
```python
from di import EventBusDep

@inject
async def function(event_bus=EventBusDep):
    await event_bus.emit_event("custom_event", {"data": "value"})
    history = event_bus.get_event_history()
```

### ファクトリー関連
```python
from di import CogFactoryDep

@inject
def function(factory=CogFactoryDep):
    factory.register_cog("custom", CustomCog)
    cog = factory.create_cog("custom", bot=bot)
```

## コンテナの初期化とワイヤリング

### アプリケーション起動時

```python
# bot.py
async def main():
    # DIコンテナを初期化
    container.init_resources()

    # ワイヤリング（依存関係を解決）
    container.wire(modules=[
        __name__,
        "cogs.admin",
        "cogs.tickets",
        "cogs.logging"
    ])

    try:
        bot = KyriosBot()  # DIが自動的に動作
        await bot.start(bot.settings.bot_token)
    finally:
        container.shutdown_resources()
```

## テストでのDIオーバーライド

### モックオブジェクトの注入

```python
import pytest
from unittest.mock import AsyncMock
from di import container

@pytest.fixture
def mock_database():
    mock = AsyncMock()
    mock.create_ticket.return_value = MockTicket(id=1)
    return mock

@pytest.fixture
def override_container(mock_database):
    # テスト用にコンテナをオーバーライド
    with container.database_manager.override(mock_database):
        yield

def test_ticket_creation(override_container):
    # テスト実行時は mock_database が注入される
    service = TicketService()
    # テストロジック
```

### テスト用設定の注入

```python
class TestSettings(Settings):
    def __init__(self):
        super().__init__()
        self.bot_token = "test_token"
        self.database_path = ":memory:"

@pytest.fixture
def test_container():
    with container.config.override(TestSettings()):
        yield
```

## カスタムプロバイダーの追加

### 新しいサービスの追加

```python
# di/container.py に追加
class Container(containers.DeclarativeContainer):
    # 既存のプロバイダー...

    # カスタムサービス
    notification_service = providers.Singleton(
        NotificationService,
        config=config,
        database=database_manager
    )

    # APIクライアント
    external_api = providers.Singleton(
        ExternalAPIClient,
        api_key=config.provided.api_key
    )

# di/__init__.py にエイリアス追加
NotificationDep = Provide[Container.notification_service]
ExternalAPIDep = Provide[Container.external_api]
```

## リソースの自動管理

### リソースプロバイダーの実装

```python
def _setup_event_bus(
    event_bus: EventBus,
    logging_observer: LoggingObserver,
    metrics_observer: MetricsObserver
) -> EventBus:
    """イベントバスのセットアップ"""
    event_bus.attach(logging_observer)
    event_bus.attach(metrics_observer)

    # リソース初期化ログ
    logging.info("Event bus initialized with observers")

    return event_bus

def _teardown_event_bus(event_bus: EventBus) -> None:
    """イベントバスのクリーンアップ"""
    event_bus.clear_event_history()
    logging.info("Event bus cleaned up")

# コンテナ内でリソース定義
wired_event_bus = providers.Resource(
    _setup_event_bus,
    event_bus=event_bus,
    logging_observer=logging_observer,
    metrics_observer=metrics_observer,
    # クリーンアップ関数
    shutdown=_teardown_event_bus
)
```

## よくある問題と解決方法

### 1. 循環依存
**問題**: AがBに依存し、BがAに依存する

**解決**:
```python
# Factory Patternを使用して遅延初期化
service_a = providers.Factory(ServiceA)
service_b = providers.Factory(ServiceB, service_a=service_a)
```

### 2. ワイヤリングエラー
**問題**: `DependencyError: Dependency is not defined`

**解決**:
```python
# bot.py でモジュールの確実なワイヤリング
container.wire(modules=[
    __name__,
    "cogs.admin",     # 実際のモジュール名を指定
    "cogs.tickets",
    "cogs.logging"
])
```

### 3. 型エラー
**問題**: MyPyで型チェックエラー

**解決**:
```python
# 型ヒントの明示
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from database.manager import DatabaseManager

@inject
def function(database: "DatabaseManager" = DatabaseDep):
    # 型安全な実装
```

## パフォーマンス考慮事項

### Singletonの適切な使用
- **重いオブジェクト**: データベース接続、設定オブジェクト
- **状態を持つオブジェクト**: イベントバス、メトリクスコレクター

### Factoryの適切な使用
- **軽量オブジェクト**: 一時的なサービスクラス
- **状態を持たないオブジェクト**: ユーティリティクラス

この設計により、Kyriosは柔軟で保守しやすい依存関係管理を実現しています。