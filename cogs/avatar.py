# type: ignore
import discord
from discord import app_commands
from discord.ext import commands
import logging
import aiohttp
import asyncio
from datetime import datetime
from typing import Optional, Union, List, Tuple

from database.models import AvatarHistoryType
from common import ImageAnalyzer, EmbedBuilder, UIColors, UIEmojis, UserFormatter, ButtonStyles


class AvatarDownloadView(discord.ui.View):
    """アバター・バナーダウンロード用のUI"""

    def __init__(self, user: Union[discord.User, discord.Member], avatar_url: str, banner_url: Optional[str] = None):
        super().__init__(timeout=300)
        self.user = user
        self.avatar_url = avatar_url
        self.banner_url = banner_url
        self._setup_buttons()

    def _setup_buttons(self):
        """ボタンを動的にセットアップ"""
        # アバターダウンロードボタン（複数サイズ）
        sizes = [128, 256, 512, 1024]
        for size in sizes:
            button = discord.ui.Button(
                label=f"Avatar {size}px",
                style=discord.ButtonStyle.primary,
                custom_id=f"avatar_{size}",
                emoji="🖼️"
            )
            button.callback = self._create_avatar_callback(size)
            self.add_item(button)

        # バナーダウンロードボタン（存在する場合）
        if self.banner_url:
            banner_button = discord.ui.Button(
                label="Banner",
                style=discord.ButtonStyle.secondary,
                custom_id="banner",
                emoji="🎨"
            )
            banner_button.callback = self._banner_callback
            self.add_item(banner_button)

    def _create_avatar_callback(self, size: int):
        async def callback(interaction: discord.Interaction):
            await interaction.response.defer(ephemeral=True)

            try:
                # 指定サイズのアバターURLを生成
                sized_url = self.avatar_url.replace('1024', str(size)) if '1024' in self.avatar_url else f"{self.avatar_url}?size={size}"

                embed = discord.Embed(
                    title=f"🖼️ {self.user.display_name} のアバター ({size}px)",
                    color=discord.Color.blue(),
                    timestamp=datetime.now()
                )
                embed.set_image(url=sized_url)
                embed.add_field(name="💾 ダウンロードURL", value=f"[クリックしてダウンロード]({sized_url})", inline=False)
                embed.add_field(name="📏 サイズ", value=f"{size}×{size}px", inline=True)

                await interaction.followup.send(embed=embed, ephemeral=True)

            except Exception as e:
                await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)

        return callback

    async def _banner_callback(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        try:
            embed = discord.Embed(
                title=f"🎨 {self.user.display_name} のバナー",
                color=discord.Color.purple(),
                timestamp=datetime.now()
            )
            embed.set_image(url=self.banner_url)
            embed.add_field(name="💾 ダウンロードURL", value=f"[クリックしてダウンロード]({self.banner_url})", inline=False)

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ エラーが発生しました: {str(e)}", ephemeral=True)


class AvatarHistoryView(discord.ui.View):
    """アバター履歴表示用のUI"""

    def __init__(self, bot, user: Union[discord.User, discord.Member]):
        super().__init__(timeout=300)
        self.bot = bot
        self.user = user

    @discord.ui.button(label="📈 統計情報", style=discord.ButtonStyle.primary, emoji="📊")
    async def show_stats(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        try:
            stats = await self.bot.database.get_user_avatar_stats(self.user.id)

            embed = discord.Embed(
                title=f"📊 {self.user.display_name} のアバター統計",
                color=discord.Color.gold(),
                timestamp=datetime.now()
            )

            if stats:
                embed.add_field(name="🖼️ アバター変更回数", value=f"{stats.total_avatar_changes}回", inline=True)
                embed.add_field(name="🎨 バナー変更回数", value=f"{stats.total_banner_changes}回", inline=True)
                embed.add_field(name="👀 初回確認", value=f"<t:{int(stats.first_seen.timestamp())}:F>", inline=True)

                if stats.last_avatar_change:
                    embed.add_field(name="🖼️ 最新アバター変更", value=f"<t:{int(stats.last_avatar_change.timestamp())}:R>", inline=True)

                if stats.last_banner_change:
                    embed.add_field(name="🎨 最新バナー変更", value=f"<t:{int(stats.last_banner_change.timestamp())}:R>", inline=True)

                if stats.most_used_format:
                    embed.add_field(name="💾 よく使う形式", value=stats.most_used_format.upper(), inline=True)
            else:
                embed.description = "このユーザーの統計データがありません。"

            embed.set_thumbnail(url=self.user.display_avatar.url)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ 統計情報の取得でエラーが発生しました: {str(e)}", ephemeral=True)

    @discord.ui.button(label="📜 履歴", style=discord.ButtonStyle.secondary, emoji="🕐")
    async def show_history(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(ephemeral=True)

        try:
            history = await self.bot.database.get_avatar_history(self.user.id, limit=5)

            embed = discord.Embed(
                title=f"📜 {self.user.display_name} のアバター履歴",
                color=discord.Color.blurple(),
                timestamp=datetime.now()
            )

            if history:
                for i, entry in enumerate(history[:5], 1):
                    type_emoji = {
                        AvatarHistoryType.AVATAR_CHANGE: "🖼️",
                        AvatarHistoryType.BANNER_CHANGE: "🎨",
                        AvatarHistoryType.SERVER_AVATAR_CHANGE: "🏠"
                    }.get(entry.history_type, "❓")

                    type_name = {
                        AvatarHistoryType.AVATAR_CHANGE: "アバター変更",
                        AvatarHistoryType.BANNER_CHANGE: "バナー変更",
                        AvatarHistoryType.SERVER_AVATAR_CHANGE: "サーバーアバター変更"
                    }.get(entry.history_type, "不明")

                    value = f"<t:{int(entry.timestamp.timestamp())}:R>"
                    if entry.dominant_color:
                        value += f" • 主要色: `{entry.dominant_color}`"
                    if entry.image_format:
                        value += f" • 形式: `{entry.image_format.upper()}`"

                    embed.add_field(
                        name=f"{type_emoji} {i}. {type_name}",
                        value=value,
                        inline=False
                    )
            else:
                embed.description = "このユーザーのアバター履歴がありません。"

            embed.set_thumbnail(url=self.user.display_avatar.url)
            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(f"❌ 履歴の取得でエラーが発生しました: {str(e)}", ephemeral=True)


class AvatarCog(commands.Cog):
    def __init__(self, bot, database=None, event_bus=None, config=None):
        self.bot = bot
        self.database = database or bot.database
        self.event_bus = event_bus or bot.event_bus
        self.config = config or bot.settings
        self.logger = logging.getLogger(__name__)
        self.image_analyzer = ImageAnalyzer()

    @app_commands.command(name="avatar", description="🖼️ ユーザーのアバターとバナーを高機能表示します")
    @app_commands.describe(user="アバターを表示するユーザー（省略時は自分）")
    async def avatar(self, interaction: discord.Interaction, user: Optional[discord.Member] = None):
        target_user = user or interaction.user
        await interaction.response.defer()

        try:
            # ユーザー情報を取得（必要に応じてAPIから）
            if hasattr(target_user, 'id'):
                try:
                    # より詳細な情報を取得するためにAPIから再取得
                    fetched_user = await self.bot.fetch_user(target_user.id)
                except:
                    fetched_user = target_user
            else:
                fetched_user = target_user

            # アバターとバナーのURL取得
            avatar_url = target_user.display_avatar.with_size(1024).url
            global_avatar_url = target_user.avatar.with_size(1024).url if target_user.avatar else None
            banner_url = fetched_user.banner.with_size(1024).url if fetched_user.banner else None

            # 画像解析
            avatar_info = await self.image_analyzer.analyze_image(avatar_url)
            banner_info = {}
            if banner_url:
                banner_info = await self.image_analyzer.analyze_image(banner_url)

            # メインEmbed作成
            embed = discord.Embed(
                title=f"🖼️ {target_user.display_name} のアバター・バナー情報",
                color=discord.Color.from_str(avatar_info.get('dominant_color', '#808080')),
                timestamp=datetime.now()
            )

            # ユーザー基本情報
            embed.add_field(
                name="👤 ユーザー情報",
                value=f"**名前:** {target_user.display_name}\n**ID:** `{target_user.id}`\n**アカウント作成:** <t:{int(target_user.created_at.timestamp())}:R>",
                inline=False
            )

            # アバター情報
            avatar_value = f"**URL:** [表示]({avatar_url})\n"
            if avatar_info:
                if avatar_info.get('format'):
                    avatar_value += f"**形式:** {avatar_info['format'].upper()}\n"
                if avatar_info.get('size'):
                    avatar_value += f"**ファイルサイズ:** {avatar_info['size']:,} bytes\n"
                if avatar_info.get('dimensions'):
                    avatar_value += f"**解像度:** {avatar_info['dimensions'][0]}×{avatar_info['dimensions'][1]}px\n"
                if avatar_info.get('animated'):
                    avatar_value += f"**アニメーション:** {'あり' if avatar_info['animated'] else 'なし'}\n"
                if avatar_info.get('dominant_color'):
                    avatar_value += f"**主要色:** `{avatar_info['dominant_color']}`"

            embed.add_field(name="🖼️ アバター詳細", value=avatar_value, inline=True)

            # サーバーアバターとグローバルアバターが異なる場合
            if isinstance(target_user, discord.Member) and target_user.guild_avatar and global_avatar_url != avatar_url:
                embed.add_field(
                    name="🏠 サーバー専用アバター",
                    value=f"このユーザーはこのサーバー専用のアバターを使用中\n**グローバル:** [表示]({global_avatar_url})",
                    inline=True
                )

            # バナー情報
            if banner_url and banner_info:
                banner_value = f"**URL:** [表示]({banner_url})\n"
                if banner_info.get('format'):
                    banner_value += f"**形式:** {banner_info['format'].upper()}\n"
                if banner_info.get('size'):
                    banner_value += f"**ファイルサイズ:** {banner_info['size']:,} bytes\n"
                if banner_info.get('dimensions'):
                    banner_value += f"**解像度:** {banner_info['dimensions'][0]}×{banner_info['dimensions'][1]}px\n"
                if banner_info.get('dominant_color'):
                    banner_value += f"**主要色:** `{banner_info['dominant_color']}`"

                embed.add_field(name="🎨 バナー詳細", value=banner_value, inline=True)
            else:
                embed.add_field(name="🎨 バナー", value="このユーザーはバナーを設定していません", inline=True)

            # メイン画像設定
            embed.set_image(url=avatar_url)
            if banner_url:
                embed.set_thumbnail(url=banner_url)

            embed.set_footer(
                text=f"リクエスト: {interaction.user.display_name} | Kyrios Avatar System",
                icon_url=interaction.user.display_avatar.url
            )

            # UI作成
            download_view = AvatarDownloadView(target_user, avatar_url, banner_url)
            history_view = AvatarHistoryView(self.bot, target_user)

            # ビューを結合
            combined_view = discord.ui.View(timeout=300)

            # ダウンロードボタン追加
            for item in download_view.children[:4]:  # アバターボタンのみ
                combined_view.add_item(item)

            if banner_url:
                for item in download_view.children[4:]:  # バナーボタン
                    combined_view.add_item(item)

            # 履歴ボタン追加
            for item in history_view.children:
                combined_view.add_item(item)

            await interaction.followup.send(embed=embed, view=combined_view)

            # イベント発火
            await self.event_bus.emit_event("avatar_command_used", {
                "user_id": interaction.user.id,
                "target_user_id": target_user.id,
                "guild_id": interaction.guild.id if interaction.guild else None,
                "has_banner": banner_url is not None
            })

            # アバター情報をデータベースに記録
            if avatar_info:
                await self.database.record_avatar_change(
                    user_id=target_user.id,
                    history_type=AvatarHistoryType.AVATAR_CHANGE,
                    new_avatar_url=avatar_url,
                    guild_id=interaction.guild.id if interaction.guild and isinstance(target_user, discord.Member) and target_user.guild_avatar else None,
                    dominant_color=avatar_info.get('dominant_color'),
                    image_format=avatar_info.get('format'),
                    image_size=avatar_info.get('size')
                )

        except Exception as e:
            self.logger.error(f"Avatar command error: {e}", exc_info=True)
            error_embed = discord.Embed(
                title="❌ エラー",
                description="アバター情報の取得中にエラーが発生しました。",
                color=discord.Color.red()
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(AvatarCog(bot))
