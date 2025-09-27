# Luna Bot - アーキテクチャドキュメント

## システム設計原則

Lunaは以下の設計原則に基づいて構築されています：

### 核心原則
- **依存性注入 (DI)**: 疎結合とテスタビリティを実現
- **型安全性**: Python 3.13 + 厳格な型チェック
- **非同期処理**: 全てasync/awaitベースの実装
- **モジュラー設計**: 機能別の明確な分離

## プロジェクト構造

```
Luna/
├── bot.py                  # メインBOTエントリーポイント
├── pyproject.toml          # Poetry設定ファイル
├── config.toml             # BOT設定ファイル
├── config.toml.example     # 設定ファイルテンプレート
├── test_bot.py             # BOTテスト・開発用スクリプト
├── core/                   # 核心システム統合
│   ├── __init__.py         # 統合インポート管理
│   ├── settings.py         # TOML設定ファイルの読み込み
│   ├── container.py        # DIコンテナ定義
│   ├── command.py          # Command Pattern 実装
│   ├── factory.py          # Factory Pattern 実装
│   └── observer.py         # Observer Pattern & EventBus 実装
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLModel データモデル
│   └── manager.py          # データベース操作管理
├── cogs/
│   ├── __init__.py
│   ├── ping.py             # システム情報・Pingコマンド
│   ├── avatar.py           # アバター表示・解析システム
│   ├── tickets.py          # チケットシステム
│   ├── logging.py          # ログシステム
│   └── music.py            # 音楽システム（インタラクティブプレイヤー）
├── common/                 # 共通ユーティリティ
│   ├── __init__.py
│   ├── embed_builder.py    # Embed作成パターン（音楽プレイヤー含む）
│   ├── ui_constants.py     # 色・絵文字定数管理（音楽UI含む）
│   ├── user_formatter.py   # ユーザー情報フォーマット（プログレスバー含む）
│   └── image_analyzer.py   # 画像解析・メタデータ抽出
├── music/                  # 音楽システムコア
│   ├── __init__.py
│   ├── music_service.py    # MusicService・MusicPlayer クラス
│   ├── youtube_extractor.py # YouTube音楽抽出（yt-dlp）
│   ├── spotify_extractor.py # Spotify API統合・楽曲変換
│   ├── url_detector.py     # URL自動判定・ルーティング
│   └── constants.py        # 音楽システム定数管理
├── translation/            # 翻訳システムコア
│   ├── __init__.py
│   ├── deepl_extractor.py  # DeepL API統合
│   ├── translation_service.py # 翻訳サービス・管理クラス
│   └── constants.py        # 翻訳関連定数（言語コード・UI・制限）
└── docs/                   # 包括的ドキュメント
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    ├── CONFIGURATION.md
    ├── CONTRIBUTING.md
    ├── DATABASE.md
    ├── DEPENDENCY_INJECTION.md
    ├── DEPLOYMENT.md
    ├── FEATURE_DEVELOPMENT.md
    ├── PERFORMANCE.md
    ├── SECURITY.md
    ├── TESTING.md
    └── TROUBLESHOOTING.md
```

## デザインパターン実装

### 1. Command Pattern
**目的**: コマンドの実行・取り消し・ログを統一管理

```python
from core import Command, CommandInvoker

class TicketCreateCommand(Command):
    async def execute(self, *args, **kwargs):
        # チケット作成ロジック
        return ticket_id

    def can_undo(self) -> bool:
        return True

    async def undo(self) -> bool:
        # チケット削除ロジック
        return True
```

**利点**:
- 操作の履歴管理
- 取り消し機能の実装
- コマンドの統一インターフェース

### 2. Factory Pattern
**目的**: Cogやコンポーネントの動的生成

```python
from core import LunaCogFactory

# Cog登録
factory.register_cog("tickets", TicketsCog)
factory.register_cog("logging", LoggingCog)

# 動的生成
cog = factory.create_cog("tickets", bot=bot)
```

**利点**:
- 実行時のCog生成
- 設定による機能の有効/無効化
- プラグインアーキテクチャの実現

### 3. Observer Pattern
**目的**: イベントドリブンなログ・通知システム

```python
from core import EventBus

# イベント発火
await event_bus.emit_event("ticket_created", {
    "ticket_id": ticket.id,
    "user_id": user.id
})

# オブザーバー登録
event_bus.attach(LoggingObserver())
event_bus.attach(MetricsObserver())
```

**利点**:
- 疎結合なイベント処理
- 複数システムへの同時通知
- メトリクス・ログの自動収集

## データフロー

### 1. コマンド実行フロー
```
Discord User Input → Discord.py → Cog → Command Pattern → Database → Observer Pattern → Event Bus → Logging
```

### 2. チケット作成フロー
```
ボタンクリック → TicketView → Database操作 → チャンネル作成 → Event発火 → ログ記録
```

