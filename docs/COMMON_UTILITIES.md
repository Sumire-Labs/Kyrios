# Common Utilities - 共通ユーティリティガイド

このドキュメントでは、Lunaの`common/`ディレクトリに配置された共通ユーティリティの使用方法を説明します。

## 📋 目次

1. [EmbedBuilder - Embed作成](#embedbuilder---embed作成)
2. [UIConstants - UI要素管理](#uiconstants---ui要素管理)
3. [UserFormatter - フォーマット機能](#userformatter---フォーマット機能)
4. [ImageAnalyzer - 画像解析](#imageanalyzer---画像解析)

## EmbedBuilder - Embed作成

### 基本的なEmbed作成

```python
from common import EmbedBuilder

# 成功メッセージ
embed = EmbedBuilder.create_success_embed(
    "操作完了",
    "正常に処理されました"
)

# エラーメッセージ
embed = EmbedBuilder.create_error_embed(
    "エラー発生",
    "処理に失敗しました"
)

# 警告メッセージ
embed = EmbedBuilder.create_warning_embed(
    "注意",
    "この操作は元に戻せません"
)

# 情報メッセージ
embed = EmbedBuilder.create_info_embed(
    "お知らせ",
    "新機能が追加されました"
)

# ローディング表示
embed = EmbedBuilder.create_loading_embed(
    "処理中",
    "データを取得しています..."
)
```

### フィールドの追加

```python
# ユーザー情報フィールド
EmbedBuilder.add_user_info_field(embed, user, "👤 対象ユーザー", inline=True)

# パフォーマンス情報フィールド
metrics = {
    "api_latency": 45,
    "db_latency": 12,
    "cpu_usage": 23.5,
    "memory_usage": 67.2
}
EmbedBuilder.add_performance_fields(embed, metrics)

# チケット情報フィールド
EmbedBuilder.add_ticket_info_fields(
    embed,
    ticket_id=123,
    status="🟢 オープン",
    assigned_to="管理者",
    created_at=datetime.now()
)
```

### フッターとページネーション

```python
# ユーザー情報付きフッター
EmbedBuilder.set_footer_with_user(embed, interaction.user, "Luna System")

# ページネーション対応Embed
items = ["項目1", "項目2", "項目3", "..."]
embed = EmbedBuilder.create_paginated_embed(
    "アイテム一覧",
    items,
    items_per_page=5,
    page=1
)
```

## UIConstants - UI要素管理

### 色の統一管理

```python
from common import UIColors

# 基本色
embed.color = UIColors.SUCCESS    # 緑色
embed.color = UIColors.ERROR      # 赤色
embed.color = UIColors.WARNING    # オレンジ色
embed.color = UIColors.INFO       # 青色
embed.color = UIColors.LOADING    # 黄色

# 特殊色
embed.color = UIColors.TICKET     # チケット用
embed.color = UIColors.AVATAR     # アバター用
embed.color = UIColors.PERFORMANCE # パフォーマンス用
```

### 絵文字の統一管理

```python
from common import UIEmojis

# 基本アクション
title = f"{UIEmojis.SUCCESS} 成功"
title = f"{UIEmojis.ERROR} エラー"
title = f"{UIEmojis.WARNING} 警告"
title = f"{UIEmojis.LOADING} 読み込み中"

# システム関連
title = f"{UIEmojis.PING} レイテンシ測定"
title = f"{UIEmojis.CPU} CPU使用率"
title = f"{UIEmojis.MEMORY} メモリ使用率"
title = f"{UIEmojis.DATABASE} データベース"

# ユーザー関連
title = f"{UIEmojis.USER} ユーザー情報"
title = f"{UIEmojis.AVATAR} アバター"
title = f"{UIEmojis.BANNER} バナー"

# チケット関連
title = f"{UIEmojis.TICKET} チケット"
status = f"{UIEmojis.TICKET_OPEN} オープン"
status = f"{UIEmojis.TICKET_CLOSED} クローズ"
```

### パフォーマンス判定

```python
from common import PerformanceUtils

# レイテンシに基づく色・絵文字の自動選択
latency = 45  # ms
color = PerformanceUtils.get_latency_color(latency)
emoji = PerformanceUtils.get_latency_emoji(latency)

# パフォーマンス総合評価
avg_latency = 67.5
performance_text, performance_color = PerformanceUtils.get_performance_rating(avg_latency)
# → ("✅ 良好", discord.Color.yellow())
```

### ログ機能の統合

```python
from common import LogUtils
from database.models import LogType

# ログタイプに応じた色・絵文字の自動取得
log_color = LogUtils.get_log_color(LogType.MEMBER_JOIN)
log_emoji = LogUtils.get_log_emoji(LogType.MEMBER_JOIN)

embed = EmbedBuilder.create_base_embed(
    f"{log_emoji} メンバー参加",
    color=log_color
)
```

### ボタンスタイルの統一

```python
from common import ButtonStyles

class ExampleView(discord.ui.View):
    @discord.ui.button(label="作成", style=ButtonStyles.CREATE)
    async def create_button(self, interaction, button):
        pass

    @discord.ui.button(label="削除", style=ButtonStyles.DELETE)
    async def delete_button(self, interaction, button):
        pass

    @discord.ui.button(label="編集", style=ButtonStyles.EDIT)
    async def edit_button(self, interaction, button):
        pass
```

## UserFormatter - フォーマット機能

### ユーザー情報のフォーマット

```python
from common import UserFormatter

# 基本的なユーザー表示
user_display = UserFormatter.format_user_mention_and_tag(user)
# → "@username\n`User#1234`"

user_id = UserFormatter.format_user_id(user)
# → "`123456789012345678`"

# 詳細なユーザー情報
user_info = UserFormatter.format_user_basic_info(user)
# → "**名前:** DisplayName\n**ID:** `123456789012345678`\n**アカウント作成:** <t:1234567890:R>"

# メンバー情報（サーバー参加日含む）
member_info = UserFormatter.format_member_join_info(member)
```

### 時刻フォーマット

```python
from datetime import datetime

dt = datetime.now()

# 様々なタイムスタンプ形式
short_time = UserFormatter.format_timestamp(dt, "t")      # 16:20
long_time = UserFormatter.format_timestamp(dt, "T")       # 16:20:30
short_date = UserFormatter.format_timestamp(dt, "d")      # 20/04/2021
long_date = UserFormatter.format_timestamp(dt, "D")       # 20 April 2021
short_datetime = UserFormatter.format_timestamp(dt, "f")  # 20 April 2021 16:20
long_datetime = UserFormatter.format_timestamp(dt, "F")   # Tuesday, 20 April 2021 16:20
relative_time = UserFormatter.format_timestamp(dt, "R")   # 2 months ago
```

### データフォーマット

```python
# ファイルサイズ
size_display = UserFormatter.format_file_size(1024000)
# → "1000.0 KB"

# パーセンテージ
percentage = UserFormatter.format_percentage(67.8234, 1)
# → "67.8%"

# 時間間隔
duration = UserFormatter.format_duration(3665)
# → "1時間1分5秒"

# テキスト切り詰め
truncated = UserFormatter.truncate_text("長いテキスト...", 10)
# → "長いテキスト..."

# コードブロック
code_block = UserFormatter.format_code_block("print('hello')", "python")
# → "```python\nprint('hello')\n```"

# インラインコード
inline_code = UserFormatter.format_inline_code("variable")
# → "`variable`"
```

### ロール表示

```python
# ロール一覧のフォーマット（最大10個まで）
role_display = UserFormatter.format_role_list(member.roles, max_roles=5)
# → "@Role1 @Role2 @Role3 (+2個)"
```

### アカウント年数警告

```python
# 新規アカウントの警告メッセージ
warning = UserFormatter.format_account_age_warning(user, threshold_days=7)
if warning:
    embed.add_field(name="⚠️ 注意", value=warning, inline=False)
```

### ユーザーID抽出

```python
# メンションまたはIDからユーザーIDを抽出
user_id = UserFormatter.format_user_id_or_mention("<@123456789012345678>")
# → 123456789012345678

user_id = UserFormatter.format_user_id_or_mention("123456789012345678")
# → 123456789012345678
```

## ImageAnalyzer - 画像解析

```python
from common import ImageAnalyzer

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.image_analyzer = ImageAnalyzer()

    async def analyze_user_avatar(self, user):
        # 非同期画像解析
        avatar_info = await self.image_analyzer.analyze_image(user.avatar.url)

        return {
            'format': avatar_info.get('format'),           # 'png', 'jpg', etc.
            'size': avatar_info.get('size'),              # ファイルサイズ（bytes）
            'dimensions': avatar_info.get('dimensions'),   # (width, height)
            'dominant_color': avatar_info.get('dominant_color'),  # '#FF0000'
            'animated': avatar_info.get('animated')        # True/False
        }
```

## 統合使用例

### 完全なCogの実装例

```python
from discord.ext import commands
from discord import app_commands
import discord
from common import (
    EmbedBuilder, UIColors, UIEmojis, UserFormatter,
    ButtonStyles, PerformanceUtils
)

class ExampleCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="userinfo", description="ユーザー情報を表示")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        target = user or interaction.user

        # ローディング表示
        loading_embed = EmbedBuilder.create_loading_embed(
            "ユーザー情報取得中",
            f"{target.mention} の情報を取得しています..."
        )
        await interaction.response.send_message(embed=loading_embed, ephemeral=True)

        try:
            # メイン情報Embed作成
            embed = EmbedBuilder.create_info_embed(
                f"{UIEmojis.USER} ユーザー情報",
                f"{target.mention} の詳細情報"
            )

            # ユーザー基本情報を追加
            EmbedBuilder.add_user_info_field(embed, target)

            # ロール情報
            role_info = UserFormatter.format_role_list(target.roles)
            embed.add_field(name="🏷️ ロール", value=role_info, inline=False)

            # アカウント年数警告
            warning = UserFormatter.format_account_age_warning(target)
            if warning:
                embed.add_field(name="⚠️ 注意", value=warning, inline=False)

            # フッター設定
            EmbedBuilder.set_footer_with_user(embed, interaction.user, "User Info System")

            # サムネイル設定
            embed.set_thumbnail(url=target.display_avatar.url)

            await interaction.edit_original_response(embed=embed)

        except Exception as e:
            # エラー処理
            error_embed = EmbedBuilder.create_error_embed(
                "情報取得失敗",
                f"ユーザー情報の取得に失敗しました: {str(e)[:100]}"
            )
            await interaction.edit_original_response(embed=error_embed)

async def setup(bot):
    await bot.add_cog(ExampleCog(bot))
```

## 開発のベストプラクティス

1. **統一性の維持**: 常に共通関数を使用してUI一貫性を保つ
2. **適切な色選択**: 操作の性質に応じて適切な色を選択
3. **エラーハンドリング**: 統一されたエラー表示パターンを使用
4. **ユーザビリティ**: 予測可能で一貫したインターフェース設計
5. **保守性**: 共通関数の変更で全機能に反映される設計

これらのユーティリティを活用することで、保守性が高く、一貫性のある機能を効率的に開発できます。