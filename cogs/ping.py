import discord
from discord import app_commands
from discord.ext import commands
import logging
import time
import asyncio
import psutil
from datetime import datetime


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
        embed_initial = discord.Embed(
            title="🔍 レイテンシ測定中...",
            description="各種レイテンシを測定しています...",
            color=discord.Color.yellow()
        )
        await interaction.followup.send(embed=embed_initial)
        message_latency = round((time.perf_counter() - start_time) * 1000)

        # データベースレスポンス測定
        db_start = time.perf_counter()
        try:
            # 簡単なDB操作でレイテンシ測定
            await self.bot.database.get_guild_settings(ctx.guild.id if ctx.guild else 0)
            db_latency = round((time.perf_counter() - db_start) * 1000)
            db_status = "✅ 正常"
        except Exception as e:
            db_latency = round((time.perf_counter() - db_start) * 1000)
            db_status = f"❌ エラー: {str(e)[:50]}..."

        # システムリソース情報
        cpu_usage = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        memory_usage = memory_info.percent

        # レイテンシ判定
        def get_latency_color(latency):
            if latency < 50:
                return discord.Color.green()
            elif latency < 100:
                return discord.Color.yellow()
            elif latency < 200:
                return discord.Color.orange()
            else:
                return discord.Color.red()

        def get_latency_emoji(latency):
            if latency < 50:
                return "🟢"
            elif latency < 100:
                return "🟡"
            elif latency < 200:
                return "🟠"
            else:
                return "🔴"

        # 最終Embed作成
        embed = discord.Embed(
            title="🏓 高度なレイテンシ測定結果",
            color=get_latency_color(api_latency),
            timestamp=datetime.now()
        )

        embed.add_field(
            name="📡 Discord API レイテンシ",
            value=f"{get_latency_emoji(api_latency)} **{api_latency}ms**",
            inline=True
        )

        embed.add_field(
            name="💬 メッセージレスポンス",
            value=f"{get_latency_emoji(message_latency)} **{message_latency}ms**",
            inline=True
        )

        embed.add_field(
            name="💾 データベースレスポンス",
            value=f"{get_latency_emoji(db_latency)} **{db_latency}ms**\n{db_status}",
            inline=True
        )

        embed.add_field(
            name="⚙️ CPU使用率",
            value=f"**{cpu_usage}%**",
            inline=True
        )

        embed.add_field(
            name="🧠 メモリ使用率",
            value=f"**{memory_usage}%**\n({memory_info.used // 1024 // 1024}MB / {memory_info.total // 1024 // 1024}MB)",
            inline=True
        )

        embed.add_field(
            name="🌐 シャード情報",
            value=f"シャード: **{ctx.guild.shard_id if ctx.guild else 'N/A'}**\nサーバー数: **{len(self.bot.guilds)}**",
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
        if avg_latency < 75:
            performance = "🚀 優秀"
            performance_color = discord.Color.green()
        elif avg_latency < 150:
            performance = "✅ 良好"
            performance_color = discord.Color.yellow()
        elif avg_latency < 250:
            performance = "⚠️ 普通"
            performance_color = discord.Color.orange()
        else:
            performance = "🐌 低速"
            performance_color = discord.Color.red()

        embed.add_field(
            name="📊 総合パフォーマンス",
            value=f"{performance}\n平均レイテンシ: **{round(avg_latency)}ms**",
            inline=False
        )

        embed.color = performance_color
        embed.set_footer(text="Kyrios Performance Monitor", icon_url=self.bot.user.avatar.url if self.bot.user.avatar else None)

        await interaction.edit_original_response(embed=embed)

        # パフォーマンスログ
        self.logger.info(f"Ping command executed - API: {api_latency}ms, Message: {message_latency}ms, DB: {db_latency}ms")


async def setup(bot):
    await bot.add_cog(PingCog(bot))