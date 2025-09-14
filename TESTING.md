# Kyrios Bot - テストドキュメント

## テスト戦略概要

Kyriosは包括的なテストカバレッジを提供し、高品質で信頼性の高いコードベースを維持しています。

## テストの種類

### 1. 単体テスト (Unit Tests)
- 個別の関数・メソッドの動作検証
- モック/スタブを使用した依存関係の分離
- 高速実行、頻繁な実行が可能

### 2. 統合テスト (Integration Tests)
- コンポーネント間の連携動作検証
- データベース・DIコンテナとの統合テスト
- より実環境に近い動作確認

### 3. エンドツーエンドテスト (E2E Tests)
- 実際のDiscord環境での動作確認
- 手動テスト + 自動化されたボット動作テスト

## テスト環境セットアップ

### 依存関係

```toml
# pyproject.toml
[tool.poetry.group.dev.dependencies]
pytest = "^8.3.4"
pytest-asyncio = "^0.24.0"
pytest-cov = "^6.0.0"
pytest-mock = "^3.12.0"
factory-boy = "^3.3.1"
```

### pytest設定

```toml
# pyproject.toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
asyncio_mode = "auto"
addopts = [
    "--cov=.",
    "--cov-report=html",
    "--cov-report=term-missing",
    "--cov-fail-under=80"
]
```

### テストディレクトリ構造

```
tests/
├── __init__.py
├── conftest.py                 # pytest設定・共通フィクスチャ
├── unit/
│   ├── test_models.py         # データベースモデルテスト
│   ├── test_database_manager.py
│   ├── test_patterns.py       # デザインパターンテスト
│   └── test_utils.py
├── integration/
│   ├── test_cogs.py           # Cogの統合テスト
│   ├── test_di_container.py   # DIコンテナテスト
│   └── test_workflows.py      # ワークフロー全体テスト
├── fixtures/
│   ├── sample_data.json       # テストデータ
│   └── mock_discord.py        # Discord APIモック
└── e2e/
    └── test_bot_commands.py    # ボットコマンドE2Eテスト
```

## 共通フィクスチャとユーティリティ

### conftest.py

```python
# tests/conftest.py
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from sqlmodel import create_engine, Session

from database.manager import DatabaseManager
from database.models import *
from di.container import Container


@pytest.fixture
def event_loop():
    """非同期テスト用のイベントループ"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def in_memory_db():
    """インメモリテストデータベース"""
    db_manager = DatabaseManager(":memory:")
    yield db_manager


@pytest.fixture
def mock_bot():
    """Discord.py Bot のモック"""
    bot = MagicMock()
    bot.user.id = 123456789
    bot.user.name = "TestBot"
    bot.latency = 0.05
    bot.guilds = []
    return bot


@pytest.fixture
def mock_guild():
    """Discord Guild のモック"""
    guild = MagicMock()
    guild.id = 987654321
    guild.name = "Test Guild"
    guild.member_count = 100
    return guild


@pytest.fixture
def mock_user():
    """Discord User のモック"""
    user = MagicMock()
    user.id = 555666777
    user.name = "TestUser"
    user.discriminator = "1234"
    user.mention = "<@555666777>"
    return user


@pytest.fixture
def mock_channel():
    """Discord Channel のモック"""
    channel = MagicMock()
    channel.id = 111222333
    channel.name = "test-channel"
    channel.mention = "<#111222333>"
    channel.send = AsyncMock()
    return channel


@pytest.fixture
def mock_interaction(mock_user, mock_guild, mock_channel):
    """Discord Interaction のモック"""
    interaction = AsyncMock()
    interaction.user = mock_user
    interaction.guild = mock_guild
    interaction.channel = mock_channel
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()
    return interaction


@pytest.fixture
def test_container():
    """テスト用DIコンテナ"""
    container = Container()
    # テスト用の設定でオーバーライド
    yield container
    container.reset_override()


@pytest.fixture
def sample_ticket_data():
    """サンプルチケットデータ"""
    return {
        "guild_id": 987654321,
        "channel_id": 111222333,
        "user_id": 555666777,
        "title": "Test Ticket",
        "description": "This is a test ticket"
    }
```

### テストデータファクトリー

