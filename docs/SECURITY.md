# Luna - セキュリティガイド

## 概要

このガイドでは、Lunaボットのセキュリティベストプラクティス、脆弱性対策、安全な運用方法について説明します。

---

## 🔐 セキュリティ原則

### 1. **最小権限の原則**
- 必要最小限の権限のみを付与
- 管理コマンドは適切な権限チェック実装済み
- ユーザーレベルでの権限分離

### 2. **多層防御**
- アプリケーションレベル + システムレベル + ネットワークレベル
- 入力検証 + 権限チェック + ログ監視
- フェイルセーフ設計

### 3. **透明性とログ**
- 全ての重要な操作をログ記録
- 監査証跡の保持
- セキュリティインシデントの検出

---

## 🛡️ Discord Bot セキュリティ

### 1. **Bot Token 管理**

#### ⚠️ 重要な注意事項
```bash
# 絶対にやってはいけない
git add config.toml           # ❌ トークン流出
echo "token=abc123" >> .env   # ❌ プレーンテキスト保存
```

#### ✅ 安全な管理方法

**環境変数での管理**
```bash
# .bashrc または .profile
export DISCORD_BOT_TOKEN="your_secure_token_here"
```

**設定ファイルの権限設定**
```bash
# config.toml の権限を制限
chmod 600 config.toml
chown bot-user:bot-user config.toml
```

**Docker環境での管理**
```yaml
# docker-compose.yml
services:
  kyrios-bot:
    environment:
      - DISCORD_BOT_TOKEN_FILE=/run/secrets/bot_token
    secrets:
      - bot_token

secrets:
  bot_token:
    file: ./secrets/bot_token.txt
```

### 2. **Discord 権限設定**

#### Bot 招待時の最小権限
```
✅ 推奨権限:
- Read Messages/View Channels
- Send Messages
- Use Slash Commands
- Embed Links
- Read Message History
- Add Reactions

⚠️ 注意が必要な権限:
- Manage Messages (ログ機能で必要)
- Manage Channels (チケット機能で必要)

❌ 避けるべき権限:
- Administrator (過大な権限)
- Manage Server (不要)
- Manage Roles (現在未使用)
```

#### サーバー内権限の制限
```python
# 実装済み権限チェック例
@UserFormatter.has_manage_permissions
async def admin_command(interaction):
    # manage_messages または administrator 権限が必要
    pass
```

---

## 🔒 データ保護

### 1. **機密情報の取り扱い**

#### 保存データの分類
```
🔴 機密レベル 高:
- Discord Bot Token
- データベース暗号化キー（将来実装予定）
- API Keys（外部サービス）

🟡 機密レベル 中:
- ユーザーID、ギルドID
- チャット履歴（ログ）
- チケット内容

🟢 機密レベル 低:
- コマンド使用統計
- パフォーマンス メトリクス
- 一般的な設定情報
```

#### データベースセキュリティ
```bash
# SQLiteファイルの権限設定
chmod 600 data/databases/kyrios.db
chown bot-user:bot-user data/databases/kyrios.db

# バックアップファイルの暗号化（推奨）
gpg --symmetric --cipher-algo AES256 kyrios_backup.db
```

### 2. **データ保持ポリシー**

#### 自動削除の実装
```sql
-- 古いログの自動削除（実装推奨）
DELETE FROM logs
WHERE timestamp < datetime('now', '-90 days');

-- 古いアバター履歴の削除
DELETE FROM avatar_history
WHERE timestamp < datetime('now', '-1 year');
```

#### ユーザーデータの削除
```python
# GDPR準拠のデータ削除機能（実装予定）
async def delete_user_data(user_id: int):
    await database.delete_user_logs(user_id)
    await database.delete_user_tickets(user_id)
    await database.delete_user_avatar_history(user_id)
```

---

## 🚫 入力検証とサニタイゼーション

### 1. **実装済み検証機能**

#### ユーザーID検証
```python
# UserFormatter.format_user_id_or_mention() で実装済み
def safe_user_id_extraction(user_input: str) -> Optional[int]:
    # メンション形式の安全な解析
    # 不正な入力の拒否
    # SQL インジェクション対策
```

