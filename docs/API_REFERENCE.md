# Luna Bot - API リファレンス

## コマンド一覧

Lunaボットで利用可能なすべてのコマンドとその使用方法を説明します。

## 🎵 音楽コマンド

### 音楽再生

#### `/play <query>`
**説明**: 音楽を検索・再生します。インタラクティブな音楽プレイヤーUIを表示

**パラメーター**:
- `query` (必須): YouTube URL / Spotify URL / プレイリストURL / 検索キーワード

**使用方法**:
```
# YouTube URL
/play https://www.youtube.com/watch?v=dQw4w9WgXcQ

# YouTube プレイリスト
/play https://www.youtube.com/playlist?list=PLs4Gp5VU4Fv9rGksKf_XXs1aRV7HdqnyK

# Spotify トラック
/play https://open.spotify.com/track/4iV5W9uYEdYUVa79Axb7Rh

# Spotify プレイリスト
/play https://open.spotify.com/playlist/37i9dQZF1DX0XUsuxWHRQd

# Spotify アルバム
/play https://open.spotify.com/album/1DFixLWuPkv3KT3TnV35m3

# 検索キーワード
/play Never Gonna Give You Up
/play オフィシャル髭男dism Pretender
```

**機能**:

##### 🎵 音楽検索・再生
- **YouTube統合**: yt-dlp による高品質音楽抽出
- **Spotify統合**: Spotify API連携・YouTube変換再生
- **プレイリスト対応**: YouTube/Spotifyプレイリスト一括追加
- **自動音声接続**: ユーザーのボイスチャンネルに自動接続
- **キュー管理**: 複数楽曲の自動キュー追加
- **ループモード**: 楽曲・キューリピート対応

##### 🎮 インタラクティブプレイヤーUI
**統合音楽コントローラー** - 1つのEmbedに全機能を集約

**🎵 再生情報表示**:
- 現在再生中の楽曲情報（タイトル・アーティスト）
- プログレスバー（現在位置/総時間）
- サムネイル表示
- 再生状態（再生中/一時停止）
- ループモード（NONE/TRACK/QUEUE）

**🎛️ Row 1: メイン再生コントロール**
- `⏮️` 前の曲（未実装）
- `⏸️/▶️` 再生/一時停止トグル
- `⏭️` 次の曲（スキップ）
- `🔄` ループモード切り替え
- `⏹️` 停止・切断

**🗂️ Row 2: キュー・追加操作**
- `🗑️ キュークリア` キュー内の全楽曲削除
- `➕ 楽曲追加` 新しい楽曲をキューに追加（モーダル表示）

##### 📋 キュー表示
- 次の3曲のプレビュー表示
- 総キュー数の表示
- リアルタイムキュー更新

**出力例**:
```
🎵 Luna Music Player

🎶 Never Gonna Give You Up
👤 Rick Astley

▰▰▰▰▰▰▱▱▱▱▱▱▱▱▱▱▱▱ 1:23 / 3:32
▶️ 再生中 | 🔄 NONE

📋 次の曲 (2曲キュー待ち)
1. Bohemian Rhapsody
2. Hotel California
```

**インタラクティブUI**:
- 全コントロールボタン（7個）
- 楽曲追加モーダル
- リアルタイム状態更新

**権限**: ボイスチャンネル参加が必要
**制限**: ボイスチャンネル内でのみ使用可能

#### `/stop`
**説明**: 音楽を停止し、ボイスチャンネルから退出します

**使用方法**:
```
/stop
```

**機能**:
- 現在の再生を停止
- キューをクリア
- ボイスチャンネルから切断
- 音楽セッションを終了

**権限**: なし（全ユーザー使用可能）

#### `/loop [mode]`
**説明**: ループモードを設定・切り替えします

**パラメーター**:
- `mode` (オプション): ループモード選択
  - `none` - リピートなし
  - `track` - 楽曲リピート
  - `queue` - キューリピート

**使用方法**:
```
/loop
/loop track
/loop queue
/loop none
```

