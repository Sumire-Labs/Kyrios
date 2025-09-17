# Kyrios Bot

![Python](https://img.shields.io/badge/python-3.13%2B-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.4.0-blue.svg)
![License](https://img.shields.io/badge/license-MPL--2.0-green.svg)

**Kyrios**は個人用の高度な管理BOTです。オーバーエンジニアリングされたアーキテクチャと、最適化されたUXを提供します。

## 特徴

- **高度なチケットシステム** - チケットツール
- **包括的ログシステム** - ログ出力
- **デザインパターン実装** - Command, Factory, Observer パターン

## セットアップ

### 前提条件

- Python 3.13以上
- Poetry（依存関係管理）
- Discord BOT トークン

### インストール

1. **リポジトリをクローン**
```bash
git clone https://github.com/your-username/kyrios-bot.git
cd kyrios-bot
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
Kyrios/
├── bot.py              # メインBOTファイル
├── config.toml         # 設定ファイル
├── config.toml.example # 設定ファイルテンプレート
├── pyproject.toml      # Poetry設定ファイル
├── test_bot.py         # BOTテスト・開発用スクリプト
├── kyrios/             # Pythonパッケージ
│   └── __init__.py
├── config/
│   ├── __init__.py
│   └── settings.py     # TOML設定管理
├── database/
│   ├── __init__.py
│   ├── models.py       # SQLModelデータモデル
│   └── manager.py      # データベース操作管理
├── patterns/           # デザインパターン実装
│   ├── __init__.py
│   ├── command.py      # Command Pattern
│   ├── factory.py      # Factory Pattern
│   └── observer.py     # Observer Pattern & EventBus
├── cogs/               # Discord.py Cogs (機能別モジュール)
│   ├── __init__.py
│   ├── ping.py         # システム情報・Pingコマンド
│   ├── avatar.py       # アバター表示・解析システム
│   ├── tickets.py      # チケットシステム
│   └── logging.py      # ログシステム
├── events/             # カスタムイベントハンドラー
│   └── __init__.py
├── common/             # 共通ユーティリティ
│   ├── __init__.py
│   └── image_analyzer.py # 画像解析・メタデータ抽出
├── di/                 # 依存性注入システム
│   ├── __init__.py
│   └── container.py    # DIコンテナ設定
└── docs/               # 包括的ドキュメント
    ├── ARCHITECTURE.md
    ├── API_REFERENCE.md
    ├── CONFIGURATION.md
    ├── CONTRIBUTING.md
    ├── DATABASE.md
    ├── DEPENDENCY_INJECTION.md
    ├── DEPLOYMENT.md
    ├── FEATURE_DEVELOPMENT.md
    ├── TESTING.md
    └── TROUBLESHOOTING.md
```

### デザインパターン

- **Command Pattern** - コマンドの実行・取り消し・ログを統一管理
- **Factory Pattern** - Cogや コンポーネントの動的生成
- **Observer Pattern** - イベントドリブンなログ・通知システム

## 設定

### config.toml
```toml
[bot]
token = "YOUR_BOT_TOKEN_HERE"  # BOTトークン
prefix = "!"                   # コマンドプレフィックス
description = "Kyrios - Advanced Discord Administration Bot"

[database]
path = "kyrios.db"            # SQLiteファイルパス
backup_interval = 3600        # バックアップ間隔（秒）

[logging]
level = "INFO"                # ログレベル
file = "kyrios.log"          # ログファイルパス
max_size = 10485760          # ログファイル最大サイズ

```

## データベース

### 主要テーブル
- **tickets** - チケット情報
- **logs** - ログエントリ
- **guild_settings** - サーバー別設定
- **ticket_messages** - チケット内メッセージ

## 開発ドキュメント

Kyriosの開発docsは以下のファイルです
詳細な実装については、各ドキュメントをご参照ください。

### 🏗️ [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- システム設計原則
- プロジェクト構造詳細
- デザインパターン実装

### 💉 [DEPENDENCY_INJECTION.md](docs/DEPENDENCY_INJECTION.md)
- DIシステムの使用方法
- コンテナ設定
- 依存関係の管理

### 📊 [DATABASE.md](docs/DATABASE.md)
- データベース設計
- モデル定義
- クエリ操作方法

### 🚀 [FEATURE_DEVELOPMENT.md](docs/FEATURE_DEVELOPMENT.md)
- 新機能開発ガイド
- Cog作成方法
- UI/UX ガイドライン

### 🧪 [TESTING.md](docs/TESTING.md)
- テストフレームワーク
- モックとテストデータ
- CI/CD設定

### 📚 [API_REFERENCE.md](docs/API_REFERENCE.md)
- 全コマンドリファレンス
- 使用方法と例
- パラメーター詳細

### ⚙️ [CONFIGURATION.md](docs/CONFIGURATION.md)
- 設定ファイル詳細ガイド
- 環境別設定例
- パラメーター解説

### 🚀 [DEPLOYMENT.md](docs/DEPLOYMENT.md)
- 本番環境デプロイガイド
- systemd設定
- Docker設定

### 🤝 [CONTRIBUTING.md](docs/CONTRIBUTING.md)
- 開発貢献ガイド
- コーディング規約
- プルリクエスト手順

### 🔧 [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
- 問題解決ガイド
- よくあるエラーと対処法
- デバッグ方法

### 📝 [CHANGELOG.md](CHANGELOG.md)
- バージョン履歴
- 新機能・修正履歴
- マイグレーション注意事項

## ライセンス

このプロジェクトはMozilla Public License 2.0の下で公開されています。詳細は[LICENSE.md](LICENSE.md)ファイルをご覧ください。
