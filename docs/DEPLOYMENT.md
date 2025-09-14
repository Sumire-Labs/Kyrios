# Kyrios Bot - デプロイメントガイド

## 本番環境への展開

Kyriosボットを本番環境にデプロイする手順を説明します。

## 前提条件

### システム要件
- **Python 3.13以上**
- **Poetry** - 依存関係管理
- **Git** - バージョン管理
- **Discord Application** - Bot Token
- **VPS/サーバー** - Linux推奨（Ubuntu 20.04+）

### 推奨スペック
- **CPU**: 1コア以上
- **RAM**: 512MB以上（推奨1GB）
- **ストレージ**: 2GB以上の空き容量
- **ネットワーク**: 安定したインターネット接続

## デプロイメント手順

### 1. サーバー準備

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# 必要パッケージインストール
sudo apt install git python3 python3-pip python3-venv curl -y

# Poetryインストール
curl -sSL https://install.python-poetry.org | python3 -
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### 2. プロジェクトデプロイ

```bash
# プロジェクトクローン
git clone https://github.com/your-username/kyrios-bot.git
cd kyrios-bot

# 依存関係インストール
poetry install --only=main

# 設定ファイル準備
cp config.toml.example config.toml
```

### 3. 設定ファイル編集

```bash
# 設定ファイル編集
nano config.toml
```

必要な設定：
- `bot.token` - Discord Bot Token
- `database.path` - データベースファイルパス
- `logging.file` - ログファイルパス

### 4. systemd サービス設定

```bash
# サービスファイル作成
sudo nano /etc/systemd/system/kyrios-bot.service
```

サービスファイル内容：
```ini
[Unit]
Description=Kyrios Discord Bot
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/kyrios-bot
ExecStart=/home/ubuntu/.local/bin/poetry run python bot.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

### 5. サービス開始

```bash
# サービス有効化・開始
sudo systemctl daemon-reload
sudo systemctl enable kyrios-bot.service
sudo systemctl start kyrios-bot.service

# ステータス確認
sudo systemctl status kyrios-bot.service
```

## 更新手順

### アプリケーション更新

```bash
cd /path/to/kyrios-bot

# 最新コードを取得
git pull origin main

# 依存関係更新
poetry install --only=main

# サービス再起動
sudo systemctl restart kyrios-bot.service
```

### データベースバックアップ

```bash
# 自動バックアップスクリプト作成
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/home/ubuntu/backups"
DB_FILE="/path/to/kyrios.db"

mkdir -p $BACKUP_DIR
cp $DB_FILE $BACKUP_DIR/kyrios_$DATE.db

# 30日以上古いバックアップを削除
find $BACKUP_DIR -name "kyrios_*.db" -mtime +30 -delete
EOF

chmod +x backup.sh

# Cronでバックアップ自動化（毎日3時実行）
echo "0 3 * * * /home/ubuntu/kyrios-bot/backup.sh" | crontab -
```

## 監視・ログ管理

### ログ確認

```bash
# リアルタイムログ確認
sudo journalctl -u kyrios-bot.service -f

# ログファイル確認
tail -f data/logs/kyrios.log
```

### パフォーマンス監視

```bash
# CPU・メモリ使用量確認
sudo systemctl status kyrios-bot.service

# 詳細なリソース使用量
htop
```

## セキュリティ設定

### ファイアウォール設定

```bash
# UFW有効化
sudo ufw enable

# SSH許可（必要な場合のみ）
sudo ufw allow ssh

# HTTP/HTTPS（Webダッシュボード用）
sudo ufw allow 80,443/tcp
```

### 権限設定

```bash
# ボットユーザー作成（推奨）
sudo useradd -m -s /bin/bash kyrios-bot

# ディレクトリ権限設定
sudo chown -R kyrios-bot:kyrios-bot /path/to/kyrios-bot
sudo chmod -R 755 /path/to/kyrios-bot
sudo chmod 600 /path/to/kyrios-bot/config.toml
```

## トラブルシューティング

### 一般的な問題

1. **Bot Token無効**
   - Discord Developer Portalでトークンを再生成
   - config.tomlを更新

2. **権限不足**
   - Discordサーバーでボット権限を確認
   - 管理者権限が必要な機能は適切に設定

3. **メモリ不足**
   - サーバースペックを確認
   - 不要なプロセスを停止

### ログ分析

```bash
# エラーログのみ表示
sudo journalctl -u kyrios-bot.service --since "1 hour ago" | grep ERROR

# 起動失敗の原因確認
sudo journalctl -u kyrios-bot.service --since "1 hour ago" | grep -A 5 -B 5 "Failed"
```

## Docker デプロイメント（オプション）

### Dockerfile

```dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN pip install poetry

COPY pyproject.toml poetry.lock ./
RUN poetry config virtualenvs.create false \
    && poetry install --only=main --no-dev

COPY . .

CMD ["python", "bot.py"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  kyrios-bot:
    build: .
    restart: unless-stopped
    volumes:
      - ./data:/app/data
      - ./config.toml:/app/config.toml
    environment:
      - PYTHONUNBUFFERED=1
```

## 高可用性設定

### 複数インスタンス対応

- データベースを外部化（PostgreSQL推奨）
- Redis使用でセッション管理
- ロードバランサーでの分散

## パフォーマンス最適化

### 設定調整

```toml
[logging]
level = "WARNING"  # 本番環境では警告以上のみ

[database]
backup_interval = 86400  # 24時間間隔でバックアップ

[features]
auto_mod = false  # 不要な機能は無効化
```

## 監視ツール連携

### Grafana + Prometheus（上級者向け）

- メトリクス収集
- アラート設定
- ダッシュボード作成

## サポート

問題が発生した場合：
1. [TROUBLESHOOTING.md](TROUBLESHOOTING.md)を確認
2. GitHub Issuesで報告
3. ログファイルを添付して詳細を記載