```python
# tests/fixtures/factories.py
import factory
from factory import Faker
from datetime import datetime

from database.models import Ticket, Log, GuildSettings, TicketStatus, TicketCategory, LogType


class GuildSettingsFactory(factory.Factory):
    class Meta:
        model = GuildSettings

    guild_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    log_channel_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    ticket_category_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    prefix = "!"
    features_enabled = "tickets,logger"


class TicketFactory(factory.Factory):
    class Meta:
        model = Ticket

    guild_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    channel_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    user_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    title = Faker('sentence', nb_words=4)
    description = Faker('text', max_nb_chars=200)
    category = Faker('random_element', elements=list(TicketCategory))
    status = TicketStatus.OPEN
    created_at = Faker('date_time_between', start_date='-30d', end_date='now')


class LogFactory(factory.Factory):
    class Meta:
        model = Log

    guild_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    log_type = Faker('random_element', elements=list(LogType))
    user_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    channel_id = Faker('random_int', min=100000000000000000, max=999999999999999999)
    action = Faker('sentence', nb_words=3)
    details = Faker('json', data_columns={'key': 'word', 'value': 'word'})
    timestamp = Faker('date_time_between', start_date='-7d', end_date='now')
```

## 単体テストパターン

### データベースモデルテスト

```python
# tests/unit/test_models.py
import pytest
from datetime import datetime

from database.models import Ticket, TicketStatus, TicketCategory, TicketPriority
from tests.fixtures.factories import TicketFactory


class TestTicketModel:
    def test_ticket_creation(self):
        """チケット作成の基本テスト"""
        ticket = TicketFactory()

        assert ticket.guild_id is not None
        assert ticket.user_id is not None
        assert ticket.title is not None
        assert ticket.status == TicketStatus.OPEN
        assert ticket.created_at is not None

    def test_ticket_validation(self):
        """チケットバリデーションテスト"""
        with pytest.raises(ValueError):
            # タイトルが空の場合
            Ticket(
                guild_id=123,
                channel_id=456,
                user_id=789,
                title=""  # 無効な値
            )

    def test_ticket_status_transitions(self):
        """チケットステータス遷移テスト"""
        ticket = TicketFactory()

        # OPEN -> IN_PROGRESS
        ticket.status = TicketStatus.IN_PROGRESS
        assert ticket.status == TicketStatus.IN_PROGRESS

        # IN_PROGRESS -> CLOSED
        ticket.status = TicketStatus.CLOSED
        ticket.closed_at = datetime.now()
        assert ticket.status == TicketStatus.CLOSED
        assert ticket.closed_at is not None

    @pytest.mark.parametrize("category", list(TicketCategory))
    def test_ticket_categories(self, category):
        """全カテゴリのテスト"""
        ticket = TicketFactory(category=category)
        assert ticket.category == category

    @pytest.mark.parametrize("priority", list(TicketPriority))
    def test_ticket_priorities(self, priority):
        """全優先度のテスト"""
        ticket = TicketFactory(priority=priority)
        assert ticket.priority == priority
```

### データベースマネージャーテスト

```python
# tests/unit/test_database_manager.py
import pytest
from unittest.mock import patch, MagicMock

from database.manager import DatabaseManager
from database.models import Ticket, TicketStatus, LogType


class TestDatabaseManager:
    @pytest.fixture
    async def db_manager(self):
        """テスト用データベースマネージャー"""
        return DatabaseManager(":memory:")

    @pytest.mark.asyncio
    async def test_create_ticket(self, db_manager, sample_ticket_data):
        """チケット作成テスト"""
        ticket = await db_manager.create_ticket(**sample_ticket_data)

        assert ticket.id is not None
        assert ticket.guild_id == sample_ticket_data["guild_id"]
        assert ticket.user_id == sample_ticket_data["user_id"]
        assert ticket.title == sample_ticket_data["title"]
        assert ticket.status == TicketStatus.OPEN

    @pytest.mark.asyncio
    async def test_get_tickets_by_user(self, db_manager, sample_ticket_data):
        """ユーザー別チケット取得テスト"""
        # テストデータ作成
        ticket1 = await db_manager.create_ticket(**sample_ticket_data)
        ticket2 = await db_manager.create_ticket(
            **{**sample_ticket_data, "title": "Second Ticket"}
        )

        # 取得テスト
        tickets = await db_manager.get_tickets_by_user(
            sample_ticket_data["guild_id"],
            sample_ticket_data["user_id"]
        )

        assert len(tickets) == 2
        assert ticket1.id in [t.id for t in tickets]
        assert ticket2.id in [t.id for t in tickets]

    @pytest.mark.asyncio
    async def test_close_ticket(self, db_manager, sample_ticket_data):
        """チケットクローズテスト"""
        # チケット作成
        ticket = await db_manager.create_ticket(**sample_ticket_data)
        assert ticket.status == TicketStatus.OPEN
        assert ticket.closed_at is None

        # クローズ処理
        closed_ticket = await db_manager.close_ticket(ticket.id)

        assert closed_ticket.status == TicketStatus.CLOSED
        assert closed_ticket.closed_at is not None

    @pytest.mark.asyncio
    async def test_create_log(self, db_manager):
        """ログ作成テスト"""
        log_data = {
            "guild_id": 123456789,
            "log_type": LogType.MESSAGE_DELETE,
            "action": "Message Deleted",
            "user_id": 555666777,
            "channel_id": 111222333,
            "details": '{"content": "Test message"}'
        }

        log = await db_manager.create_log(**log_data)

        assert log.id is not None
        assert log.guild_id == log_data["guild_id"]
        assert log.log_type == log_data["log_type"]
        assert log.action == log_data["action"]

    @pytest.mark.asyncio
    async def test_database_error_handling(self, db_manager):
        """データベースエラーハンドリングテスト"""
        with pytest.raises(Exception):
            # 不正なデータでチケット作成を試行
            await db_manager.create_ticket(
                guild_id=None,  # 無効な値
                channel_id=123,
                user_id=456,
                title="Test"
            )
```

