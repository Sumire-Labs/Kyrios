# Luna - パフォーマンスガイド

## 概要

このガイドでは、Lunaボットのパフォーマンス最適化、監視、トラブルシューティングについて説明します。

---

## 📊 パフォーマンス指標

### 主要メトリクス

#### 1. **レスポンス時間**
```
/ping コマンドで確認可能
```

**目標値**:
- **Discord APIレイテンシ**: < 100ms
- **データベースレスポンス**: < 50ms
- **コマンド処理時間**: < 200ms

#### 2. **リソース使用量**
```
/ping コマンドで確認可能
```

**推奨値**:
- **CPU使用率**: < 30%（平常時）
- **メモリ使用率**: < 70%
- **ディスク使用量**: < 80%

#### 3. **データベースパフォーマンス**
- **クエリ実行時間**: < 100ms
- **同時接続数**: 最大10接続
- **トランザクション成功率**: > 99%

---

## ⚡ 最適化戦略

### 1. **メモリ最適化**

#### EventBus設定
```toml
[eventbus]
max_history_size = 1000  # 小規模: 500, 大規模: 2000
```

**効果**:
- メモリリーク防止
- 長期稼働時の安定性向上
- ガベージコレクション効率化

#### 画像処理最適化
```python
# common/image_analyzer.py で実装済み
await asyncio.to_thread(self._analyze_image_data_sync, image_data)
```

**効果**:
- UIスレッドのブロック防止
- 並行処理による高速化
- メモリ効率の向上

### 2. **データベース最適化**

#### 非同期操作
```python
# 全データベース操作で実装済み
async with self.database.transaction():
    result = await self.database.create_ticket(...)
```

**効果**:
- イベントループのブロック防止
- 並行リクエスト処理
- スループット向上

#### インデックス戦略
```sql
-- 自動実装済みインデックス
CREATE INDEX idx_tickets_user_id ON tickets(user_id);
CREATE INDEX idx_logs_guild_timestamp ON logs(guild_id, timestamp);
CREATE INDEX idx_avatar_history_user ON avatar_history(user_id, timestamp);
```

### 3. **キャッシュ戦略**

#### ギルド設定キャッシュ
```python
# logging.py で実装済み
self.log_channels = {}  # ギルドごとのログチャンネルキャッシュ
```

#### Discord オブジェクトキャッシュ
```python
# Discord.py内蔵キャッシュを活用
member = interaction.guild.get_member(user_id)  # キャッシュから取得
```

---

## 📈 パフォーマンス監視

### 1. **リアルタイム監視**

#### `/ping`コマンド活用
```
定期実行推奨: 1時間ごと
```

**監視項目**:
- Discord APIレイテンシ
- データベースレスポンス時間
- CPU/メモリ使用率
- EventBus統計情報

#### ログベース監視
```bash
# ログファイル監視
tail -f luna.log | grep -E "(ERROR|WARNING|CRITICAL)"
```

### 2. **システム監視**

#### systemctl での監視
```bash
# サービス状態確認
sudo systemctl status luna-bot.service

# メモリ使用量確認
sudo systemctl show luna-bot.service --property=MemoryCurrent
```

#### リソース監視
```bash
# プロセス監視
ps aux | grep "python bot.py"

# ファイルディスクリプタ使用量
lsof -p $(pgrep -f "python bot.py") | wc -l
```

---

## 🔧 パフォーマンス調整

### 1. **設定最適化**

#### サーバーサイズ別推奨設定

**小規模サーバー (< 100メンバー)**
```toml
[eventbus]
max_history_size = 500

[database]
backup_interval = 7200  # 2時間

[logger]
ignore_bots = true
```

**中規模サーバー (100-1000メンバー)**
```toml
[eventbus]
max_history_size = 1000

[database]
backup_interval = 3600  # 1時間

[logger]
ignore_bots = true
log_edits = true
```

**大規模サーバー (1000+ メンバー)**
```toml
[eventbus]
max_history_size = 2000

[database]
backup_interval = 1800  # 30分

[logger]
ignore_bots = true
log_edits = false  # 負荷軽減
log_deletes = true
```

### 2. **システムレベル最適化**

#### Python最適化
```bash
# プロダクション実行
export PYTHONOPTIMIZE=1
python -O bot.py
```

#### メモリ管理
```bash
# スワップ設定
sudo sysctl vm.swappiness=10

# ファイルディスクリプタ制限
ulimit -n 4096
```

---

## 🚨 トラブルシューティング

### 1. **高レイテンシ対策**

#### 症状
```
Discord APIレイテンシ > 200ms
```

**原因と対策**:
1. **ネットワーク問題**
   ```bash
   # Discord API接続テスト
   ping discord.com
   traceroute discord.com
   ```

2. **レート制限**
   ```python
   # ログで確認
   grep "429" luna.log
   ```

3. **サーバー負荷**
   ```bash
   top -p $(pgrep -f "python bot.py")
   ```

### 2. **メモリリーク対策**

#### 症状
```
メモリ使用率が時間とともに増加
```

**診断方法**:
```python
# メモリプロファイリング
import tracemalloc
tracemalloc.start()

# EventBus統計確認
/ping  # EventBus統計を確認
```