**機能**:
- **循環切り替え**: パラメーター省略で自動切り替え
- **指定モード設定**: 直接モード指定も可能
- **リアルタイム更新**: プレイヤーUIに即座に反映

**権限**: なし（全ユーザー使用可能）

### 音楽システムの特徴

#### 🏗️ オーバーエンジニアリング設計
- **デザインパターン**: MusicService + MusicPlayer のクリーンアーキテクチャ
- **依存性注入**: DIコンテナによる疎結合設計
- **EventBus統合**: 音楽イベントの一元管理
- **型安全性**: 完全な型ヒント + SQLModelデータベース

#### 📊 データベース統合
- **Track**: 楽曲メタデータ保存
- **Queue**: キュー管理システム
- **MusicSession**: セッション状態管理

#### ⚡ パフォーマンス最適化
- **非ブロッキングI/O**: 完全非同期処理
- **メモリ効率**: 適切なリソース管理
- **エラー回復**: 強固なエラーハンドリング

---

## 基本コマンド

### Ping コマンド

#### `/ping`
**説明**: 高度なレイテンシ測定と包括的なシステム状態確認を行います

**使用方法**:
```
/ping
```

**機能**:
- **Discord APIレイテンシ**: WebSocket接続の応答時間
- **メッセージレスポンス**: インタラクション処理時間
- **データベースレスポンス**: SQLite操作時間
- **システムリソース**: CPU使用率・メモリ使用量
- **EventBus統計**: イベント処理状況・メモリ効率
- **翻訳サービス状態**: DeepL API接続状況・使用量（機能有効時）
- **総合パフォーマンス評価**: 平均レイテンシによる総合判定

**出力例**:
```
🏓 Pong! レイテンシ測定結果

🌐 Discord API レイテンシ: ⚡ 45ms
💬 メッセージレスポンス: ⚡ 123ms
🗄️ データベースレスポンス: ⚡ 12ms ✅ 正常
🔧 CPU使用率: 15.2%
💾 メモリ使用量: 99.8MB
🌐 シャード情報: シャード: 0, サーバー数: 5
📊 イベントバス統計: 処理済み: 1,234, メモリ使用: 10/1000
🌐 翻訳サービス: ✅ 利用可能, 使用率: 2.5%
📊 総合パフォーマンス: ⚡ 優秀, 平均レイテンシ: 60ms
```

**権限**: なし（全ユーザー使用可能）

---

## ユーティリティコマンド

### アバター・バナー表示

#### `/avatar [user]`
**説明**: ユーザーのアバターとバナーを高機能表示・ダウンロード

**パラメーター**:
- `user` (オプション): 対象ユーザー（省略時は実行者）

**使用方法**:
```
/avatar
/avatar @username
/avatar 123456789012345678
```

**機能**:

##### 🖼️ アバター表示
- **複数サイズ対応**: 128px, 256px, 512px, 1024px
- **サーバー専用アバター検出**: グローバルアバターとの差異表示
- **高度な画像解析**:
  - ファイル形式（PNG, JPG, GIF, WebP）
  - ファイルサイズ（バイト単位）
  - 解像度（ピクセル）
  - カラーモード（RGB、RGBA等）
  - アニメーション検出（GIF対応）
  - 主要色抽出（PILベース色解析、16進カラーコード）
  - ノンブロッキング処理（asyncio.to_thread使用）

##### 🎨 バナー表示
- **高解像度表示**: 1024px品質
- **ダウンロードリンク**: 直接ダウンロード可能
- **詳細情報**: 形式・サイズ・主要色

##### 💾 ダウンロード機能
- **マルチサイズダウンロード**: 4つのサイズ別ボタン
- **ワンクリックアクセス**: 直接リンク提供
- **バナーダウンロード**: 存在する場合のみ表示

##### 📊 統計・履歴機能
- **アバター変更統計**:
  - 総変更回数
  - バナー変更回数
  - 初回確認日時
  - 最新変更日時
  - よく使用する画像形式

- **変更履歴**:
  - 最新5件の変更ログ
  - 変更タイプ別分類（アバター/バナー/サーバーアバター）
  - 各変更の主要色・形式記録