### デザインパターンテスト

```python
# tests/unit/test_patterns.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from patterns.command import Command, CommandInvoker
from patterns.observer import EventBus, Observer
from patterns.factory import KyriosCogFactory


class TestCommandPattern:
    class MockCommand(Command):
        def __init__(self, name: str, should_succeed: bool = True):
            super().__init__(name)
            self.should_succeed = should_succeed
            self.executed = False

        async def execute(self, *args, **kwargs):
            if not self.should_succeed:
                raise ValueError("Mock command failure")
            self.executed = True
            return "success"

        def can_undo(self) -> bool:
            return True

        async def undo(self) -> bool:
            self.executed = False
            return True

    @pytest.mark.asyncio
    async def test_command_execution(self):
        """コマンド実行テスト"""
        invoker = CommandInvoker()
        command = self.MockCommand("test_command")

        result = await invoker.execute_command(command)

        assert result == "success"
        assert command.executed
        assert len(invoker.history) == 1

    @pytest.mark.asyncio
    async def test_command_undo(self):
        """コマンド取り消しテスト"""
        invoker = CommandInvoker()
        command = self.MockCommand("test_command")

        # 実行
        await invoker.execute_command(command)
        assert command.executed

        # 取り消し
        success = await invoker.undo_last_command()
        assert success
        assert not command.executed
        assert len(invoker.history) == 0

    @pytest.mark.asyncio
    async def test_command_failure_handling(self):
        """コマンド失敗処理テスト"""
        invoker = CommandInvoker()
        command = self.MockCommand("failing_command", should_succeed=False)

        with pytest.raises(ValueError):
            await invoker.execute_command(command)

        assert len(invoker.history) == 0


class TestObserverPattern:
    class MockObserver(Observer):
        def __init__(self):
            self.received_events = []

        async def update(self, event_type: str, data: dict):
            self.received_events.append((event_type, data))

    @pytest.mark.asyncio
    async def test_event_emission(self):
        """イベント発火テスト"""
        event_bus = EventBus()
        observer = self.MockObserver()

        event_bus.attach(observer)

        await event_bus.emit_event("test_event", {"key": "value"})

        assert len(observer.received_events) == 1
        event_type, event_data = observer.received_events[0]
        assert event_type == "test_event"
        assert event_data["data"] == {"key": "value"}

    @pytest.mark.asyncio
    async def test_multiple_observers(self):
        """複数オブザーバーテスト"""
        event_bus = EventBus()
        observer1 = self.MockObserver()
        observer2 = self.MockObserver()

        event_bus.attach(observer1)
        event_bus.attach(observer2)

        await event_bus.emit_event("multi_test", {"data": "test"})

        assert len(observer1.received_events) == 1
        assert len(observer2.received_events) == 1

    def test_event_history(self):
        """イベント履歴テスト"""
        event_bus = EventBus()

        # 履歴が空であることを確認
        history = event_bus.get_event_history()
        assert len(history) == 0

        # イベント発火後の履歴確認
        asyncio.run(event_bus.emit_event("history_test", {}))
        history = event_bus.get_event_history()
        assert len(history) == 1
        assert history[0]["type"] == "history_test"


class TestFactoryPattern:
    def test_cog_registration_and_creation(self):
        """Cog登録・作成テスト"""
        factory = KyriosCogFactory()

        # モックCogクラス
        class MockCog:
            def __init__(self, bot, **kwargs):
                self.bot = bot
                self.kwargs = kwargs

        # 登録
        factory.register_cog("mock_cog", MockCog)
        assert factory.is_cog_registered("mock_cog")

        # 作成
        mock_bot = MagicMock()
        cog = factory.create_cog("mock_cog", bot=mock_bot, extra_param="test")

        assert isinstance(cog, MockCog)
        assert cog.bot is mock_bot
        assert cog.kwargs["extra_param"] == "test"

    def test_unknown_cog_creation(self):
        """未知のCog作成エラーテスト"""
        factory = KyriosCogFactory()

        with pytest.raises(ValueError, match="Unknown cog type"):
            factory.create_cog("unknown_cog")
```

