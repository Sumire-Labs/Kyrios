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
├── pyproject.toml      # Poetry設定ファイル
├── kyrios/             # Pythonパッケージ
│   └── __init__.py
├── config/
│   └── settings.py     # 設定管理
├── database/
│   ├── models.py       # データモデル
│   └── manager.py      # DB管理
├── patterns/           # デザインパターン
│   ├── command.py
│   ├── factory.py
│   └── observer.py
├── cogs/               # 機能別モジュール
│   ├── admin.py
│   ├── tickets.py
│   └── logging.py
├── events/             # イベントハンドラー
├── utils/              # ユーティリティ
└── di/                 # 依存性注入
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

[features]
tickets = true               # チケット機能
logger = true               # ログ機能
auto_mod = false           # 自動モデレーション（未実装）
```

## データベース

### 主要テーブル
- **tickets** - チケット情報
- **logs** - ログエントリ
- **guild_settings** - サーバー別設定
- **ticket_messages** - チケット内メッセージ

### 多サーバー対応
各テーブルに`guild_id`を含めることで、複数サーバーでの利用に対応しています。

## 開発ドキュメント

Kyriosの開発docsは以下のファイルです
詳細な実装については、各ドキュメントをご参照ください。

### 🏗️ [ARCHITECTURE.md](ARCHITECTURE.md)
- システム設計原則
- プロジェクト構造詳細
- デザインパターン実装

### 💉 [DEPENDENCY_INJECTION.md](DEPENDENCY_INJECTION.md)
- DIシステムの使用方法
- コンテナ設定
- 依存関係の管理

### 📊 [DATABASE.md](DATABASE.md)
- データベース設計
- モデル定義
- クエリ操作方法

### 🚀 [FEATURE_DEVELOPMENT.md](FEATURE_DEVELOPMENT.md)
- 新機能開発ガイド
- Cog作成方法
- UI/UX ガイドライン

### 🧪 [TESTING.md](TESTING.md)
- テスト
- モックとテストデータ
- CI/CD設定

## ライセンス

このプロジェクトはMozilla Public License 2.0の下で公開されています。詳細は[LICENSE.md](LICENSE.md)ファイルをご覧ください。