##### 🔍 画像解析
- **色彩分析**: 支配的色彩の自動抽出
- **メタデータ取得**: ファイル形式・サイズ等
- **品質評価**: 解像度・圧縮情報

**出力例**:
```
🖼️ UserName のアバター・バナー情報

👤 ユーザー情報
名前: UserName
ID: 123456789012345678
アカウント作成: 2年前

🖼️ アバター詳細
URL: [表示](https://cdn.discordapp.com/...)
形式: PNG
ファイルサイズ: 45,231 bytes
解像度: 1024×1024px
アニメーション: なし
主要色: #3b82f6
```

**インタラクティブUI**:
- `Avatar 128px` `Avatar 256px` `Avatar 512px` `Avatar 1024px` ボタン
- `Banner` ボタン（存在時のみ）
- `📊 統計情報` ボタン
- `📜 履歴` ボタン

**権限**: なし（全ユーザー使用可能）
**クールダウン**: なし
**エフェメラル**: ダウンロード・統計・履歴は個人表示

---

## チケットシステム

### チケットパネル設置

#### `/ticket`
**説明**: チケット作成用のパネルを設置します

**使用方法**:
```
/ticket
```

**権限**: `manage_guild` (サーバー管理権限)

**機能**:
- チケット作成ボタンの設置
- カテゴリ別チケット分類
- 優先度設定機能

### チケット管理UI

#### チケット作成ボタン
**説明**: ユーザーが新しいサポートチケットを作成

**動作**:
1. 専用チャンネルの作成
2. 権限設定（作成者＋管理者のみアクセス）
3. 管理用UIの表示

**制限**:
- 1ユーザーあたり最大3つまで（設定変更可能）
- 適切な権限が必要

#### チケット管理ボタン

##### 🏷️ カテゴリ変更
**説明**: チケットのカテゴリを変更

**利用可能カテゴリ**:
- `technical` - 技術的な問題
- `moderation` - モデレーション関連
- `general` - 一般的な質問
- `other` - その他

##### 👤 アサイン
**説明**: 担当者をチケットに割り当て

**使用方法**:
- ユーザーID入力: `123456789012345678`
- メンション入力: `@username`

##### ⚡ 優先度変更
**説明**: チケットの優先度を設定

**優先度レベル**:
- ⚪ **低** (1) - 一般的な質問
- 🟢 **中** (2) - 標準的な問題（デフォルト）
- 🟡 **高** (3) - 重要な問題
- 🔴 **緊急** (4) - 即座の対応が必要

##### 🔒 クローズ
**説明**: チケットを閉じる

**権限**:
- チケット作成者
- `manage_messages` 権限を持つユーザー

**動作**:
- チケットステータスをクローズに変更
- チャンネル名を `closed-` プレフィックス付きに変更
- アーカイブカテゴリに移動（設定されている場合）

---

## ログシステム

### ログ設定

#### `/logger`
**説明**: 現在のチャンネルをログ出力先に設定

**使用方法**:
```
/logger
```

**権限**: `manage_guild` (サーバー管理権限)

**ログ対象**:
- 📝 メッセージの削除・編集
- 📥📤 メンバーの参加・退出
- 🔨 モデレーション操作（Ban, Kick, Timeout等）
- 🏷️ ロール変更
- 📝🗂️ チャンネル作成・削除

### 自動ログ機能

#### メッセージ削除ログ
**トリガー**: メッセージが削除された時

**情報**:
- 削除されたメッセージ内容
- 作成者情報
- 削除時刻
- チャンネル情報

#### メッセージ編集ログ
**トリガー**: メッセージが編集された時

**情報**:
- 編集前後の内容
- 編集者情報
- 編集時刻
- チャンネル情報

#### メンバー参加ログ
**トリガー**: 新しいメンバーがサーバーに参加

**情報**:
- ユーザー情報
- 参加時刻
- アカウント作成日

#### メンバー退出ログ
**トリガー**: メンバーがサーバーから退出

**情報**:
- ユーザー情報
- 退出時刻
- 在籍期間

---

## イベントシステム

### カスタムイベント