## 統合テストパターン

### Cog統合テスト

```python
# tests/integration/test_cogs.py
import pytest
from unittest.mock import AsyncMock, patch

from cogs.admin import AdminCog
from cogs.tickets import TicketsCog


class TestAdminCogIntegration:
    @pytest.fixture
    def admin_cog(self, mock_bot, in_memory_db, test_container):
        """管理Cog統合テスト用フィクスチャ"""
        with test_container.database_manager.override(in_memory_db):
            cog = AdminCog(mock_bot)
            return cog

    @pytest.mark.asyncio
    async def test_ping_command_full_workflow(self, admin_cog, mock_interaction):
        """pingコマンドの完全ワークフローテスト"""
        with patch('psutil.cpu_percent', return_value=25.5), \
             patch('psutil.virtual_memory') as mock_memory:

            mock_memory.return_value.percent = 45.2
            mock_memory.return_value.used = 4 * 1024 * 1024 * 1024  # 4GB
            mock_memory.return_value.total = 8 * 1024 * 1024 * 1024  # 8GB

            await admin_cog.ping(mock_interaction)

            # インタラクション応答の確認
            mock_interaction.response.defer.assert_called_once()
            mock_interaction.followup.send.assert_called_once()

            # 送信されたEmbedの確認
            call_args = mock_interaction.followup.send.call_args
            embed = call_args[1]['embed']
            assert "高度なレイテンシ測定結果" in embed.title


class TestTicketsCogIntegration:
    @pytest.fixture
    def tickets_cog(self, mock_bot, in_memory_db, test_container):
        """チケットCog統合テスト用フィクスチャ"""
        with test_container.database_manager.override(in_memory_db):
            cog = TicketsCog(mock_bot)
            return cog

    @pytest.mark.asyncio
    async def test_ticket_creation_workflow(self, tickets_cog, mock_interaction, mock_guild):
        """チケット作成ワークフローテスト"""
        # モックチャンネル作成設定
        mock_channel = AsyncMock()
        mock_channel.id = 999888777
        mock_guild.create_text_channel = AsyncMock(return_value=mock_channel)

        # チケットビューのボタンクリックシミュレーション
        ticket_view = tickets_cog.TicketView(tickets_cog.bot)

        await ticket_view.create_ticket(mock_interaction, None)

        # チャンネル作成の確認
        mock_guild.create_text_channel.assert_called_once()

        # フォローアップメッセージの確認
        mock_interaction.followup.send.assert_called_once()
        call_args = mock_interaction.followup.send.call_args
        assert "チケットを作成しました" in call_args[1]['content']
```

### DIコンテナ統合テスト

```python
# tests/integration/test_di_container.py
import pytest
from unittest.mock import MagicMock

from di.container import Container


class TestDIContainerIntegration:
    @pytest.fixture
    def container(self):
        """テスト用コンテナ"""
        container = Container()
        container.init_resources()
        yield container
        container.shutdown_resources()

    def test_container_initialization(self, container):
        """コンテナ初期化テスト"""
        # 各プロバイダーが正しく初期化されているか確認
        config = container.config()
        database = container.database_manager()
        event_bus = container.wired_event_bus()

        assert config is not None
        assert database is not None
        assert event_bus is not None

    def test_dependency_injection(self, container):
        """依存性注入テスト"""
        from dependency_injector.wiring import inject, Provide

        @inject
        def test_function(
            config=Provide[container.config],
            database=Provide[container.database_manager]
        ):
            return config, database

        # ワイヤリング
        container.wire(modules=[__name__])

        try:
            config, database = test_function()
            assert config is not None
            assert database is not None
        finally:
            container.unwire()

    def test_singleton_behavior(self, container):
        """Singletonプロバイダーの動作テスト"""
        # 同じインスタンスが返されることを確認
        config1 = container.config()
        config2 = container.config()

        assert config1 is config2

        database1 = container.database_manager()
        database2 = container.database_manager()

        assert database1 is database2
```

## E2Eテストパターン

### ボットコマンドE2Eテスト

