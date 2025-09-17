# Kyrios Bot - 機能開発ガイド

## 新機能開発の流れ

新機能開発の基本的な手順と、実装パターンについて説明します。

## 開発手順

### 1. 設計フェーズ
1. **要件定義**: 機能の目的と仕様を明確化
2. **UI/UX設計**: Discord UIでの表現方法を検討
3. **データ設計**: 必要なデータベースモデルを定義
4. **API設計**: コマンド・イベントインターフェースを設計

### 2. 実装フェーズ
1. **モデル実装**: `database/models.py`にデータモデル追加
2. **マネージャー拡張**: `database/manager.py`にCRUD操作追加
3. **Cog実装**: `cogs/`に機能固有のCogを作成
4. **DI統合**: 必要に応じて`di/container.py`にプロバイダー追加

### 3. テストフェーズ
1. **単体テスト**: モデル・マネージャーのテスト作成
2. **統合テスト**: Cog・コマンドのテスト作成
3. **手動テスト**: Discord環境での動作確認

## 新しいCogの作成

### テンプレート構造

```python
# cogs/new_feature.py
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional
import logging

from di import DatabaseDep, EventBusDep, ConfigDep
from dependency_injector.wiring import inject
from database.models import NewModel, LogType

class NewFeatureCog(commands.Cog):
    @inject
    def __init__(
        self,
        bot,
        database=DatabaseDep,
        event_bus=EventBusDep,
        config=ConfigDep
    ):
        self.bot = bot
        self.database = database
        self.event_bus = event_bus
        self.config = config
        self.logger = logging.getLogger(__name__)

    @app_commands.command(name="new_command", description="新しいコマンドの説明")
    async def new_command(self, interaction: discord.Interaction):
        await interaction.response.defer()

        try:
            # ビジネスロジック実装
            result = await self._process_command(interaction)

            embed = discord.Embed(
                title="✅ 処理完了",
                description="コマンドが正常に実行されました",
                color=discord.Color.green()
            )
            await interaction.followup.send(embed=embed)

            # イベント発火
            await self.event_bus.emit_event("new_command_executed", {
                "user_id": interaction.user.id,
                "guild_id": interaction.guild.id
            })

        except Exception as e:
            self.logger.error(f"Command execution failed: {e}")
            embed = discord.Embed(
                title="❌ エラー",
                description="コマンド実行中にエラーが発生しました",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=embed, ephemeral=True)

    async def _process_command(self, interaction: discord.Interaction):
        # 実際の処理ロジック
        pass

    @commands.Cog.listener()
    async def on_some_event(self, event_data):
        # イベントリスナーの実装
        await self.event_bus.emit_event("custom_event", event_data)

async def setup(bot):
    await bot.add_cog(NewFeatureCog(bot))
```

### Cogの登録

```python
# bot.py の _load_cogs メソッドに追加
cog_files = [
    "cogs.admin",
    "cogs.tickets",
    "cogs.logging",
    "cogs.new_feature"  # 新しいCogを追加
]
```

## データベースモデルの追加

### 新しいモデルの定義

```python
# database/models.py に追加
class NewModel(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int                           # マルチサーバー対応
    user_id: int                           # Discord ユーザーID
    name: str                              # 名前
    description: Optional[str] = None       # 説明
    status: str = "active"                 # ステータス
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    # バリデーション例
    @validator('name')
    def validate_name(cls, v):
        if len(v) < 3:
            raise ValueError('名前は3文字以上である必要があります')
        return v
```

### データベースマネージャーの拡張

```python
# database/manager.py に追加
async def create_new_model(self, guild_id: int, user_id: int,
                          name: str, description: Optional[str] = None) -> NewModel:
    with self.get_session() as session:
        model = NewModel(
            guild_id=guild_id,
            user_id=user_id,
            name=name,
            description=description
        )
        session.add(model)
        session.commit()
        session.refresh(model)
        self.logger.info(f"Created new model {model.id} for user {user_id}")
        return model

async def get_user_models(self, guild_id: int, user_id: int) -> List[NewModel]:
    with self.get_session() as session:
        statement = select(NewModel).where(
            NewModel.guild_id == guild_id,
            NewModel.user_id == user_id,
            NewModel.status == "active"
        )
        return list(session.exec(statement))

async def update_model(self, model_id: int, **kwargs) -> Optional[NewModel]:
    with self.get_session() as session:
        model = session.get(NewModel, model_id)
        if not model:
            return None

        for key, value in kwargs.items():
            if hasattr(model, key):
                setattr(model, key, value)

        model.updated_at = datetime.now()
        session.add(model)
        session.commit()
        session.refresh(model)
        return model
```

