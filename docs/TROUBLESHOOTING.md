# Luna Bot - トラブルシューティングガイド

## 問題解決の基本手順

1. **エラーメッセージの確認**
2. **ログファイルの確認**
3. **設定ファイルの検証**
4. **権限・環境の確認**
5. **最新版への更新**

---

## 起動・設定関連の問題

### ❌ Bot Token関連エラー

#### 症状
```
ValueError: Bot token not configured in config.toml
```

#### 原因と解決策

**原因1**: Token未設定または無効値
```toml
[bot]
token = "YOUR_BOT_TOKEN_HERE"  # デフォルト値のまま
```
**解決**: Discord Developer PortalでBot Tokenを取得して設定

**原因2**: Token形式エラー
- Tokenは通常70文字程度の英数字
- スペースや改行が含まれていないか確認

**原因3**: Tokenが無効化された
- Discord Developer Portalで新しいTokenを生成
- 古いTokenを新しいTokenに置き換え

#### 対処手順
1. [Discord Developer Portal](https://discord.com/developers/applications)にアクセス
2. アプリケーション → Bot → Token → Reset Token
3. 新しいTokenをコピーして`config.toml`に設定

---

### ❌ 設定ファイル読み込みエラー

#### 症状
```
FileNotFoundError: Config file not found: config.toml
```

#### 解決策
```bash
# ファイルの存在確認
ls -la config.toml

# サンプルファイルからコピー
cp config.toml.example config.toml

# 実行パスの確認
pwd
python -c "import os; print(os.getcwd())"
```

#### 症状
```
ValueError: Invalid TOML in config file
```

#### 解決策
```bash
# TOML構文チェック
python -c "
import tomllib
try:
    with open('config.toml', 'rb') as f:
        tomllib.load(f)
    print('✅ 設定ファイルは正常です')
except Exception as e:
    print(f'❌ 設定エラー: {e}')
"
```

**よくある構文エラー**:
```toml
# ❌ 間違い
token = YOUR_TOKEN_HERE          # クォート不足

# ✅ 正しい
token = "YOUR_TOKEN_HERE"        # 文字列はクォートで囲む

# ❌ 間違い
max_per_user = "3"               # 数値を文字列として定義

# ✅ 正しい
max_per_user = 3                 # 数値はそのまま
```

---

### ❌ 権限エラー

#### 症状
```
PermissionError: [Errno 13] Permission denied: 'data/logs/kyrios.log'
```

#### 解決策
```bash
# ディレクトリ作成・権限設定
mkdir -p data/logs data/databases
chmod 755 data data/logs data/databases

# ログファイル権限設定
touch data/logs/kyrios.log
chmod 644 data/logs/kyrios.log

# 設定ファイル権限（セキュリティ強化）
chmod 600 config.toml
```

---

## Poetry/Python関連の問題

### ❌ Poetry not found

#### 症状
```
bash: poetry: command not found
```

#### 解決策
```bash
# Poetryインストール確認
which poetry

# インストールされていない場合
curl -sSL https://install.python-poetry.org | python3 -

# パスに追加
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### ❌ Python バージョンエラー

#### 症状
```
The current project requires Python ^3.13 but you are using Python 3.11.x
```

#### 解決策

**方法1: pyenvでPython 3.13インストール**
```bash
# pyenvインストール（Ubuntu/Debian）
curl https://pyenv.run | bash

# Python 3.13インストール
pyenv install 3.13.0
pyenv local 3.13.0

# Poetry環境再作成
poetry env remove python
poetry install
```

**方法2: システムPython更新**
```bash
# Ubuntu 22.04+ の場合
sudo apt update
sudo apt install python3.13 python3.13-venv
```

### ❌ 依存関係エラー

#### 症状
```
Unable to find a matching version of discord.py
```

#### 解決策
```bash
# Poetryキャッシュクリア
poetry cache clear pypi --all

# 仮想環境再作成
poetry env remove python
poetry install

# 手動での依存関係更新
poetry update
```

---

## Discord Bot関連の問題

### ❌ Bot招待・権限エラー

#### 症状
- Botがサーバーに参加しない
- コマンドに反応しない
- 「Missing Permissions」エラー

#### 解決策

**1. Bot招待の確認**
1. Discord Developer Portal → OAuth2 → URL Generator
2. Scopes: `bot`, `applications.commands`
3. Bot Permissions: 必要な権限を選択
   - `Read Messages/View Channels`
   - `Send Messages`
   - `Embed Links`
   - `Manage Channels` (チケット機能用)
   - `Manage Messages` (ログ機能用)

**2. サーバー権限の確認**
```bash
# ボットが参加しているサーバー確認
# ログで以下が出力されているかチェック
# "Bot is in X guilds"
```

**3. チャンネル権限の確認**
- ボットがチャンネルを閲覧可能か
- メッセージ送信権限があるか
- 必要に応じて管理者権限を付与

### ❌ スラッシュコマンドが表示されない

#### 症状
- `/ping`や`/ticket`が候補に表示されない

#### 解決策

**1. アプリケーションコマンドの同期**
```bash
# ボット再起動
# 通常は自動同期されるが、最大1時間かかる場合がある
```

**2. 権限確認**
- ボット招待時に`applications.commands`スコープが含まれているか
- サーバー管理者権限でコマンド権限を設定

**3. キャッシュクリア**
- Discordアプリの再起動
- `Ctrl+R` でDiscord Web版をリロード

---

## 機能固有の問題

### 🎫 チケットシステムの問題

#### 症状
- チケット作成ボタンが動作しない
- チケットチャンネルが作成されない

#### 解決策

**1. 権限確認**
```toml
# config.toml で機能が有効か確認
[features]
tickets = true
```

**2. カテゴリ設定の確認**
```toml
[tickets]
# カテゴリIDが正しいか確認（オプション）
category_id = 123456789012345678
```

**3. ボット権限確認**
- `Manage Channels` - チャンネル作成用
- `Manage Roles` - 権限設定用

#### 症状
- チケット作成の制限エラー

#### 解決策
```toml
[tickets]
# 制限数を調整
max_per_user = 5  # デフォルト: 3
```

### 📊 ログシステムの問題

#### 症状
- `/logger`コマンドが機能しない
- ログが出力されない

#### 解決策

**1. 機能有効化確認**
```toml
[features]
logger = true

[logger]
log_edits = true
log_deletes = true
log_joins = true
```

**2. ログチャンネル設定**
- `/logger`コマンドを実行したチャンネルでログ出力される
- ボットがそのチャンネルにメッセージ送信権限を持っているか確認

**3. ログファイル確認**
```bash
# ログファイルの内容確認
tail -f data/logs/kyrios.log

# エラーメッセージの検索
grep "ERROR" data/logs/kyrios.log
```

---

## v0.1.6 特有の問題

### ❌ 共通関数インポートエラー

#### 症状
```
ImportError: cannot import name 'UserFormatter' from 'common'
ModuleNotFoundError: No module named 'common'
```

#### 原因と解決策

**原因1**: キャッシュの問題
```bash
# Pythonキャッシュクリア
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +

# Poetryキャッシュクリア
poetry cache clear pypi --all
```

**原因2**: インストールの問題
```bash
# 依存関係の再インストール
poetry install --no-cache

# 仮想環境の再作成
rm -rf .venv
poetry install
```

#### 対処手順
1. ボット停止
2. キャッシュクリア
3. 仮想環境再作成
4. ボット再起動

### ❌ 権限チェックエラー

#### 症状
```
AttributeError: 'NoneType' object has no attribute 'guild_permissions'
TypeError: UserFormatter.has_manage_permissions() missing 1 required positional argument
```

#### 原因と解決策

**原因**: 不正なユーザーオブジェクト渡し
```python
# ❌ 間違った使用法
UserFormatter.has_manage_permissions()  # 引数なし

# ✅ 正しい使用法
UserFormatter.has_manage_permissions(interaction.user)
```

**対処方法**:
```python
# Null安全性チェック
if interaction.user and UserFormatter.has_manage_permissions(interaction.user):
    # 管理者処理
    pass
```

### ❌ チャンネル参照エラー

#### 症状
```
AttributeError: 'NoneType' object has no attribute 'name'
AttributeError: 'TextChannel' object has no attribute 'mention'
```

#### 原因と解決策

**v0.1.6での対応**: 共通関数が自動的に処理
```python
# 旧版での問題（v0.1.5以前）
channel_name = f"#{channel.name}"  # channel.nameがNoneの場合エラー

# v0.1.6での解決
channel_name = UserFormatter.format_channel_name(channel)  # 安全
```

### ❌ 色変換エラー

#### 症状
```
ValueError: Invalid color value: 'invalid_color'
discord.errors.HTTPException: Invalid embed color
```

#### 原因と解決策

**v0.1.6での対応**: 安全な色変換関数
```python
# 旧版での問題
try:
    color = discord.Color.from_str(hex_color)
except:
    color = discord.Color.default()

# v0.1.6での解決
color = UserFormatter.safe_color_from_hex(hex_color, UIColors.DEFAULT)
```

---

## リファクタリング後の互換性問題

### 🔄 v0.1.5→v0.1.6移行時の問題

#### メソッド名変更エラー
```
AttributeError: module 'common' has no attribute 'old_function_name'
```

**解決**: [MIGRATION.md](MIGRATION.md)の移行ガイドを参照

#### 設定ファイル互換性
```toml
# v0.1.6で新しく追加された設定（オプション）
[eventbus]
max_history_size = 1000

[status]
type = "game"
message = "Luna v0.1.6"
```

**注意**: これらの設定は必須ではありません。未設定でもボットは正常動作します。

---

## パフォーマンス関連の問題

### 🐌 レスポンスが遅い

#### 原因と解決策

**1. データベース最適化**
```bash
# データベースサイズ確認
du -h data/databases/kyrios.db

# 大きすぎる場合（100MB+）はバックアップして最適化
sqlite3 data/databases/kyrios.db "VACUUM;"
```

**2. ログ設定の最適化**
```toml
[logging]
level = "WARNING"  # DEBUGからWARNINGに変更

[logger]
ignore_bots = true  # ボットログを無視
```

**3. リソース確認**
```bash
# CPU・メモリ使用量確認
htop

# ディスク使用量確認
df -h
```

### 💾 メモリ不足・リーク

#### 症状
```
MemoryError
OutOfMemoryError: Process exceeded memory limit
```

#### v0.1.6での改善
EventBusメモリリーク対策が実装済み：
```toml
[eventbus]
max_history_size = 1000  # メモリ使用量制限
```

#### 解決策

**1. EventBus設定最適化（v0.1.6）**
```toml
# 小規模サーバー
[eventbus]
max_history_size = 500

# 大規模サーバー
[eventbus]
max_history_size = 2000
```

**2. システムリソース確認**
```bash
# メモリ使用量確認
free -h

# プロセス別メモリ使用量
ps aux | grep "python bot.py"

# v0.1.6でのメモリ統計確認
# /ping コマンドで詳細表示
```

**3. スワップファイル作成（緊急対応）**
```bash
sudo fallocate -l 1G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**4. 設定最適化**
```toml
[database]
backup_interval = 86400  # バックアップ頻度を下げる

[logging]
level = "ERROR"  # ログレベルを上げる
max_size = 5242880  # ログファイルサイズを小さく

[eventbus]
max_history_size = 500  # メモリ使用量削減
```

**5. 定期再起動（最終手段）**
```bash
# 週1回の自動再起動（crontab）
0 3 * * 0 sudo systemctl restart kyrios-bot.service
```

---

## ネットワーク関連の問題

### 🌐 接続エラー

#### 症状
```
aiohttp.client_exceptions.ClientConnectorError
```

#### 解決策

**1. インターネット接続確認**
```bash
ping discord.com
curl -I https://discord.com/api/v10/gateway
```

**2. ファイアウォール設定**
```bash
# ポート443（HTTPS）が開放されているか確認
sudo ufw status
sudo ufw allow out 443
```

**3. DNS設定確認**
```bash
nslookup discord.com
# 応答がない場合、DNS設定を確認
```

---

## ログ分析とデバッグ

### 📋 ログファイルの確認方法

#### 基本的なログ確認
```bash
# 最新100行表示
tail -100 data/logs/kyrios.log

# エラーのみ表示
grep "ERROR" data/logs/kyrios.log

# 特定時間のログ表示
grep "2024-01-15 10:" data/logs/kyrios.log

# リアルタイム監視
tail -f data/logs/kyrios.log
```

#### システムログの確認（systemd使用時）
```bash
# サービスログ表示
sudo journalctl -u kyrios-bot.service -f

# エラーログのみ
sudo journalctl -u kyrios-bot.service --since "1 hour ago" | grep ERROR
```

### 🔍 デバッグモードの有効化

#### 一時的なデバッグ
```toml
[logging]
level = "DEBUG"  # 詳細なログ出力
```

#### 特定機能のデバッグ
```python
# bot.py での一時的なデバッグコード追加
import logging
logging.getLogger('discord.gateway').setLevel(logging.DEBUG)
```

---

## よくあるエラーメッセージと対処法

### Discord.py関連エラー

#### `Forbidden: 403 Forbidden (error code: 50013)`
**原因**: ボット権限不足
**解決**: サーバーでボット権限を確認・付与

#### `NotFound: 404 Not Found (error code: 10003)`
**原因**: 指定されたチャンネル・ユーザーが存在しない
**解決**: ID確認、チャンネル存在確認

#### `HTTPException: 400 Bad Request`
**原因**: リクエストパラメータエラー
**解決**: ログでリクエスト内容を確認

### SQLModel関連エラー

#### `sqlalchemy.exc.OperationalError: no such table`
**原因**: データベーステーブル未作成
**解決**:
```bash
# データベース初期化（将来実装予定）
poetry run python -c "from database.manager import DatabaseManager; DatabaseManager().init_db()"
```

---

## サポートとリソース

### 🆘 問題が解決しない場合

1. **GitHub Issues作成**
   - エラーメッセージの完全なコピー
   - 環境情報（OS、Python版、Poetry版）
   - 再現手順の記載

2. **ログファイル添付**
   - 個人情報をマスキングしてからアップロード
   - エラー発生前後のログ

3. **設定ファイル共有**
   - **⚠️ BOT TOKENは削除してから共有**

### 📚 追加リソース

- [Discord.py Documentation](https://discordpy.readthedocs.io/)
- [Discord Developer Documentation](https://discord.com/developers/docs)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [SQLModel Documentation](https://sqlmodel.tiangolo.com/)

### 🛠️ 開発者向けデバッグ

```python
# 詳細なスタックトレース表示
import traceback
try:
    # 問題のあるコード
    pass
except Exception as e:
    traceback.print_exc()
    logging.error(f"Detailed error: {e}")
```

---

## 予防的メンテナンス

### 定期チェックリスト

**週次**:
- [ ] ログファイル確認
- [ ] データベースサイズ確認
- [ ] ディスク使用量確認

**月次**:
- [ ] データベースバックアップ
- [ ] 依存関係更新チェック
- [ ] 設定ファイル見直し

**重要な更新前**:
- [ ] フルバックアップ作成
- [ ] テスト環境での動作確認
- [ ] ロールバック計画準備