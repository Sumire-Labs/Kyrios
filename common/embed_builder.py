import discord
from datetime import datetime
from typing import Optional, Dict, Any, List


class EmbedBuilder:
    """共通のEmbed作成ユーティリティクラス"""

    @staticmethod
    def create_base_embed(
        title: str,
        description: Optional[str] = None,
        color: Optional[discord.Color] = None,
        timestamp: bool = True
    ) -> discord.Embed:
        """基本的なEmbedを作成"""
        embed = discord.Embed(
            title=title,
            description=description,
            color=color or discord.Color.blue()
        )

        if timestamp:
            embed.timestamp = datetime.now()

        return embed

    @staticmethod
    def create_success_embed(
        title: str,
        description: Optional[str] = None,
        timestamp: bool = True
    ) -> discord.Embed:
        """成功メッセージ用のEmbed"""
        return EmbedBuilder.create_base_embed(
            title=f"✅ {title}",
            description=description,
            color=discord.Color.green(),
            timestamp=timestamp
        )

    @staticmethod
    def create_error_embed(
        title: str,
        description: Optional[str] = None,
        timestamp: bool = True
    ) -> discord.Embed:
        """エラーメッセージ用のEmbed"""
        return EmbedBuilder.create_base_embed(
            title=f"❌ {title}",
            description=description,
            color=discord.Color.red(),
            timestamp=timestamp
        )

    @staticmethod
    def create_warning_embed(
        title: str,
        description: Optional[str] = None,
        timestamp: bool = True
    ) -> discord.Embed:
        """警告メッセージ用のEmbed"""
        return EmbedBuilder.create_base_embed(
            title=f"⚠️ {title}",
            description=description,
            color=discord.Color.orange(),
            timestamp=timestamp
        )

    @staticmethod
    def create_info_embed(
        title: str,
        description: Optional[str] = None,
        timestamp: bool = True
    ) -> discord.Embed:
        """情報メッセージ用のEmbed"""
        return EmbedBuilder.create_base_embed(
            title=f"ℹ️ {title}",
            description=description,
            color=discord.Color.blue(),
            timestamp=timestamp
        )

    @staticmethod
    def create_loading_embed(
        title: str,
        description: Optional[str] = None
    ) -> discord.Embed:
        """ローディング用のEmbed"""
        return EmbedBuilder.create_base_embed(
            title=f"🔍 {title}",
            description=description or "処理中です...",
            color=discord.Color.yellow(),
            timestamp=True
        )

    @staticmethod
    def add_user_info_field(
        embed: discord.Embed,
        user: discord.User,
        field_name: str = "👤 ユーザー情報",
        inline: bool = False
    ) -> discord.Embed:
        """ユーザー情報フィールドを追加"""
        value = f"**名前:** {user.display_name}\n"
        value += f"**ID:** `{user.id}`\n"
        value += f"**アカウント作成:** <t:{int(user.created_at.timestamp())}:R>"

        embed.add_field(name=field_name, value=value, inline=inline)
        return embed

    @staticmethod
    def add_performance_fields(
        embed: discord.Embed,
        metrics: Dict[str, Any]
    ) -> discord.Embed:
        """パフォーマンス情報フィールドを追加"""
        if "api_latency" in metrics:
            embed.add_field(
                name="📡 Discord API レイテンシ",
                value=f"**{metrics['api_latency']}ms**",
                inline=True
            )

        if "db_latency" in metrics:
            embed.add_field(
                name="💾 データベースレスポンス",
                value=f"**{metrics['db_latency']}ms**",
                inline=True
            )

        if "cpu_usage" in metrics:
            embed.add_field(
                name="⚙️ CPU使用率",
                value=f"**{metrics['cpu_usage']}%**",
                inline=True
            )

        if "memory_usage" in metrics:
            embed.add_field(
                name="🧠 メモリ使用率",
                value=f"**{metrics['memory_usage']}%**",
                inline=True
            )

        return embed

    @staticmethod
    def add_ticket_info_fields(
        embed: discord.Embed,
        ticket_id: int,
        status: str = "🟢 オープン",
        assigned_to: str = "未割り当て",
        created_at: Optional[datetime] = None
    ) -> discord.Embed:
        """チケット情報フィールドを追加"""
        embed.add_field(name="📝 チケットID", value=f"`{ticket_id}`", inline=True)
        embed.add_field(name="👥 担当者", value=assigned_to, inline=True)
        embed.add_field(name="🔄 ステータス", value=status, inline=True)

        if created_at:
            embed.add_field(
                name="📅 作成日時",
                value=f"<t:{int(created_at.timestamp())}:F>",
                inline=True
            )

        return embed

    @staticmethod
    def set_footer_with_user(
        embed: discord.Embed,
        user: discord.User,
        additional_text: str = "",
        bot_name: str = "Kyrios"
    ) -> discord.Embed:
        """ユーザー情報付きのフッターを設定"""
        footer_text = f"リクエスト: {user.display_name}"
        if additional_text:
            footer_text += f" | {additional_text}"
        footer_text += f" | {bot_name}"

        embed.set_footer(
            text=footer_text,
            icon_url=user.display_avatar.url
        )
        return embed

    @staticmethod
    def create_paginated_embed(
        title: str,
        items: List[str],
        items_per_page: int = 10,
        page: int = 1,
        color: Optional[discord.Color] = None
    ) -> discord.Embed:
        """ページネーション対応のEmbedを作成"""
        total_pages = (len(items) + items_per_page - 1) // items_per_page
        start_idx = (page - 1) * items_per_page
        end_idx = start_idx + items_per_page
        page_items = items[start_idx:end_idx]

        embed = EmbedBuilder.create_base_embed(
            title=f"{title} (ページ {page}/{total_pages})",
            color=color
        )

        description = "\n".join(page_items)
        if description:
            embed.description = description

        embed.set_footer(text=f"総件数: {len(items)} | ページ {page}/{total_pages}")

        return embed