### 3. ログシステムフロー
```
Discordイベント → EventListener → Database操作 → LogEmbed生成 → チャンネル送信
```

## レイヤーアーキテクチャ

### プレゼンテーション層 (Presentation Layer)
- **Discord UI**: Embed, Button, Modal, SelectMenu
- **Cogs**: Discord.pyのCogシステム
- **コマンドハンドラー**: スラッシュコマンドの処理

### アプリケーション層 (Application Layer)
- **Command Pattern**: ビジネスロジックの実行
- **Factory Pattern**: オブジェクトの動的生成
- **Observer Pattern**: イベント処理

### ドメイン層 (Domain Layer)
- **Models**: データモデルの定義
- **Business Logic**: チケット・ログの業務ロジック

### インフラストラクチャ層 (Infrastructure Layer)
- **Database Manager**: SQLite操作
- **Config System**: TOML設定管理
- **DI Container**: 依存関係の管理

## 技術スタック

### 言語・フレームワーク
- **Python 3.13**: 最新の言語機能
- **Discord.py 2.4+**: Discord BOT開発
- **FastAPI風設計**: 非同期・型安全

### データ管理
- **SQLModel**: ORMとデータバリデーション
- **SQLAlchemy[asyncio]**: 非同期データベース抽象化
- **aiosqlite**: 非同期SQLiteドライバー（真の非ブロッキングI/O）

### 音楽・メディア処理
- **yt-dlp**: YouTube音楽抽出（高品質・高速）
- **spotipy**: Spotify Web API統合（v0.1.10+）
- **FFmpeg**: 音声処理・形式変換
- **PyNaCl**: Discord音声通信暗号化
- **aiohttp**: 非同期HTTP通信（サムネイル取得等）

### 依存関係管理
- **dependency-injector**: DI コンテナ
- **Pydantic**: 設定バリデーション
- **Poetry**: パッケージ管理

### 開発ツール
- **MyPy**: 静的型チェック
- **Black + Ruff**: コードフォーマット
- **Pytest**: テストフレームワーク

## 設定アーキテクチャ

### 設定の階層
1. **config.toml**: グローバル設定（トークン、ログレベル等）
2. **GuildSettings**: サーバー別設定（DB保存）
3. **環境変数**: デプロイ時オーバーライド

### 設定読み込みフロー
```
config.toml → core/settings.py → DIコンテナ → 各コンポーネント
```

## 共通ユーティリティアーキテクチャ

### 共通関数の設計原則
Lunaでは`common/`ディレクトリに配置された共通ユーティリティが、全cogで統一されたUI/UXを提供します。

#### 1. EmbedBuilder パターン
```python
from common import EmbedBuilder

# 統一されたEmbed作成パターン
embed = EmbedBuilder.create_success_embed("操作完了", "正常に処理されました")
EmbedBuilder.add_user_info_field(embed, user)
EmbedBuilder.set_footer_with_user(embed, interaction.user, "システム名")
```

**利点**:
- 全cogで統一されたEmbed デザイン
- 標準的なフィールド構成の再利用
- フッター・タイムスタンプの自動設定

#### 2. UI Constants 管理
```python
from common import UIColors, UIEmojis, PerformanceUtils

# 統一された色管理
embed.color = UIColors.SUCCESS
title = f"{UIEmojis.SUCCESS} 処理完了"

# パフォーマンス指標の統一判定
color = PerformanceUtils.get_latency_color(latency)
emoji = PerformanceUtils.get_latency_emoji(latency)
```

**利点**:
- ブランド一貫性の維持
- 色・絵文字の集中管理
- レイテンシ判定ロジックの統一

#### 3. UserFormatter ユーティリティ
```python
from common import UserFormatter

# 統一されたユーザー情報表示
user_display = UserFormatter.format_user_mention_and_tag(user)
timestamp = UserFormatter.format_timestamp(datetime.now(), "F")
file_size = UserFormatter.format_file_size(size_bytes)
```

**利点**:
- 情報表示の一貫性
- 国際化対応の準備
- フォーマット変更の一元管理

### 共通化の効果

#### コード削減効果
- **重複コード**: 約150行削除
- **保守性**: 修正箇所の一元化
- **開発速度**: 新機能開発の高速化

#### 一貫性向上
- **UI統一**: 全機能で同一のデザインパターン
- **エラー処理**: 統一されたエラー表示
- **ユーザビリティ**: 予測可能なインターフェース

## 拡張可能性

### 新機能追加のパターン
1. **新しいCog**: 機能単位のモジュール追加
2. **新しいModel**: データベーススキーマ拡張
3. **新しいPattern**: デザインパターンの追加実装
4. **新しいObserver**: イベント処理の拡張
5. **音楽拡張**: 新しい音楽ソースの統合
6. **翻訳拡張**: 新しい翻訳プロバイダーの統合