#### チャンネル情報の安全な取得
```python
# UserFormatter.format_channel_info() で実装済み
def safe_channel_reference(channel) -> str:
    # 属性存在確認
    # Null 安全性
    # エラーハンドリング
```

### 2. **追加の検証が必要な箇所**

#### チケットコンテンツ
```python
# 実装推奨: コンテンツフィルタリング
def sanitize_ticket_content(content: str) -> str:
    # HTML/Markdownインジェクション対策
    # 不適切なコンテンツの検出
    # 長さ制限の実装
    return clean_content
```

#### ファイルアップロード
```python
# アバター解析での安全性（実装済み）
async def safe_image_analysis(image_url: str):
    # URL バリデーション
    # ファイルサイズ制限
    # ファイル形式チェック
    # タイムアウト設定
```

---

## 🔍 セキュリティ監視

### 1. **ログベース監視**

#### セキュリティイベントの検出
```bash
# 不審なアクティビティの監視
grep -E "(CRITICAL|ERROR)" logs/kyrios.log | grep -E "(auth|permission|token)"

# 大量リクエストの検出
grep "rate limit" logs/kyrios.log | tail -100

# 異常なコマンド使用パターン
grep "command" logs/kyrios.log | awk '{print $3}' | sort | uniq -c | sort -nr
```

#### 自動アラート設定
```bash
#!/bin/bash
# security_monitor.sh

# 権限エラーの検出
if grep -q "permission denied" logs/kyrios.log; then
    echo "Permission violation detected" | mail security@example.com
fi

# 異常なAPIレイテンシ
latency=$(grep "latency" logs/kyrios.log | tail -1 | grep -o '[0-9]*ms' | cut -d'm' -f1)
if [ "$latency" -gt 1000 ]; then
    echo "High latency detected: ${latency}ms" | mail admin@example.com
fi
```

### 2. **リアルタイム監視**

#### Discord.py イベント監視
```python
# 実装済み: ログシステムでの監視
@commands.Cog.listener()
async def on_member_ban(self, guild, user):
    # BANイベントの記録
    # 異常なBAN頻度の検出
    pass

@commands.Cog.listener()
async def on_message_delete(self, message):
    # 大量削除の検出
    # 管理者アクションの監視
    pass
```

---

## 🚨 インシデント対応

### 1. **セキュリティインシデントの分類**

#### レベル1: 軽微
```
例:
- 無効なコマンド使用
- 権限不足でのアクセス試行
- 軽微な設定ミス

対応:
- ログ記録
- 通常運用継続
```

#### レベル2: 中程度
```
例:
- 不審なAPIアクセスパターン
- 予期しない権限昇格
- データベースエラーの頻発

対応:
- 詳細調査
- 一時的な機能制限
- 管理者への通知
```

#### レベル3: 重大
```
例:
- Token の流出疑い
- データベースの破損
- サービス拒否攻撃

対応:
- 即座にサービス停止
- Token の再生成
- フォレンジック調査
```

### 2. **緊急時対応手順**

#### Token 流出時の対応
```bash
# 1. ボット即座停止
sudo systemctl stop kyrios-bot.service

# 2. Discord Developer Portal でToken再生成
# 3. 新しいTokenで config.toml 更新
nano config.toml

# 4. ログの確認
grep -E "(login|auth|token)" logs/kyrios.log

# 5. サービス再開
sudo systemctl start kyrios-bot.service
```

#### データベース破損時の対応
```bash
# 1. データベースの整合性チェック
sqlite3 kyrios.db "PRAGMA integrity_check;"

# 2. バックアップからの復旧
cp data/backups/kyrios_latest.db data/databases/kyrios.db

# 3. データベース修復（軽微な破損時）
sqlite3 kyrios.db "VACUUM; REINDEX;"
```

---

## 🔧 セキュリティ設定

### 1. **システムレベル**

#### ファイアウォール設定
```bash
# UFW での基本設定
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 443  # HTTPS (Discord API)
sudo ufw enable
```

#### ユーザー権限
```bash
# 専用ユーザーの作成
sudo useradd -r -s /bin/false kyrios-bot
sudo mkdir -p /opt/kyrios-bot
sudo chown kyrios-bot:kyrios-bot /opt/kyrios-bot
```