## UI/UXパターン

### 1. Embedデザインパターン

```python
def create_success_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=f"✅ {title}",
        description=description,
        color=discord.Color.green(),
        timestamp=datetime.now()
    )

def create_error_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=f"❌ {title}",
        description=description,
        color=discord.Color.red(),
        timestamp=datetime.now()
    )

def create_info_embed(title: str, description: str) -> discord.Embed:
    return discord.Embed(
        title=f"ℹ️ {title}",
        description=description,
        color=discord.Color.blue(),
        timestamp=datetime.now()
    )
```

### 2. ボタンUIパターン

```python
class FeatureView(discord.ui.View):
    def __init__(self, bot, data):
        super().__init__(timeout=300)  # 5分のタイムアウト
        self.bot = bot
        self.data = data

    @discord.ui.button(label="🔧 設定", style=discord.ButtonStyle.secondary)
    async def configure(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ConfigurationModal())

    @discord.ui.button(label="📊 統計", style=discord.ButtonStyle.primary)
    async def show_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = await self._create_stats_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="🗑️ 削除", style=discord.ButtonStyle.danger)
    async def delete(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_messages:
            await interaction.response.send_message("❌ 権限がありません", ephemeral=True)
            return

        # 確認ダイアログ
        confirm_view = ConfirmView()
        await interaction.response.send_message("本当に削除しますか？", view=confirm_view, ephemeral=True)

    async def _create_stats_embed(self) -> discord.Embed:
        # 統計情報のEmbed作成
        pass

class ConfigurationModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="設定変更")

        self.name_input = discord.ui.TextInput(
            label="名前",
            placeholder="新しい名前を入力...",
            max_length=50
        )
        self.description_input = discord.ui.TextInput(
            label="説明",
            style=discord.TextStyle.paragraph,
            placeholder="詳細説明を入力...",
            max_length=500,
            required=False
        )

        self.add_item(self.name_input)
        self.add_item(self.description_input)

    async def on_submit(self, interaction: discord.Interaction):
        # フォーム送信処理
        await interaction.response.send_message("設定が更新されました！", ephemeral=True)
```

### 3. セレクトメニューパターン

```python
class OptionSelect(discord.ui.Select):
    def __init__(self, options_data):
        options = [
            discord.SelectOption(
                label=option["label"],
                description=option["description"],
                emoji=option.get("emoji"),
                value=str(option["value"])
            )
            for option in options_data
        ]

        super().__init__(
            placeholder="オプションを選択してください...",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        selected_value = self.values[0]
        await self.process_selection(interaction, selected_value)

    async def process_selection(self, interaction: discord.Interaction, value: str):
        # 選択処理の実装
        pass
```

## イベント駆動開発

### カスタムイベントの定義

```python
# イベントの発火
await self.event_bus.emit_event("feature_action", {
    "action": "create",
    "user_id": user.id,
    "guild_id": guild.id,
    "resource_id": resource.id,
    "timestamp": datetime.now().isoformat()
})

# イベントの受信
class FeatureObserver(Observer):
    async def update(self, event_type: str, data: Dict[str, Any]) -> None:
        if event_type == "feature_action":
            await self._handle_feature_action(data)

    async def _handle_feature_action(self, data: Dict[str, Any]):
        # イベント処理ロジック
        action = data["action"]
        if action == "create":
            await self._log_creation(data)
        elif action == "update":
            await self._log_update(data)
```

## テスト実装パターン

### 単体テストテンプレート

