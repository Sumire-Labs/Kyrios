# Kyrios Bot - 設定ガイド

## 設定ファイル概要

Kyriosボットの設定は `config.toml` ファイルで管理されています。このファイルはTOML形式で記述され、ボットの動作をカスタマイズできます。

## 設定ファイル構造

```toml
[bot]
# Discord Bot基本設定

[database]
# データベース設定

[logging]
# ログ設定

[features]
# 機能ON/OFF設定

[tickets]
# チケットシステム設定

[logger]
# ロガー詳細設定
```

---

## [bot] セクション

ボットの基本的な設定を定義します。

```toml
[bot]
token = "YOUR_BOT_TOKEN_HERE"
prefix = "!"
description = "Kyrios - Advanced Discord Administration Bot"
```

### パラメーター詳細

#### `token` (必須)
- **型**: String
- **説明**: Discord Bot Token
- **取得方法**:
  1. [Discord Developer Portal](https://discord.com/developers/applications)
  2. アプリケーション作成
  3. Bot セクションでToken生成

**⚠️ 重要**: Tokenは絶対に公開しないでください

#### `prefix`
- **型**: String
- **デフォルト**: `"!"`
- **説明**: 従来のコマンドプレフィックス
- **例**: `!`, `?`, `>>`, `kyrios!`

#### `description`
- **型**: String
- **デフォルト**: `"Kyrios - Advanced Discord Administration Bot"`
- **説明**: ボットの説明文
- **用途**: ヘルプメッセージなどで表示

---

## [database] セクション

データベース関連の設定を定義します。

```toml
[database]
path = "data/databases/kyrios.db"
backup_interval = 3600
```

### パラメーター詳細

#### `path`
- **型**: String
- **デフォルト**: `"data/databases/kyrios.db"`
- **説明**: SQLiteデータベースファイルパス
- **注意**:
  - ディレクトリが存在しない場合、自動作成されます
  - 相対パスまたは絶対パス使用可能

#### `backup_interval`
- **型**: Integer
- **デフォルト**: `3600` (1時間)
- **単位**: 秒
- **説明**: 自動バックアップ実行間隔
- **推奨値**:
  - 本番環境: `1800` (30分) - `86400` (24時間)
  - 開発環境: `3600` (1時間) - `7200` (2時間)

---

## [logging] セクション

ロギングシステムの設定を定義します。

```toml
[logging]
level = "INFO"
file = "data/logs/kyrios.log"
max_size = 10485760
```

### パラメーター詳細

#### `level`
- **型**: String
- **デフォルト**: `"INFO"`
- **説明**: ログレベル
- **利用可能値**:
  - `"DEBUG"` - 詳細なデバッグ情報
  - `"INFO"` - 一般的な情報
  - `"WARNING"` - 警告メッセージ
  - `"ERROR"` - エラーメッセージのみ
  - `"CRITICAL"` - 致命的エラーのみ

**推奨設定**:
- 開発環境: `"DEBUG"`
- 本番環境: `"INFO"` または `"WARNING"`

#### `file`
- **型**: String
- **デフォルト**: `"data/logs/kyrios.log"`
- **説明**: ログファイル出力パス
- **注意**: ディレクトリが存在しない場合、自動作成されます

#### `max_size`
- **型**: Integer
- **デフォルト**: `10485760` (10MB)
- **単位**: バイト
- **説明**: ログファイル最大サイズ
- **参考値**:
  - `1048576` = 1MB
  - `5242880` = 5MB
  - `10485760` = 10MB
  - `52428800` = 50MB

---

## [features] セクション

各機能の有効/無効を設定します。

```toml
[features]
tickets = true
logger = true
auto_mod = false
```

### パラメーター詳細

#### `tickets`
- **型**: Boolean
- **デフォルト**: `true`
- **説明**: チケットシステム機能の有効化
- **影響**:
  - `true`: `/ticket`コマンド、チケット管理UI利用可能
  - `false`: チケット関連機能すべて無効

#### `logger`
- **型**: Boolean
- **デフォルト**: `true`
- **説明**: ログ機能の有効化
- **影響**:
  - `true`: `/logger`コマンド、自動ログ機能利用可能
  - `false`: ログ関連機能すべて無効

#### `auto_mod`
- **型**: Boolean
- **デフォルト**: `false`
- **説明**: 自動モデレーション機能（未実装）
- **状態**: 開発中のため現在は無効

---

## [tickets] セクション

チケットシステムの詳細設定を定義します。

```toml
[tickets]
category_id = 123456789012345678
archive_category_id = 876543210987654321
max_per_user = 3
```

### パラメーター詳細

#### `category_id`
- **型**: Integer (オプション)
- **デフォルト**: なし
- **説明**: チケット用カテゴリチャンネルのID
- **取得方法**:
  1. Discordで開発者モードを有効化
  2. カテゴリチャンネルを右クリック
  3. 「IDをコピー」を選択

**設定効果**:
- 設定有り: チケットチャンネルが指定カテゴリに作成
- 設定無し: サーバーのトップレベルにチケットチャンネル作成

#### `archive_category_id`
- **型**: Integer (オプション)
- **デフォルト**: なし
- **説明**: クローズされたチケット用アーカイブカテゴリのID

**設定効果**:
- 設定有り: クローズ時に指定カテゴリに移動
- 設定無し: チケットは現在位置でクローズ

#### `max_per_user`
- **型**: Integer
- **デフォルト**: `3`
- **説明**: 1ユーザーあたりの同時オープン可能チケット数
- **推奨値**: `1` - `5`

---

## [logger] セクション

ロガー機能の詳細設定を定義します。

```toml
[logger]
ignore_bots = true
log_edits = true
log_deletes = true
log_joins = true
```

### パラメーター詳細

#### `ignore_bots`
- **型**: Boolean
- **デフォルト**: `true`
- **説明**: ボットのアクションをログから除外
- **推奨**: `true` (ボットのスパム防止)

#### `log_edits`
- **型**: Boolean
- **デフォルト**: `true`
- **説明**: メッセージ編集のログ記録
- **注意**: 高頻度での編集がある場合、ログ量が増大

#### `log_deletes`
- **型**: Boolean
- **デフォルト**: `true`
- **説明**: メッセージ削除のログ記録
- **用途**: モデレーション、証拠保全

#### `log_joins`
- **型**: Boolean
- **デフォルト**: `true`
- **説明**: メンバー参加のログ記録
- **用途**: サーバー成長モニタリング

---

## 環境別設定例

### 開発環境 (config.dev.toml)

```toml
[bot]
token = "DEV_BOT_TOKEN"
prefix = "dev!"
description = "Kyrios - Development Build"

[database]
path = "data/dev/kyrios_dev.db"
backup_interval = 7200  # 2時間

[logging]
level = "DEBUG"
file = "data/logs/kyrios_dev.log"
max_size = 5242880  # 5MB

[features]
tickets = true
logger = true
auto_mod = false

[tickets]
max_per_user = 10  # テスト用に多めに設定

[logger]
ignore_bots = false  # 開発中はボットログも記録
log_edits = true
log_deletes = true
log_joins = true
```

### 本番環境 (config.prod.toml)

```toml
[bot]
token = "PRODUCTION_BOT_TOKEN"
prefix = "!"
description = "Kyrios - Advanced Discord Administration Bot"

[database]
path = "data/production/kyrios.db"
backup_interval = 1800  # 30分

[logging]
level = "WARNING"  # 警告以上のみ
file = "data/logs/kyrios.log"
max_size = 52428800  # 50MB

[features]
tickets = true
logger = true
auto_mod = false

[tickets]
category_id = 987654321098765432
archive_category_id = 123456789012345678
max_per_user = 3

[logger]
ignore_bots = true
log_edits = true
log_deletes = true
log_joins = false  # 大規模サーバーでは無効化検討
```

---

## セキュリティ考慮事項

### ファイル権限

```bash
# 設定ファイルは読み取り専用に設定
chmod 600 config.toml

# ディレクトリ権限
chmod 755 data/
chmod 755 data/logs/
chmod 755 data/databases/
```

### Token管理

1. **環境変数使用（推奨）**:
   ```bash
   export KYRIOS_BOT_TOKEN="your_token_here"
   ```

2. **設定ファイル分離**:
   ```toml
   # config.toml
   token = "${BOT_TOKEN}"  # 環境変数参照
   ```

3. **Git除外設定**:
   ```gitignore
   config.toml
   *.env
   .env.*
   ```

---

## 設定変更の反映

### 再起動が必要な設定
- `[bot]` セクション全体
- `[database]` セクション全体
- `[features]` セクション

### 動的反映可能な設定
- `[logging]` レベル変更
- `[logger]` セクション設定
- 一部の `[tickets]` 設定

### 設定リロード（将来実装予定）

```python
# 管理者コマンドでの設定リロード
/admin reload_config
```

---

## トラブルシューティング

### よくある設定エラー

#### 1. Token関連
```
ValueError: Bot token not configured in config.toml
```
**解決**: `token` 値を正しいBot Tokenに設定

#### 2. パス関連
```
FileNotFoundError: Config file not found: config.toml
```
**解決**: 設定ファイルが正しい場所にあるか確認

#### 3. 権限関連
```
PermissionError: Cannot write to log file
```
**解決**: ログディレクトリの権限を確認

### 設定検証

```bash
# 設定ファイル構文チェック
python -c "import tomllib; tomllib.load(open('config.toml', 'rb'))"

# ボット起動テスト
poetry run python -c "from config.settings import Settings; Settings()"
```

---

## 高度な設定

### 複数環境管理

```bash
# 環境変数で設定ファイル切り替え
export KYRIOS_CONFIG_PATH="config.production.toml"
poetry run python bot.py
```

### 動的設定変更

将来のアップデートで、データベース経由での動的設定変更機能を実装予定。

---

## サポート

設定に関する問題は：
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- [API_REFERENCE.md](API_REFERENCE.md)
- GitHub Issues