```python
# tests/e2e/test_bot_commands.py
import pytest
import asyncio
from unittest.mock import patch

from bot import KyriosBot


class TestBotE2E:
    @pytest.fixture
    async def bot_instance(self):
        """E2Eテスト用BOTインスタンス"""
        # テスト用設定でBOTを初期化
        with patch('config.settings.Settings') as mock_settings:
            mock_settings.return_value.bot_token = "test_token"
            mock_settings.return_value.database_path = ":memory:"

            bot = KyriosBot()
            yield bot

    @pytest.mark.e2e
    @pytest.mark.asyncio
    async def test_bot_startup_sequence(self, bot_instance):
        """BOT起動シーケンステスト"""
        # setup_hookが正常に完了することを確認
        await bot_instance.setup_hook()

        # Cogが正しく読み込まれているか確認
        loaded_cogs = list(bot_instance.cogs.keys())
        expected_cogs = ["AdminCog", "TicketsCog", "LoggingCog"]

        for expected_cog in expected_cogs:
            assert any(expected_cog in cog_name for cog_name in loaded_cogs)

    @pytest.mark.e2e
    @pytest.mark.skipif(not pytest.config.getoption("--run-e2e"),
                       reason="E2E tests require --run-e2e option")
    async def test_real_discord_interaction(self):
        """実際のDiscord環境でのテスト"""
        # 注意: 実際のDiscord BOTトークンが必要
        # CI環境では環境変数から取得
        # このテストは手動実行時のみ有効
        pass
```

## テストカバレッジと品質

### カバレッジ設定

```bash
# テスト実行とカバレッジレポート生成
poetry run pytest --cov=. --cov-report=html --cov-report=term-missing

# 特定のディレクトリのみテスト
poetry run pytest tests/unit/ -v

# 統合テストのみ実行
poetry run pytest tests/integration/ -v

# E2Eテストを含む全テスト実行
poetry run pytest --run-e2e
```

### 品質ゲート

```yaml
# .github/workflows/tests.yml
name: Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.13]

    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install Poetry
      uses: snok/install-poetry@v1

    - name: Install dependencies
      run: poetry install

    - name: Run tests with coverage
      run: |
        poetry run pytest --cov=. --cov-report=xml --cov-fail-under=80

    - name: Upload coverage reports
      uses: codecov/codecov-action@v4
      with:
        file: ./coverage.xml
```

### テストの実行パターン

```bash
# 開発時の高速テスト
poetry run pytest tests/unit/ -x --tb=short

# 詳細テストレポート
poetry run pytest -v --tb=long

# 並列テスト実行（pytest-xdist使用）
poetry run pytest -n auto

# 特定のテストファイル実行
poetry run pytest tests/unit/test_models.py::TestTicketModel::test_ticket_creation

# マーカーベースの実行
poetry run pytest -m "not e2e"  # E2Eテストを除外
poetry run pytest -m "slow"     # 重いテストのみ実行
```

## テストのベストプラクティス

### テスト設計原則

1. **AAA パターン**: Arrange, Act, Assert の明確な分離
2. **独立性**: テスト間での依存関係を排除
3. **再現性**: 同じ条件で常に同じ結果
4. **可読性**: テストの意図が明確に分かる命名・構造

### モックの使用ガイドライン

```python
# Good: 外部依存のモック
@patch('discord.Guild.create_text_channel')
async def test_channel_creation(self, mock_create_channel):
    mock_create_channel.return_value = mock_channel
    # テストロジック

# Good: 複雑な依存関係の分離
@pytest.fixture
def mock_database():
    db = AsyncMock()
    db.create_ticket.return_value = TicketFactory()
    return db

# Bad: 過度なモック（ビジネスロジックが隠れる）
@patch('database.models.Ticket')  # モデル自体をモックするのは避ける
```

### パフォーマンステスト

```python
import time
import pytest


@pytest.mark.performance
@pytest.mark.asyncio
async def test_database_performance(in_memory_db):
    """データベース操作のパフォーマンステスト"""
    start_time = time.time()

    # 大量データの作成・取得
    tasks = [
        in_memory_db.create_ticket(
            guild_id=123,
            channel_id=456,
            user_id=789,
            title=f"Test Ticket {i}"
        )
        for i in range(100)
    ]

    tickets = await asyncio.gather(*tasks)
    end_time = time.time()

    # パフォーマンス要件の確認
    assert len(tickets) == 100
    assert (end_time - start_time) < 1.0  # 1秒以内に完了
```

この包括的なテストスイートにより、Kyriosの品質と信頼性を継続的に維持できます。