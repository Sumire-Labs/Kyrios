# Kyrios Bot - アーキテクチャドキュメント

## システム設計原則

Kyriosは以下の設計原則に基づいて構築されています：

### 核心原則
- **依存性注入 (DI)**: 疎結合とテスタビリティを実現
- **型安全性**: Python 3.13 + 厳格な型チェック
- **非同期処理**: 全てasync/awaitベースの実装
- **モジュラー設計**: 機能別の明確な分離

## プロジェクト構造

```
Kyrios/
├── bot.py                  # メインBOTエントリーポイント
├── pyproject.toml          # Poetry設定ファイル
├── config.toml             # BOT設定ファイル
├── kyrios/                 # Pythonパッケージ
│   └── __init__.py
├── config/
│   └── settings.py         # TOML設定ファイルの読み込み
├── di/
│   ├── __init__.py
│   └── container.py        # DIコンテナ定義
├── database/
│   ├── __init__.py
│   ├── models.py           # SQLModel データモデル
│   └── manager.py          # データベース操作管理
├── patterns/
│   ├── __init__.py
│   ├── command.py          # Command Pattern 実装
│   ├── factory.py          # Factory Pattern 実装
│   └── observer.py         # Observer Pattern 実装
├── cogs/
│   ├── __init__.py
│   ├── admin.py            # 管理コマンド（ping等）
│   ├── tickets.py          # チケットシステム
│   └── logging.py          # ログシステム
├── events/
│   ├── __init__.py
│   └── handlers.py         # カスタムイベントハンドラー
└── utils/
    ├── __init__.py
    └── helpers.py          # ユーティリティ関数
```

## デザインパターン実装

### 1. Command Pattern
**目的**: コマンドの実行・取り消し・ログを統一管理

```python
from patterns.command import Command, CommandInvoker

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
from patterns.factory import KyriosCogFactory

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
from patterns.observer import EventBus

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
- **SQLAlchemy**: データベース抽象化
- **SQLite**: 軽量データベース

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
config.toml → Settings クラス → DIコンテナ → 各コンポーネント
```

## 拡張可能性

### 新機能追加のパターン
1. **新しいCog**: 機能単位のモジュール追加
2. **新しいModel**: データベーススキーマ拡張
3. **新しいPattern**: デザインパターンの追加実装
4. **新しいObserver**: イベント処理の拡張

### プラグインアーキテクチャ
```python
# 将来的な拡張
factory.register_cog("auto_mod", AutoModerationCog)
~~factory.register_cog("music", MusicCog)~~
~~factory.register_cog("games", GamesCog)~~
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
- **リソース管理**: 適切なコネクション管理

### メモリ効率
- **Singleton Pattern**: 重いオブジェクトの再利用
- **レイジーロード**: 必要時のみリソース読み込み
- **ガベージコレクション**: 適切なオブジェクト解放

この設計により、Kyriosは拡張性・保守性・パフォーマンスを兼ね備えた堅牢なシステムとなっています。