```python
# tests/test_new_feature.py
import pytest
from unittest.mock import AsyncMock, MagicMock
from database.models import NewModel
from cogs.new_feature import NewFeatureCog

@pytest.fixture
def mock_bot():
    bot = MagicMock()
    bot.user.id = 123456789
    return bot

@pytest.fixture
def mock_database():
    db = AsyncMock()
    db.create_new_model.return_value = NewModel(
        id=1,
        guild_id=123,
        user_id=456,
        name="Test Model"
    )
    return db

@pytest.fixture
def cog(mock_bot, mock_database):
    cog = NewFeatureCog(mock_bot)
    cog.database = mock_database
    return cog

@pytest.mark.asyncio
async def test_create_model(cog, mock_database):
    # テスト実行
    result = await cog._create_model(123, 456, "Test Name")

    # アサーション
    mock_database.create_new_model.assert_called_once_with(
        guild_id=123,
        user_id=456,
        name="Test Name"
    )
    assert result is not None

@pytest.mark.asyncio
async def test_command_execution(cog):
    # Discord Interactionのモック
    interaction = AsyncMock()
    interaction.user.id = 456
    interaction.guild.id = 123
    interaction.response.defer = AsyncMock()
    interaction.followup.send = AsyncMock()

    # コマンド実行
    await cog.new_command(interaction)

    # 検証
    interaction.response.defer.assert_called_once()
    interaction.followup.send.assert_called_once()
```

### 統合テストテンプレート

```python
@pytest.mark.asyncio
async def test_full_workflow():
    # セットアップ
    db_manager = DatabaseManager(":memory:")

    # 1. モデル作成
    model = await db_manager.create_new_model(
        guild_id=123,
        user_id=456,
        name="Integration Test"
    )
    assert model.id is not None

    # 2. 取得テスト
    retrieved = await db_manager.get_user_models(123, 456)
    assert len(retrieved) == 1
    assert retrieved[0].name == "Integration Test"

    # 3. 更新テスト
    updated = await db_manager.update_model(model.id, name="Updated Name")
    assert updated.name == "Updated Name"
```

## ユーティリティ関数

### 共通ユーティリティの活用

Kyriosでは`common/`ディレクトリに再利用可能なユーティリティを配置しています。

#### 画像解析ユーティリティ
```python
# common/image_analyzer.py の使用例
from common.image_analyzer import ImageAnalyzer

class NewFeatureCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.image_analyzer = ImageAnalyzer()

    async def process_image(self, image_url: str):
        # ノンブロッキング画像解析（asyncio.to_thread使用）
        info = await self.image_analyzer.analyze_image(image_url)
        return info.get('dominant_color', '#808080')
```

### よく使う関数パターン

```python
# common/helpers.py（将来の拡張例）
import re
from typing import Optional
from datetime import datetime, timedelta

def parse_time_duration(duration_str: str) -> Optional[timedelta]:
    """
    時間文字列をtimedeltaに変換
    例: "1h30m", "2d", "45s"
    """
    pattern = r'(?:(\d+)d)?(?:(\d+)h)?(?:(\d+)m)?(?:(\d+)s)?'
    match = re.match(pattern, duration_str.lower())

    if not match:
        return None

    days, hours, minutes, seconds = match.groups()
    return timedelta(
        days=int(days or 0),
        hours=int(hours or 0),
        minutes=int(minutes or 0),
        seconds=int(seconds or 0)
    )

#### ログ機能の活用

```python
from common import LogUtils
from database.models import LogType

# ログタイプに応じた色・絵文字の自動選択
log_embed = EmbedBuilder.create_base_embed(
    f"{LogUtils.get_log_emoji(LogType.MEMBER_JOIN)} メンバー参加",
    color=LogUtils.get_log_color(LogType.MEMBER_JOIN)
)
```

### 開発時の注意点

1. **統一性の維持**: 新機能でも既存の共通関数を使用
2. **型ヒントの使用**: 全ての関数で適切な型注釈を記述
3. **エラーハンドリング**: 共通のエラー表示パターンを使用
4. **UI一貫性**: 色・絵文字・フォーマットの統一
5. **ドキュメント**: 新機能の使用例をドキュメントに追加

async def safe_send_message(channel, content=None, embed=None, view=None):
    """安全なメッセージ送信（権限チェック付き）"""
    try:
        return await channel.send(content=content, embed=embed, view=view)
    except discord.Forbidden:
        logging.warning(f"No permission to send message to {channel.id}")
        return None
    except discord.HTTPException as e:
        logging.error(f"Failed to send message: {e}")
        return None
```

