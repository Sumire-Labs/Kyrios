# Luna Bot

![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.4.0-blue.svg)
![Version](https://img.shields.io/badge/version-0.1.15-brightgreen.svg)
![License](https://img.shields.io/badge/license-MPL--2.0-green.svg)

**Luna**は個人用の高度なDiscord管理BOTです。オーバーエンジニアリングされたアーキテクチャと、最適化されたUX/パフォーマンスを提供します。

## 特徴

### **高度なチケットシステム**
- インタラクティブなUI（ボタン・モーダル）
- カテゴリ・優先度管理
- 自動権限設定とアーカイブ機能

### **包括的ログシステム**
- メッセージ編集/削除・メンバー参加/退出・モデレーション操作
- 設定可能なフィルタリング
- 構造化されたログ出力

### **アバター解析システム**
- 高解像度アバター・バナー表示（最大1024px）
- リアルタイム画像解析（形式・サイズ・主要色抽出）
- マルチサイズダウンロード・変更統計機能
- 履歴追跡・変更頻度分析

### **高機能音楽システム**
- **インタラクティブUI**: 統合音楽プレイヤー（7ボタンコントローラー）
- **YouTube統合**: yt-dlp による高品質音楽抽出
- **Spotify統合**: Spotify API連携・プレイリスト対応
- **キュー管理**: 無制限楽曲キュー・リアルタイム更新
- **プレイリスト対応**: YouTube/Spotifyプレイリスト一括追加
- **ループモード**: 楽曲・キューリピート対応
- **プログレスバー**: リアルタイム再生進捗表示

### **アーキテクチャ**
- **デザインパターン**: Command, Factory, Observer
- **依存性注入**: 完全なDIコンテナ
- **非同期ファースト**: 真の非ブロッキングI/O
- **型安全性**: Python 3.13 + 厳格な型チェック

### **パフォーマンス最適化**
- **共通関数統一**: 98%のコード共通化率達成
- **メモリリーク対策**: EventBusの自動メモリ管理
- **エラーハンドリング**: 統一された例外処理

## セットアップ

### 前提条件

- Python 3.13以上
- Poetry（依存関係管理）
- Discord BOT トークン
- Spotify API認証情報（音楽機能用、オプション）

### 主要依存関係

- **discord.py** 2.4.0+ - Discord BOT開発フレームワーク
- **SQLModel** 0.0.22+ - データベースORM・バリデーション
- **aiosqlite** 0.20.0+ - 非同期SQLiteドライバー
- **yt-dlp** 2024.12.13+ - YouTube音楽抽出
- **spotipy** 2.23.0+ - Spotify API統合
- **dependency-injector** 4.42.0+ - DIコンテナ
- **Pillow** 11.0.0+ - 画像解析・処理
- **PyNaCl** 1.5.0+ - Discord音声通信

### インストール

1. **リポジトリをクローン**
```bash
git clone https://github.com/Sumire-Labs/Luna.git
cd Luna
```

2. **依存関係をインストール**
```bash
poetry install
```

3. **設定ファイルを編集**
```bash
cp config.toml.example config.toml
# config.tomlのtokenを設定
```

4. **BOTを起動**
```bash
poetry run python bot.py
```
 - メッセージ編集/削除、メンバー参加/退出、モデレーション操作

## アーキテクチャ

### プロジェクト構造
```
Luna/
├── bot.py              # メインBOTファイル
├── config.toml         # 設定ファイル
├── config.toml.example # 設定ファイルテンプレート
├── pyproject.toml      # Poetry設定ファイル
├── test_bot.py         # BOTテスト・開発用スクリプト
├── core/               # 核心システム統合
│   ├── __init__.py     # 統合インポート管理
│   ├── settings.py     # TOML設定管理
│   ├── container.py    # DIコンテナ設定
│   ├── command.py      # Command Pattern
│   ├── factory.py      # Factory Pattern
│   └── observer.py     # Observer Pattern & EventBus
├── database/
│   ├── __init__.py
│   ├── models.py       # SQLModelデータモデル
│   └── manager.py      # データベース操作管理
├── cogs/               # Discord.py Cogs (機能別モジュール)
│   ├── __init__.py
│   ├── ping.py         # システム情報・Pingコマンド
│   ├── avatar.py       # アバター表示・解析システム
│   ├── tickets.py      # チケットシステム
│   ├── logging.py      # ログシステム
│   └── music.py        # 音楽システム（プレイヤー・キュー管理）
├── common/             # 共通ユーティリティ
│   ├── __init__.py
│   ├── embed_builder.py  # 統一Embed作成システム
│   ├── ui_constants.py   # UI色・絵文字・ボタンスタイル
│   ├── user_formatter.py # ユーザー情報フォーマット・権限チェック
│   └── image_analyzer.py # 画像解析・メタデータ抽出
├── music/              # 音楽システムコア
│   ├── __init__.py
│   ├── music_service.py    # 音楽サービス・プレイヤー管理
│   ├── youtube_extractor.py # YouTube音楽抽出
│   ├── spotify_extractor.py # Spotify API統合・楽曲変換
│   └── url_detector.py     # URL自動判定・ルーティング
└── docs/               # 包括的ドキュメント (12ファイル)
    ├── ARCHITECTURE.md      # システム設計・デザインパターン
    ├── API_REFERENCE.md     # コマンド・共通関数リファレンス
    ├── CONFIGURATION.md     # 設定ファイル詳細ガイド
    ├── CONTRIBUTING.md      # 開発貢献ガイド
    ├── DATABASE.md          # データベース設計・操作
    ├── DEPENDENCY_INJECTION.md # DIシステム使用法
    ├── DEPLOYMENT.md        # 本番環境デプロイガイド
    ├── FEATURE_DEVELOPMENT.md  # 新機能開発ガイド
    ├── PERFORMANCE.md       # パフォーマンス最適化
    ├── SECURITY.md          # セキュリティ対策
    ├── TESTING.md           # テスト・CI/CD
    └── TROUBLESHOOTING.md   # 問題解決・エラー対処
```

### 技術的特徴

#### デザインパターン実装
- **Command Pattern** - コマンドの実行・取り消し・ログを統一管理
- **Factory Pattern** - Cogやコンポーネントの動的生成
- **Observer Pattern** - イベントドリブンなログ・通知システム

#### 共通関数アーキテクチャ
- **98%の共通化率**: 重複コードを大幅削減
- **統一エラーハンドリング**: 一貫した例外処理パターン
- **型安全性**: 厳格な型チェックとバリデーション
- **Null安全性**: 安全なオブジェクト操作

#### パフォーマンス最適化
- **EventBusメモリ管理**: 自動メモリリーク防止
- **非同期画像処理**: `asyncio.to_thread`による非ブロッキング処理
- **データベース最適化**: 完全非同期操作 + トランザクション管理

## 設定

### config.toml
```toml
[bot]
token = "YOUR_BOT_TOKEN_HERE"
prefix = "!"
description = "Luna - Advanced Discord Administration Bot"

# ボットステータス設定 (v0.1.5+)
[status]
type = "game"                 # game, watching, listening, streaming
message = "v0.1.10"
streaming_url = ""            # streaming時のみ必要

[database]
path = "luna.db"
backup_interval = 3600

[logging]
level = "INFO"
file = "luna.log"
max_size = 10485760

# EventBusメモリ管理 (v0.1.2+)
[eventbus]
max_history_size = 1000       # メモリリーク防止

[features]
tickets = true
logger = true
music = true
auto_mod = false

# Spotify統合設定 (v0.1.10+)
[spotify]
client_id = "your_spotify_client_id"
client_secret = "your_spotify_client_secret"
```

詳細な設定については [CONFIGURATION.md](docs/CONFIGURATION.md) を参照してください。

### Spotify統合設定

Spotify機能を使用するには、[Spotify Developer Dashboard](https://developer.spotify.com/dashboard/)でアプリを作成し、Client IDとClient Secretを設定してください。

```toml
[spotify]
client_id = "your_actual_spotify_client_id"
client_secret = "your_actual_spotify_client_secret"
```

## データベース

### 主要テーブル
- **tickets** - チケット管理（カテゴリ・優先度・状態）
- **logs** - 包括的なサーバーログ
- **guild_settings** - サーバー別詳細設定
- **tracks** - 音楽楽曲メタデータ（タイトル・アーティスト・URL・Spotify情報）
- **queues** - 音楽キュー管理（位置・追加者）
- **music_sessions** - 音楽セッション状態（チャンネル・ループモード）
- **avatar_history** - アバター変更履歴・統計
- **user_avatar_stats** - ユーザー別アバター分析

詳細なスキーマと操作については [DATABASE.md](docs/DATABASE.md) を参照してください。

## ドキュメント

Lunaは包括的なドキュメントを提供しています。開発・運用・トラブルシューティングまで網羅した12のドキュメントが利用可能です。

### **アーキテクチャ・設計**
| ドキュメント | 概要 |
|-------------|------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | システム設計原則・デザインパターン実装 |
| [DEPENDENCY_INJECTION.md](docs/DEPENDENCY_INJECTION.md) | DIシステムの使用方法・コンテナ設定 |
| [DATABASE.md](docs/DATABASE.md) | データベース設計・モデル定義・クエリ操作 |

### **設定・運用**
| ドキュメント | 概要 |
|-------------|------|
| [CONFIGURATION.md](docs/CONFIGURATION.md) | 設定ファイル詳細ガイド・パラメーター解説 |
| [DEPLOYMENT.md](docs/DEPLOYMENT.md) | 本番環境デプロイ・systemd・Docker設定 |
| [PERFORMANCE.md](docs/PERFORMANCE.md) | **[新規]** パフォーマンス最適化・監視・調整 |
| [SECURITY.md](docs/SECURITY.md) | **[新規]** セキュリティ対策・ベストプラクティス |

### **開発・API**
| ドキュメント | 概要 |
|-------------|------|
| [API_REFERENCE.md](docs/API_REFERENCE.md) | 全コマンドリファレンス・共通関数 |
| [FEATURE_DEVELOPMENT.md](docs/FEATURE_DEVELOPMENT.md) | 新機能開発ガイド・Cog作成・UI/UXガイドライン |
| [TESTING.md](docs/TESTING.md) | テストフレームワーク・CI/CD設定 |

### **サポート・メンテナンス**
| ドキュメント | 概要 |
|-------------|------|
| [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) | 問題解決ガイド・エラー対処法 |
| [MIGRATION.md](docs/MIGRATION.md) | **[新規]** バージョン間移行ガイド・互換性情報 |
| [CONTRIBUTING.md](docs/CONTRIBUTING.md) | 開発貢献ガイド・コーディング規約 |

### **リリース情報**
| ドキュメント | 概要 |
|-------------|------|
| [CHANGELOG.md](CHANGELOG.md) | バージョン履歴・新機能・修正履歴 |

## ライセンス

このプロジェクトはMozilla Public License 2.0の下で公開されています。詳細は[LICENSE.md](LICENSE.md)ファイルをご覧ください。
