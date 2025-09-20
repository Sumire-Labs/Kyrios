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
  luna-bot:
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
chmod 600 data/databases/luna.db
chown bot-user:bot-user data/databases/luna.db

# バックアップファイルの暗号化（推奨）
gpg --symmetric --cipher-algo AES256 luna_backup.db
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
sudo systemctl stop luna-bot.service

# 2. Discord Developer Portal でToken再生成
# 3. 新しいTokenで config.toml 更新
nano config.toml

# 4. ログの確認
grep -E "(login|auth|token)" luna.log

# 5. サービス再開
sudo systemctl start luna-bot.service
```

#### データベース破損時の対応
```bash
# 1. データベースの整合性チェック
sqlite3 luna.db "PRAGMA integrity_check;"

# 2. バックアップからの復旧
cp data/backups/luna_latest.db data/databases/luna.db

# 3. データベース修復（軽微な破損時）
sqlite3 luna.db "VACUUM; REINDEX;"
```

---

## 📞 セキュリティサポート

### 脆弱性の報告

#### 報告方法
1. **GitHub Security Advisories**

#### 必要情報
- 脆弱性の詳細
- 再現手順
- 影響範囲
- 推奨される対策