## メトリクス・統計収集

### 統計データの収集パターン

```python
class FeatureMetrics:
    def __init__(self, database_manager):
        self.db = database_manager

    async def get_usage_stats(self, guild_id: int) -> dict:
        """機能使用統計を取得"""
        with self.db.get_session() as session:
            # 今日の使用回数
            today = datetime.now().date()
            today_count = session.exec(
                select(func.count(NewModel.id))
                .where(
                    NewModel.guild_id == guild_id,
                    func.date(NewModel.created_at) == today
                )
            ).one()

            # 週次統計
            week_ago = datetime.now() - timedelta(days=7)
            week_count = session.exec(
                select(func.count(NewModel.id))
                .where(
                    NewModel.guild_id == guild_id,
                    NewModel.created_at >= week_ago
                )
            ).one()

            # アクティブユーザー数
            active_users = session.exec(
                select(func.count(func.distinct(NewModel.user_id)))
                .where(
                    NewModel.guild_id == guild_id,
                    NewModel.created_at >= week_ago
                )
            ).one()

            return {
                "today_usage": today_count,
                "week_usage": week_count,
                "active_users": active_users,
                "generated_at": datetime.now().isoformat()
            }

    async def create_stats_embed(self, guild_id: int) -> discord.Embed:
        """統計Embedを作成"""
        stats = await self.get_usage_stats(guild_id)

        embed = discord.Embed(
            title="📊 機能使用統計",
            color=discord.Color.blue(),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="📅 今日の使用回数",
            value=f"**{stats['today_usage']}** 回",
            inline=True
        )

        embed.add_field(
            name="📈 週間使用回数",
            value=f"**{stats['week_usage']}** 回",
            inline=True
        )

        embed.add_field(
            name="👥 アクティブユーザー",
            value=f"**{stats['active_users']}** 人",
            inline=True
        )

        return embed
```

## パフォーマンス最適化ガイド

### 非同期処理のベストプラクティス

#### CPU集約的処理の最適化
```python
import asyncio

class OptimizedCog(commands.Cog):
    async def heavy_processing(self, data):
        # ❌ ブロッキング（イベントループを停止）
        # result = expensive_sync_function(data)

        # ✅ ノンブロッキング（推奨）
        result = await asyncio.to_thread(expensive_sync_function, data)
        return result
```

#### 画像処理の最適化例
```python
from utils.image_analyzer import ImageAnalyzer

async def process_multiple_images(self, image_urls: list[str]):
    analyzer = ImageAnalyzer()

    # ❌ 逐次処理（遅い）
    # results = []
    # for url in image_urls:
    #     result = await analyzer.analyze_image(url)
    #     results.append(result)

    # ✅ 並行処理（高速）
    tasks = [analyzer.analyze_image(url) for url in image_urls]
    results = await asyncio.gather(*tasks)
    return results
```

#### メモリ効率的な実装
```python
# 大量のデータ処理時はチャンク化
async def process_large_dataset(self, data_list: list):
    chunk_size = 10
    for i in range(0, len(data_list), chunk_size):
        chunk = data_list[i:i + chunk_size]
        await asyncio.gather(*[self.process_item(item) for item in chunk])
        # 各チャンク後にイベントループに制御を戻す
        await asyncio.sleep(0)
```

### パフォーマンス監視

```python
import time

async def monitor_performance(self, operation_name: str, operation):
    start_time = time.time()
    try:
        result = await operation()
        execution_time = time.time() - start_time
        self.logger.info(f"{operation_name} completed in {execution_time:.3f}s")
        return result
    except Exception as e:
        execution_time = time.time() - start_time
        self.logger.error(f"{operation_name} failed after {execution_time:.3f}s: {e}")
        raise
```

## 音楽システム開発例

### 実装済み音楽システムの概要

Kyriosには既に完全な音楽システムが実装されています。このセクションでは、音楽システムの設計パターンと拡張方法を説明します。

#### 音楽システムアーキテクチャ