**対策**:
1. **EventBus設定調整**
   ```toml
   [eventbus]
   max_history_size = 500  # 削減
   ```

2. **定期再起動**
   ```bash
   # crontabで週1回再起動
   0 3 * * 0 sudo systemctl restart luna-bot.service
   ```

### 3. **データベース最適化**

#### 症状
```
データベースレスポンス > 100ms
```

**対策**:
1. **データベース最適化**
   ```bash
   # SQLite最適化
   sqlite3 luna.db "VACUUM;"
   sqlite3 luna.db "ANALYZE;"
   ```

2. **古いデータ削除**
   ```sql
   -- 90日以上古いログを削除
   DELETE FROM logs WHERE timestamp < datetime('now', '-90 days');
   ```

---

## 📋 ベンチマーク

### 標準的なパフォーマンス値

#### 軽負荷時（< 10 リクエスト/分）
| 項目 | 目標値 | 許容値 |
|------|--------|--------|
| Discord APIレイテンシ | < 50ms | < 100ms |
| データベースレスポンス | < 20ms | < 50ms |
| CPU使用率 | < 5% | < 15% |
| メモリ使用量 | < 100MB | < 200MB |

#### 中負荷時（10-50 リクエスト/分）
| 項目 | 目標値 | 許容値 |
|------|--------|--------|
| Discord APIレイテンシ | < 100ms | < 200ms |
| データベースレスポンス | < 50ms | < 100ms |
| CPU使用率 | < 15% | < 30% |
| メモリ使用量 | < 200MB | < 400MB |

#### 高負荷時（50+ リクエスト/分）
| 項目 | 目標値 | 許容値 |
|------|--------|--------|
| Discord APIレイテンシ | < 200ms | < 500ms |
| データベースレスポンス | < 100ms | < 200ms |
| CPU使用率 | < 30% | < 50% |
| メモリ使用量 | < 400MB | < 800MB |

---

## 🔍 プロファイリング

### 1. **パフォーマンス分析**

#### cProfileでの詳細分析
```bash
# プロファイリング実行
python -m cProfile -o profile.stats bot.py

# 結果分析
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative').print_stats(20)
"
```

#### メモリプロファイリング
```python
# memory_profiler使用
pip install memory_profiler

# メモリ使用量監視
python -m memory_profiler bot.py
```

### 2. **継続的監視**

#### カスタム監視スクリプト
```bash
#!/bin/bash
# performance_monitor.sh

while true; do
    timestamp=$(date '+%Y-%m-%d %H:%M:%S')

    # CPU/メモリ取得
    stats=$(ps -p $(pgrep -f "python bot.py") -o %cpu,%mem --no-headers)

    # ログ出力
    echo "$timestamp - $stats" >> logs/performance.log

    sleep 300  # 5分間隔
done
```

---

## 🚀 スケーリング戦略

### 1. **垂直スケーリング**

#### リソース増強指標
```
CPU使用率 > 70% または メモリ使用率 > 80% が継続する場合
```

**推奨アップグレード**:
- CPU: 1コア → 2コア
- RAM: 1GB → 2GB
- ストレージ: HDD → SSD

### 2. **水平スケーリング**

#### シャーディング対応
```python
# 将来的な実装予定
# 複数インスタンスでのギルド分散処理
```

#### ロードバランシング
```
# 大規模展開時の検討事項
- 複数インスタンス起動
- データベース分散
- キャッシュ層追加
```

---

## 📖 ベストプラクティス

### 1. **開発時の注意点**

#### 非同期処理の活用
```python
# 良い例
async def handle_command(interaction):
    async with self.database.transaction():
        result = await self.database.create_record()

# 悪い例
def handle_command(interaction):
    time.sleep(1)  # ブロッキング操作
```

#### メモリ効率的な処理
```python
# 良い例
async for record in self.database.stream_records():
    await process_record(record)

# 悪い例
all_records = await self.database.get_all_records()
for record in all_records:  # 大量データを一度にメモリに読み込み
    await process_record(record)
```

### 2. **運用時の注意点**

#### 定期メンテナンス
```bash
# 週次メンテナンススクリプト
#!/bin/bash

# データベース最適化
sqlite3 luna.db "VACUUM; ANALYZE;"

# ログローテーション
find logs/ -name "*.log" -mtime +30 -delete

# パフォーマンス統計出力
python performance_report.py
```

#### アラート設定
```bash
# しきい値監視
if [ $(ps -p $PID -o %mem --no-headers | cut -d. -f1) -gt 80 ]; then
    echo "High memory usage detected" | mail admin@example.com
fi
```

---

## 📞 サポート

### パフォーマンス問題の報告

1. **必要情報**:
   - `/ping`コマンドの出力
   - システムリソース使用量
   - エラーログ（直近24時間）
   - サーバー規模（メンバー数、活動量）

2. **連絡先**:
   - GitHub Issues（パフォーマンス関連）
   - [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

### 最適化コンサルティング

大規模サーバー（1000+メンバー）での最適化相談:
- GitHub Discussions
- パフォーマンス分析レポートの提供
- カスタム設定の推奨