Lunaはイベントドリブンアーキテクチャを採用しており、以下のイベントが自動的に発火されます：

#### Bot関連イベント
- `bot_ready` - ボット起動完了
- `bot_shutdown` - ボット終了
- `guild_join` - サーバー参加
- `guild_remove` - サーバー退出

#### チケット関連イベント
- `ticket_created` - チケット作成
- `ticket_closed` - チケットクローズ
- `ticket_assigned` - 担当者アサイン

#### ログ関連イベント
- `logger_setup` - ログシステム設定
- `message_logged` - メッセージログ記録

---

## エラーハンドリング

### コマンドエラー

#### 権限不足
```
❌ あなたはこのコマンドを実行する権限がありません。
```

#### クールダウン
```
⏰ このコマンドは XX.XX 秒後に使用できます。
```

#### コマンドが見つからない
- ボットは反応しません（ログには記録）

#### 一般的なエラー
```
❌ コマンドの実行中にエラーが発生しました。
```

---

## 設定パラメーター

### config.toml 設定

#### [bot] セクション
```toml
[bot]
token = "YOUR_BOT_TOKEN"              # Discord Bot Token
prefix = "!"                          # コマンドプレフィックス
description = "Luna - Advanced Discord Administration Bot"
```

#### [features] セクション
```toml
[features]
tickets = true                        # チケット機能
logger = true                         # ログ機能
auto_mod = false                     # 自動モデレーション（未実装）
```

#### [tickets] セクション
```toml
[tickets]
category_id = 123456789012345678      # チケットカテゴリID（オプション）
archive_category_id = 876543210987654321  # アーカイブカテゴリID（オプション）
max_per_user = 3                      # 1ユーザーあたりの最大チケット数
```

#### [logger] セクション
```toml
[logger]
ignore_bots = true                    # ボットのアクションを無視
log_edits = true                      # メッセージ編集をログ
log_deletes = true                    # メッセージ削除をログ
log_joins = true                      # メンバー参加をログ
```

---

## 使用例

### 基本的なセットアップ

1. **ログシステム設定**:
   ```
   /logger
   ```

2. **チケットシステム設置**:
   ```
   /ticket
   ```

### チケット管理フロー

1. ユーザーがチケット作成ボタンをクリック
2. 専用チャンネルが自動作成
3. 管理者がカテゴリ・優先度・担当者を設定
4. 問題解決後、チケットをクローズ

### ログ分析

- メッセージ削除・編集の監視
- メンバーの参加・退出パターン分析
- モデレーション操作の履歴確認

---

## 共通ユーティリティ関数 (v0.1.6+)

Luna v0.1.7では、包括的な音楽システムと全cogで使用可能な共通ユーティリティ関数により、一貫したUI/UXとコード品質が実現されています。

### UserFormatter クラス

#### 権限チェック関数

##### `UserFormatter.has_manage_permissions(user) -> bool`
**説明**: ユーザーが管理権限を持っているかチェック

**パラメーター**:
- `user`: discord.User または discord.Member

**戻り値**: bool - 管理権限の有無

**使用例**:
```python
from common import UserFormatter

if UserFormatter.has_manage_permissions(interaction.user):
    # 管理者のみ実行可能な処理
    await handle_admin_action()
else:
    await interaction.response.send_message("❌ 権限が不足しています", ephemeral=True)
```

**チェック対象**:
- `manage_messages` 権限
- `administrator` 権限

#### チャンネル情報フォーマット

##### `UserFormatter.format_channel_name(channel) -> str`
**説明**: チャンネル名を統一フォーマットで表示（#付き）

**パラメーター**:
- `channel`: Discordチャンネルオブジェクト

**戻り値**: str - フォーマット済みチャンネル名

**使用例**:
```python
channel_display = UserFormatter.format_channel_name(channel)
# 出力: "#general" または "チャンネルID: 123456789"
```

##### `UserFormatter.format_channel_info(channel) -> str`
**説明**: チャンネル情報を安全にフォーマット（メンション形式）

**パラメーター**:
- `channel`: Discordチャンネルオブジェクト