```python
# 音楽システムの主要コンポーネント
music/
├── music_service.py      # コアサービス・プレイヤー管理
└── youtube_extractor.py  # YouTube音楽抽出

cogs/
└── music.py             # Discord UI・コマンド統合
```

#### 音楽システムのデザインパターン実装

##### 1. Service Pattern + Player Pattern
```python
# music/music_service.py
class MusicService:
    """音楽システムメインサービス - Kyriosパターン準拠"""

    def __init__(self, database_manager, event_bus, youtube_extractor):
        self.database = database_manager
        self.event_bus = event_bus
        self.youtube_extractor = youtube_extractor
        self.players: Dict[int, MusicPlayer] = {}

    async def search_and_add(self, guild_id: int, query: str, requested_by: int):
        # 検索・データベース保存・キュー追加
        track_info = await self.youtube_extractor.search_track(query)
        track = await self.database.create_track(...)
        await self.database.add_to_queue(guild_id, track.id, requested_by)

        # EventBus通知
        await self.event_bus.emit_event("track_added", {...})
        return track_info

class MusicPlayer:
    """個別ギルド用音楽プレイヤー"""

    def __init__(self, guild_id: int, voice_client: VoiceClient, music_service):
        self.guild_id = guild_id
        self.voice_client = voice_client
        self.music_service = music_service
        self.current_track: Optional[Track] = None
        self.loop_mode = LoopMode.NONE
```

##### 2. インタラクティブUI Pattern
```python
# cogs/music.py
class MusicPlayerView(discord.ui.View):
    """オールインワン音楽プレイヤー - Kyriosパターン準拠"""

    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)  # 永続View
        self.bot = bot
        self.guild_id = guild_id

    # 🎮 Row 1: メイン再生コントロール
    @discord.ui.button(emoji="⏸️", style=ButtonStyles.PRIMARY, row=0)
    async def play_pause_toggle(self, interaction, button):
        await self._handle_player_action(interaction, "toggle")

    @discord.ui.button(emoji="⏭️", style=ButtonStyles.SECONDARY, row=0)
    async def next_track(self, interaction, button):
        await self._handle_player_action(interaction, "skip")

    # 🗂️ Row 2: キュー・追加操作
    @discord.ui.button(emoji="➕", label="楽曲追加", style=ButtonStyles.SUCCESS, row=1)
    async def add_to_queue(self, interaction, button):
        modal = QuickAddModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)

class QuickAddModal(discord.ui.Modal):
    """楽曲追加用モーダル - Kyriosスタイル"""

    query = discord.ui.TextInput(
        label="YouTubeURL または 検索キーワード",
        placeholder="楽曲のURLまたはタイトル・アーティスト名を入力...",
        max_length=200
    )

    async def on_submit(self, interaction):
        # 非ブロッキング楽曲追加処理
        track_info = await self.bot.music_service.search_and_add(...)
```

##### 3. 共通関数の活用例
```python
# common/embed_builder.py の音楽機能
@staticmethod
def create_music_player_embed(track: Dict, session: Dict, queue: List[Dict]):
    """統合音楽プレイヤーEmbed"""

    # ステータス判定
    status = f"{UIEmojis.PLAY} 再生中" if not session.get('is_paused') else f"{UIEmojis.PAUSE} 一時停止中"
    color = UIColors.MUSIC_PLAYING if not session.get('is_paused') else UIColors.MUSIC_PAUSED

    # プログレスバー作成
    progress_bar = UserFormatter.create_progress_bar(
        track.get('position', 0),
        track.get('duration', 0),
        18
    )

    embed = discord.Embed(title="🎵 Kyrios Music Player", color=color)
    embed.description = f"""
**🎶 [{track['title']}]({track['url']})**
👤 **{track['artist']}**

{progress_bar}
{status} | 🔄 {session.get('loop_mode', 'none').upper()}
"""

    return embed

# common/user_formatter.py の音楽機能
@staticmethod
def create_progress_bar(current: int, total: int, length: int = 20) -> str:
    """音楽プログレスバー作成"""
    if total <= 0:
        return f"{UserFormatter.format_duration(0)} {'▱' * length} {UserFormatter.format_duration(0)}"

    progress = min(current / total, 1.0)
    filled = int(progress * length)
    bar = "▰" * filled + "▱" * (length - filled)

    return f"{UserFormatter.format_duration(current)} {bar} {UserFormatter.format_duration(total)}"

@staticmethod
def format_duration(seconds: int) -> str:
    """秒を MM:SS 形式に変換"""
    minutes, seconds = divmod(int(seconds), 60)
    return f"{minutes}:{seconds:02d}"
```

