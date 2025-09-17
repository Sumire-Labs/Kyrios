import discord
from discord import app_commands
from discord.ext import commands
import logging
import time
import asyncio
import psutil
from datetime import datetime

from common import EmbedBuilder, PerformanceUtils, UIEmojis, UserFormatter


class PingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @app_commands.command(name="ping", description="高度なレイテンシ測定を行います")
    async def ping(self, interaction: discord.Interaction):
        # Discord APIレイテンシ
        api_latency = round(self.bot.latency * 1000)

        # インタラクションレスポンス測定
        await interaction.response.defer()
        start_time = time.perf_counter()
        embed_initial = EmbedBuilder.create_loading_embed(
            "レイテンシ測定中",
            "各種レイテンシを測定しています..."
        )
        await interaction.followup.send(embed=embed_initial)
        message_latency = round((time.perf_counter() - start_time) * 1000)

        # データベースレスポンス測定
        db_start = time.perf_counter()
        try:
            # 簡単なDB操作でレイテンシ測定
            await self.bot.database.get_guild_settings(interaction.guild.id if interaction.guild else 0)
            db_latency = round((time.perf_counter() - db_start) * 1000)
            db_status = "✅ 正常"
        except Exception as e:
            db_latency = round((time.perf_counter() - db_start) * 1000)
            db_status = f"❌ エラー: {str(e)[:50]}..."

        # システムリソース情報
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent

        # レイテンシ判定は共通関数を使用

        # 最終Embed作成
        embed = EmbedBuilder.create_base_embed(
            title=f"{UIEmojis.PING} 高度なレイテンシ測定結果",
            color=PerformanceUtils.get_latency_color(api_latency)
        )

        embed.add_field(
            name=f"{UIEmojis.NETWORK} Discord API レイテンシ",
            value=f"{PerformanceUtils.get_latency_emoji(api_latency)} **{api_latency}ms**",
            inline=True
        )

        embed.add_field(
            name="💬 メッセージレスポンス",
            value=f"{PerformanceUtils.get_latency_emoji(message_latency)} **{message_latency}ms**",
            inline=True
        )

        embed.add_field(
            name=f"{UIEmojis.DATABASE} データベースレスポンス",
            value=f"{PerformanceUtils.get_latency_emoji(db_latency)} **{db_latency}ms**\n{db_status}",
            inline=True
        )

        embed.add_field(
            name=f"{UIEmojis.CPU} CPU使用率",
            value=f"**{UserFormatter.format_percentage(cpu_usage)}**",
            inline=True
        )

        embed.add_field(
            name=f"{UIEmojis.MEMORY} メモリ使用率",
            value=f"**{UserFormatter.format_percentage(memory_usage)}**\n({UserFormatter.format_file_size(memory_info.used)} / {UserFormatter.format_file_size(memory_info.total)})",
            inline=True
        )

        embed.add_field(
            name="🌐 シャード情報",
            value=f"シャード: **{interaction.guild.shard_id if interaction.guild else 'N/A'}**\nサーバー数: **{len(self.bot.guilds)}**",
            inline=True
        )

        # EventBus メモリ統計
        try:
            event_stats = self.bot.event_bus.get_memory_stats()
            embed.add_field(
                name="📊 イベントバス統計",
                value=f"**処理済み:** {event_stats['total_events_processed']:,}\n**メモリ使用:** {event_stats['memory_efficiency']}\n**破棄済み:** {event_stats['events_discarded']:,}",
                inline=True
            )
        except Exception:
            pass

        # パフォーマンス総評
        avg_latency = (api_latency + message_latency + db_latency) / 3
        performance, performance_color = PerformanceUtils.get_performance_rating(avg_latency)

        embed.add_field(
            name="📊 総合パフォーマンス",
            value=f"{performance}\n平均レイテンシ: **{round(avg_latency)}ms**",
            inline=False
        )

        embed.color = performance_color
        EmbedBuilder.set_footer_with_user(embed, interaction.user, "Performance Monitor")

        await interaction.edit_original_response(embed=embed)

        # パフォーマンスログ
        self.logger.info(f"Ping command executed - API: {api_latency}ms, Message: {message_latency}ms, DB: {db_latency}ms")


async def setup(bot):
    await bot.add_cog(PingCog(bot))