**戻り値**: str - メンション可能なチャンネル情報

**使用例**:
```python
channel_ref = UserFormatter.format_channel_info(channel)
# 出力: "<#123456789>" または "#channel-name" または "チャンネルID: 123456789"
```

#### ユーザーID処理

##### `UserFormatter.format_user_id_or_mention(user_input) -> Optional[int]`
**説明**: ユーザーIDまたはメンションから安全にユーザーIDを抽出

**パラメーター**:
- `user_input`: str - ユーザーIDまたはメンション文字列

**戻り値**: Optional[int] - 有効なユーザーID、無効な場合はNone

**対応形式**:
- 直接ID: `"123456789012345678"`
- メンション: `"<@123456789012345678>"`
- ニックネームメンション: `"<@!123456789012345678>"`

**使用例**:
```python
user_id = UserFormatter.format_user_id_or_mention(user_input)
if user_id is None:
    await interaction.response.send_message("❌ 無効なユーザーIDです", ephemeral=True)
    return

user = interaction.guild.get_member(user_id)
```

#### 色変換機能

##### `UserFormatter.safe_color_from_hex(hex_color, fallback_color) -> discord.Color`
**説明**: 16進カラーコードから安全にDiscord.Colorを作成

**パラメーター**:
- `hex_color`: Optional[str] - 16進カラーコード（例：`"#ff0000"`）
- `fallback_color`: discord.Color - 変換失敗時のフォールバック色

**戻り値**: discord.Color - 有効なDiscord色オブジェクト

**使用例**:
```python
from common import UIColors

# アバターの主要色を安全に変換
color = UserFormatter.safe_color_from_hex(
    avatar_info.get('dominant_color'),
    UIColors.AVATAR
)

embed = discord.Embed(title="アバター情報", color=color)
```

**エラーハンドリング**:
- 無効な16進コード → フォールバック色を使用
- None値 → フォールバック色を使用
- 例外発生 → フォールバック色を使用

### 使用方法

これらの共通関数は `common` パッケージからインポートして使用します：

```python
from common import UserFormatter

class YourCog(commands.Cog):
    async def your_command(self, interaction: discord.Interaction):
        # 権限チェック
        if not UserFormatter.has_manage_permissions(interaction.user):
            return await interaction.response.send_message("❌ 権限不足", ephemeral=True)

        # 安全なユーザーID取得
        user_id = UserFormatter.format_user_id_or_mention(user_input)
        if user_id is None:
            return await interaction.response.send_message("❌ 無効なユーザーID", ephemeral=True)

        # チャンネル情報の表示
        channel_name = UserFormatter.format_channel_name(interaction.channel)
```

### メリット

1. **コード統一性**: 全cogで同じロジックを使用
2. **エラーハンドリング**: 一箇所で例外処理を管理
3. **メンテナンス性**: 修正が必要な場合は共通関数のみ更新
4. **型安全性**: 適切な型チェックとバリデーション

---

## 開発者向けAPI

### イベントバス使用例

```python
# カスタムイベントの発火
await self.bot.event_bus.emit_event("custom_event", {
    "user_id": user.id,
    "action": "custom_action",
    "timestamp": datetime.utcnow()
})
```

### データベース操作例

```python
# チケット作成
ticket = await self.bot.database.create_ticket(
    guild_id=guild.id,
    user_id=user.id,
    title="サポートリクエスト"
)

# ログエントリ作成
await self.bot.database.create_log_entry(
    guild_id=guild.id,
    log_type=LogType.MESSAGE_DELETE,
    content="メッセージが削除されました"
)
```

---

## 制限事項

### レート制限
- Discord API制限に準拠
- 連続コマンド実行には制限なし（現在）

### 権限要求
- チケット・ログ機能: サーバー管理権限
- 基本コマンド: 権限不要

### データ保存
- SQLiteデータベース使用
- 自動バックアップ機能
- データ暗号化なし（設定ファイルは要保護）

## サポート

APIの使用方法や追加機能の要望は：
- GitHub Issues
- [CONTRIBUTING.md](CONTRIBUTING.md)
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md)