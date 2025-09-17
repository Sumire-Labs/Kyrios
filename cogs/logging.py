import discord
from discord.ext import commands
from typing import Optional
import logging
from datetime import datetime

from database.models import LogType
from common import EmbedBuilder, LogUtils, UIEmojis, UserFormatter


class LoggingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)
        self.log_channels = {}

    # 共通関数を使用するため、これらのメソッドは削除

    async def send_log(self, guild_id: int, embed: discord.Embed) -> None:
        if guild_id not in self.log_channels:
            settings = await self.bot.database.get_guild_settings(guild_id)
            if settings and settings.log_channel_id:
                self.log_channels[guild_id] = settings.log_channel_id

        if guild_id in self.log_channels:
            channel_id = self.log_channels[guild_id]
            channel = self.bot.get_channel(channel_id)
            if channel:
                try:
                    await channel.send(embed=embed)
                except discord.Forbidden:
                    self.logger.warning(f"No permission to send logs to channel {channel_id}")
                except discord.NotFound:
                    self.logger.warning(f"Log channel {channel_id} not found, removing from cache")
                    del self.log_channels[guild_id]

    @commands.hybrid_command(name="logger", description="このチャンネルをログ出力チャンネルに設定します")
    @commands.has_permissions(manage_guild=True)
    async def setup_logger(self, ctx: commands.Context):
        if not ctx.guild:
            await ctx.send("❌ このコマンドはサーバー内でのみ使用可能です")
            return

        channel = ctx.channel
        guild_id = ctx.guild.id

        if not channel:
            await ctx.send("❌ チャンネルが見つかりません")
            return

        await self.bot.database.create_or_update_guild_settings(
            guild_id=guild_id,
            log_channel_id=channel.id
        )

        self.log_channels[guild_id] = channel.id

        # チャンネル名を安全に取得
        channel_display = getattr(channel, 'mention', None)
        if not channel_display:
            if hasattr(channel, 'name'):
                channel_display = getattr(channel, 'name', 'Unknown Channel')
            else:
                channel_display = f"チャンネルID: {channel.id}"

        embed = EmbedBuilder.create_success_embed(
            "ログシステム設定完了",
            f"このチャンネル ({channel_display}) がログ出力チャンネルに設定されました。"
        )
        embed.add_field(
            name="📝 ログされる内容",
            value="• メッセージの削除・編集\n• メンバーの参加・退出\n• モデレーション操作\n• ロール変更\n• チャンネル作成・削除",
            inline=False
        )
        embed.add_field(
            name="⚙️ 設定",
            value=f"BOTの無視: {'✅' if self.bot.settings.logger_ignore_bots else '❌'}\n編集ログ: {'✅' if self.bot.settings.logger_log_edits else '❌'}\n削除ログ: {'✅' if self.bot.settings.logger_log_deletes else '❌'}\n参加ログ: {'✅' if self.bot.settings.logger_log_joins else '❌'}",
            inline=False
        )

        await ctx.send(embed=embed)

        await self.bot.event_bus.emit_event("logger_setup", {
            "guild_id": guild_id,
            "channel_id": getattr(channel, 'id', None),
            "setup_by": ctx.author.id
        })

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or (self.bot.settings.logger_ignore_bots and message.author.bot):
            return

        if not self.bot.settings.logger_log_deletes:
            return

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.MESSAGE_DELETE)} メッセージ削除",
            color=LogUtils.get_log_color(LogType.MESSAGE_DELETE)
        )
        embed.add_field(name="🏠 チャンネル", value=UserFormatter.format_channel_info(message.channel), inline=True)
        embed.add_field(name=f"{UIEmojis.USER} 送信者", value=UserFormatter.format_user_mention_and_tag(message.author), inline=True)
        embed.add_field(name="🕐 削除時刻", value=UserFormatter.format_timestamp(datetime.now(), "T"), inline=True)

        if message.content:
            embed.add_field(
                name="📝 削除された内容",
                value=UserFormatter.format_code_block(UserFormatter.truncate_text(message.content, 1000)),
                inline=False
            )

        if message.attachments:
            attachment_names = [att.filename for att in message.attachments]
            embed.add_field(
                name="📎 添付ファイル",
                value="\n".join([f"• {name}" for name in attachment_names[:10]]),
                inline=False
            )

        embed.set_footer(text=f"メッセージID: {message.id}")

        await self.send_log(message.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=message.guild.id,
            log_type=LogType.MESSAGE_DELETE,
            action="Message Deleted",
            user_id=message.author.id,
            channel_id=message.channel.id,
            details=f"Content: {message.content[:500] if message.content else 'No content'}"
        )

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or (self.bot.settings.logger_ignore_bots and before.author.bot):
            return

        if not self.bot.settings.logger_log_edits:
            return

        if before.content == after.content:
            return

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.MESSAGE_EDIT)} メッセージ編集",
            color=LogUtils.get_log_color(LogType.MESSAGE_EDIT)
        )
        embed.add_field(name="🏠 チャンネル", value=UserFormatter.format_channel_info(before.channel), inline=True)
        embed.add_field(name=f"{UIEmojis.USER} 編集者", value=UserFormatter.format_user_mention_and_tag(before.author), inline=True)
        embed.add_field(name="🕐 編集時刻", value=UserFormatter.format_timestamp(datetime.now(), "T"), inline=True)

        if before.content:
            embed.add_field(
                name="📝 編集前",
                value=UserFormatter.format_code_block(UserFormatter.truncate_text(before.content, 500)),
                inline=False
            )

        if after.content:
            embed.add_field(
                name="📝 編集後",
                value=UserFormatter.format_code_block(UserFormatter.truncate_text(after.content, 500)),
                inline=False
            )

        embed.add_field(name="🔗 メッセージリンク", value=f"[メッセージに移動]({after.jump_url})", inline=False)
        embed.set_footer(text=f"メッセージID: {before.id}")

        await self.send_log(before.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=before.guild.id,
            log_type=LogType.MESSAGE_EDIT,
            action="Message Edited",
            user_id=before.author.id,
            channel_id=before.channel.id,
            details=f"Before: {before.content[:250] if before.content else 'No content'} | After: {after.content[:250] if after.content else 'No content'}"
        )

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if not self.bot.settings.logger_log_joins:
            return

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.MEMBER_JOIN)} メンバー参加",
            color=LogUtils.get_log_color(LogType.MEMBER_JOIN)
        )
        embed.add_field(name=f"{UIEmojis.USER} ユーザー", value=UserFormatter.format_user_mention_and_tag(member), inline=True)
        embed.add_field(name="🆔 ユーザーID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="📅 アカウント作成日", value=UserFormatter.format_timestamp(member.created_at, "F"), inline=True)
        embed.add_field(name="🕐 参加時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        account_age = datetime.now() - member.created_at
        if account_age.days < 7:
            embed.add_field(name="⚠️ 注意", value="新しいアカウントです", inline=False)
            embed.color = discord.Color.orange()

        embed.set_footer(text=f"総メンバー数: {member.guild.member_count}")

        await self.send_log(member.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=member.guild.id,
            log_type=LogType.MEMBER_JOIN,
            action="Member Joined",
            user_id=member.id,
            details=f"Account created: {member.created_at.isoformat()}"
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.MEMBER_LEAVE)} メンバー退出",
            color=LogUtils.get_log_color(LogType.MEMBER_LEAVE)
        )
        embed.add_field(name=f"{UIEmojis.USER} ユーザー", value=UserFormatter.format_user_mention_and_tag(member), inline=True)
        embed.add_field(name="🆔 ユーザーID", value=f"`{member.id}`", inline=True)
        embed.add_field(name="📅 参加日", value=UserFormatter.format_timestamp(member.joined_at, "F") if member.joined_at else "不明", inline=True)
        embed.add_field(name="🕐 退出時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        if member.roles[1:]:
            roles = [getattr(role, 'mention', role.name) for role in member.roles[1:][:10]]
            embed.add_field(name="🏷️ 所持ロール", value=" ".join(roles), inline=False)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        embed.set_footer(text=f"総メンバー数: {member.guild.member_count}")

        await self.send_log(member.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=member.guild.id,
            log_type=LogType.MEMBER_LEAVE,
            action="Member Left",
            user_id=member.id,
            details=f"Joined at: {member.joined_at.isoformat() if member.joined_at else 'Unknown'}"
        )

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.MEMBER_BAN)} メンバーBAN",
            color=LogUtils.get_log_color(LogType.MEMBER_BAN)
        )
        embed.add_field(name=f"{UIEmojis.USER} 対象", value=UserFormatter.format_user_mention_and_tag(user), inline=True)
        embed.add_field(name="🆔 ユーザーID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="🕐 BAN時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        try:
            ban_info = await guild.fetch_ban(user)
            if ban_info.reason:
                embed.add_field(name="📝 理由", value=ban_info.reason, inline=False)
        except discord.NotFound:
            pass

        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        await self.send_log(guild.id, embed)

        await self.bot.database.create_log(
            guild_id=guild.id,
            log_type=LogType.MEMBER_BAN,
            action="Member Banned",
            user_id=user.id
        )

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.MEMBER_UNBAN)} メンバーBAN解除",
            color=LogUtils.get_log_color(LogType.MEMBER_UNBAN)
        )
        embed.add_field(name=f"{UIEmojis.USER} 対象", value=UserFormatter.format_user_mention_and_tag(user), inline=True)
        embed.add_field(name="🆔 ユーザーID", value=f"`{user.id}`", inline=True)
        embed.add_field(name="🕐 BAN解除時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        if user.avatar:
            embed.set_thumbnail(url=user.avatar.url)

        await self.send_log(guild.id, embed)

        await self.bot.database.create_log(
            guild_id=guild.id,
            log_type=LogType.MEMBER_UNBAN,
            action="Member Unbanned",
            user_id=user.id
        )


async def setup(bot):
    await bot.add_cog(LoggingCog(bot))