#### systemd セキュリティ設定
```ini
# /etc/systemd/system/kyrios-bot.service
[Unit]
Description=Luna Discord Bot
After=network.target

[Service]
Type=simple
User=kyrios-bot
Group=kyrios-bot
WorkingDirectory=/opt/kyrios-bot
ExecStart=/usr/bin/poetry run python bot.py

# セキュリティ設定
NoNewPrivileges=true
PrivateTmp=true
ProtectHome=true
ProtectSystem=strict
ReadWritePaths=/opt/kyrios-bot/data
RestrictSUIDSGID=true

[Install]
WantedBy=multi-user.target
```

### 2. **アプリケーションレベル**

#### ログレベルの調整
```toml
# 本番環境での設定
[logging]
level = "INFO"          # デバッグ情報を制限
log_to_file = true
log_to_console = false  # 機密情報の出力防止
```

#### 機能制限
```toml
# セキュリティ重視の設定
[features]
tickets = true
logger = true
auto_mod = false        # 慎重な有効化

[logger]
ignore_bots = true      # ボット間のノイズ削減
log_edits = false       # プライバシー考慮
log_deletes = true      # 削除の追跡は維持
```

---

## 📋 セキュリティチェックリスト

### 導入時チェック

#### ✅ インストール・設定
- [ ] Bot Token の安全な保存
- [ ] config.toml の権限設定 (600)
- [ ] データベースファイルの権限設定 (600)
- [ ] 不要な権限の削除
- [ ] ログファイルの権限確認

#### ✅ ネットワーク・システム
- [ ] ファイアウォール設定
- [ ] SSH キー認証の設定
- [ ] 定期アップデートの設定
- [ ] 専用ユーザーでの実行
- [ ] systemd セキュリティオプション

### 運用時チェック

#### ✅ 日常監視 (毎日)
- [ ] エラーログの確認
- [ ] 異常な権限アクセスの確認
- [ ] パフォーマンス監視
- [ ] ディスク使用量確認

#### ✅ 週次チェック (毎週)
- [ ] セキュリティログの詳細分析
- [ ] データベースバックアップ確認
- [ ] 設定ファイルの権限確認
- [ ] 不要ファイルの削除

#### ✅ 月次チェック (毎月)
- [ ] システムアップデート
- [ ] 依存関係の脆弱性チェック
- [ ] アクセスログの分析
- [ ] インシデント対応手順の見直し

---

## 🔄 セキュリティアップデート

### 1. **依存関係の監視**

#### Poetry での脆弱性チェック
```bash
# 定期実行推奨
poetry audit
poetry show --outdated
```

#### GitHub Security Alerts
```
- Dependabot の有効化
- セキュリティアップデートの自動PR
- 脆弱性データベースの監視
```

### 2. **アップデート手順**

#### セキュリティパッチの適用
```bash
# 1. バックアップ作成
cp -r /opt/kyrios-bot /opt/kyrios-bot.backup

# 2. アップデート実行
poetry update

# 3. テスト実行
poetry run python -m pytest

# 4. 本番適用
sudo systemctl restart kyrios-bot.service
```

---

## 📞 セキュリティサポート

### 脆弱性の報告

#### 報告方法
1. **GitHub Security Advisories** (推奨)
2. **Email**: security@example.com
3. **暗号化通信**: PGP公開鍵使用

#### 必要情報
- 脆弱性の詳細
- 再現手順
- 影響範囲
- 推奨される対策

### 緊急時連絡

#### インシデント報告
- **即座に**: GitHub Issues (Critical ラベル)
- **詳細分析**: セキュリティレポート提出
- **フォローアップ**: 対策実装状況報告

---

## 🔮 将来のセキュリティ強化

### 予定されている機能

#### v0.1.7+
- データベース暗号化
- 2FA 対応
- より詳細な権限管理

#### v0.2.0+
- 外部認証プロバイダー連携
- セキュリティ監査ログ
- 自動脅威検出

### 長期的な計画
- SOC2 準拠の実装
- GDPR 完全準拠
- ペネトレーションテストの実施