#### 音楽システム拡張例

##### 新しい音楽ソースの追加
```python
# music/spotify_extractor.py（拡張例）
class SpotifyExtractor:
    """Spotify音楽抽出（将来の拡張例）"""

    async def search_track(self, query: str) -> TrackInfo:
        # Spotify Web API統合
        search_results = await self._spotify_search(query)

        return TrackInfo(
            title=search_results['name'],
            artist=search_results['artists'][0]['name'],
            url=search_results['external_urls']['spotify'],
            duration=search_results['duration_ms'] // 1000,
            thumbnail_url=search_results['album']['images'][0]['url'],
            source=MusicSource.SPOTIFY
        )

# database/models.py に追加
class MusicSource(str, Enum):
    YOUTUBE = "youtube"        # ✅ 実装済み
    SPOTIFY = "spotify"        # 将来の拡張
    SOUNDCLOUD = "soundcloud"  # 将来の拡張
```

##### プレイリスト機能の追加
```python
# database/models.py に新しいモデル追加
class Playlist(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    guild_id: int
    name: str
    created_by: int
    tracks: str  # JSON array of track IDs
    created_at: datetime = Field(default_factory=datetime.now)

# cogs/music.py にプレイリストコマンド追加
@app_commands.command(name="playlist", description="プレイリストを管理します")
async def playlist(self, interaction: discord.Interaction, action: str, name: str = None):
    if action == "create":
        await self._create_playlist(interaction, name)
    elif action == "load":
        await self._load_playlist(interaction, name)
```

#### 音楽システムの最適化ポイント

##### 1. 非ブロッキング処理
```python
# ❌ ブロッキング（悪い例）
def bad_search(self, query):
    result = requests.get(f"https://youtube.com/search?q={query}")  # ブロック
    return result

# ✅ ノンブロッキング（実装済み）
async def search_track(self, query: str) -> TrackInfo:
    loop = asyncio.get_event_loop()
    # CPU集約的処理を別スレッドで実行
    return await loop.run_in_executor(None, self._extract_info, query)
```

##### 2. エラーハンドリング
```python
# 音楽システムの強固なエラーハンドリング例
async def play_track(self, track: Track):
    try:
        audio_url = await self.extractor.get_audio_source(track.url)
        if not audio_url:
            raise Exception("Audio source not found")

        # 音声再生開始
        source = discord.FFmpegPCMAudio(audio_url, ...)
        self.voice_client.play(source, after=self._track_finished)

    except Exception as e:
        self.logger.error(f"Play error: {e}")
        await self.music_service.play_next(self.guild_id)  # 自動で次へ
```

##### 3. リソース管理
```python
# 適切なリソース管理（実装済み）
async def disconnect_voice(self, guild_id: int):
    """ボイスチャンネル切断"""
    player = self.players.get(guild_id)
    if player:
        await player.voice_client.disconnect()  # 接続切断
        del self.players[guild_id]              # メモリ解放

    await self.database.delete_session(guild_id)  # DB清理
```

### 音楽システム開発の教訓

1. **UI統合**: 複雑な機能も1つのEmbedに集約することで使いやすさを確保
2. **共通関数活用**: プログレスバー等の汎用機能は共通モジュールに配置
3. **非同期処理**: yt-dlpなどの重い処理は`asyncio.to_thread`で非ブロッキング化
4. **エラー処理**: 音楽再生は外部依存が多いため、強固なエラーハンドリングが必要
5. **リソース管理**: ボイス接続・プレイヤーオブジェクトの適切な管理

この音楽システム実装により、Kyriosはエンターテイメント性と技術的洗練性を両立したDiscordボットとなっています。

---

この機能開発ガイドにより、一貫性のある高品質な機能を効率的に開発できます。