### 永続View実装 (v1.0.0新機能)

**永続性問題の根本解決**：
Discord.pyのView制限により、BOT再起動後にボタンインタラクションが失敗する問題を完全解決。

```python
class PersistentTicketView(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)  # 永続化設定
        self.bot = bot

    @discord.ui.button(custom_id="persistent_ticket_create")
    async def create_ticket(self, interaction, button):
        # チケット作成処理
```

**自動復元システム**：
```python
async def cog_load(self) -> None:
    """Cog読み込み時に永続Viewを復元"""
    await self._restore_persistent_views()

async def _restore_persistent_views(self):
    # チケット作成パネル復元
    ticket_view = TicketView(self.bot)
    self.bot.add_view(ticket_view)

    # 既存オープンチケット管理View復元
    open_tickets = await self.bot.database.get_all_open_tickets()
    for ticket in open_tickets:
        management_view = TicketManagementView(self.bot, ticket.id)
        self.bot.add_view(management_view)
```

**利点**：
- BOT再起動後もボタンが正常動作
- ユーザビリティの大幅向上
- メンテナンス時のサービス継続性

### プラグインアーキテクチャ
```python
# 既存の登録済みCog
factory.register_cog("tickets", TicketsCog)
factory.register_cog("logging", LoggingCog)
factory.register_cog("avatar", AvatarCog)
factory.register_cog("music", MusicCog)        # ✅ 実装完了（Spotify統合済み）
factory.register_cog("translation", TranslationCog)  # ✅ 実装完了（DeepL統合済み）

# 将来的な拡張
factory.register_cog("auto_mod", AutoModerationCog)
factory.register_cog("games", GamesCog)
factory.register_cog("economy", EconomyCog)
```

### 音楽システム設計実装済み
```python
# Spotify統合実装（v1.0.0）
class SpotifyExtractor:
    async def spotify_to_youtube(self, spotify_track: Dict[str, Any]) -> Optional[TrackInfo]:
        """SpotifyトラックをYouTube検索で変換"""
        artist = spotify_track['artists'][0]['name']
        title = spotify_track['name']
        search_query = f"{artist} {title}"
        youtube_tracks = await self.youtube_extractor.search_tracks(search_query, limit=1)
        return youtube_tracks[0] if youtube_tracks else None

# URL判定・ルーティング実装
class URLDetector:
    @staticmethod
    def detect_url_type(url: str) -> URLInfo:
        """URL種別を自動判定（YouTube/Spotify/検索クエリ）"""
        if 'spotify.com' in url:
            return URLDetector._detect_spotify_type(url)
        elif 'youtube.com' in url or 'youtu.be' in url:
            return URLDetector._detect_youtube_type(url)
        else:
            return URLInfo(source="search", url=url)
```

### プレイリスト機能実装済み
```python
# YouTube/Spotifyプレイリスト一括追加（v0.1.10）
async def _handle_youtube_playlist(self, interaction, message, url_info):
    """YouTubeプレイリストを一括でキューに追加"""
    tracks = await self.youtube_extractor.get_playlist_tracks(url_info.url)
    for track in tracks:
        await self.music_service.add_to_queue(interaction.guild.id, track)

async def _handle_spotify_playlist(self, interaction, message, url_info):
    """Spotifyプレイリストを一括でキューに追加"""
    tracks = await self.spotify_extractor.get_playlist_tracks(url_info.id)
    for track_info in tracks:
        await self.music_service.add_to_queue(interaction.guild.id, track_info)
```

## セキュリティ考慮事項

### データ保護
- **トークン管理**: config.tomlの.gitignore登録
- **SQL インジェクション**: SQLModel/SQLAlchemyによる防護
- **権限チェック**: Discord権限の適切な検証

### エラーハンドリング
- **例外の階層化**: カスタム例外クラス
- **ログの分離**: セキュリティログとアプリログの分離
- **フェイルセーフ**: システム障害時の安全な動作

## パフォーマンス設計

### 非同期処理
- **全面async/await**: ブロッキング処理の排除
- **並行処理**: 複数処理の同時実行
- **aiosqlite統合**: 真の非同期データベース操作によるイベントループ最適化
- **リソース管理**: 非同期コネクション管理とプーリング
- **asyncio.to_thread**: CPU集約的処理（画像解析等）のノンブロッキング実行
- **スレッドプール活用**: 同期ライブラリの非同期統合
- **トランザクション最適化**: async context managerによる自動リソース管理

### メモリ効率
- **Singleton Pattern**: 重いオブジェクトの再利用
- **レイジーロード**: 必要時のみリソース読み込み
- **ガベージコレクション**: 適切なオブジェクト解放

この設計により、Lunaは拡張性・保守性・パフォーマンスを兼ね備えた堅牢なシステムとなっています。