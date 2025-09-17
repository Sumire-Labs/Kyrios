import discord
from discord.ext import commands
from typing import Optional
import logging
from datetime import datetime

from database.models import LogType
from common import EmbedBuilder, LogUtils, UIEmojis, UIColors, UserFormatter


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
            value="**メッセージ関連**\n• メッセージの削除・編集\n\n**メンバー関連**\n• メンバーの参加・退出・BAN・キック\n\n**チャンネル関連**\n• チャンネル作成・削除・編集\n\n**ロール関連**\n• ロール作成・削除・更新\n\n**サーバー関連**\n• サーバー設定変更・絵文字更新\n\n**システム関連**\n• WebSocket接続・切断・再接続\n• BOT起動・シャットダウン",
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
        embed.add_field(name="🆔 ユーザーID", value=UserFormatter.format_id(member.id), inline=True)
        embed.add_field(name="📅 アカウント作成日", value=UserFormatter.format_timestamp(member.created_at, "F"), inline=True)
        embed.add_field(name="🕐 参加時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        if member.avatar:
            embed.set_thumbnail(url=member.avatar.url)

        account_age = datetime.now() - member.created_at
        if account_age.days < 7:
            embed.add_field(name="⚠️ 注意", value="新しいアカウントです", inline=False)
            embed.color = UIColors.WARNING

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
        embed.add_field(name="🆔 ユーザーID", value=UserFormatter.format_id(member.id), inline=True)
        embed.add_field(name="📅 参加日", value=UserFormatter.format_timestamp(member.joined_at, "F") if member.joined_at else "不明", inline=True)
        embed.add_field(name="🕐 退出時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        if member.roles[1:]:
            role_list = UserFormatter.format_role_list(member.roles[1:], 10)
            embed.add_field(name="🏷️ 所持ロール", value=role_list, inline=False)

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
        embed.add_field(name="🆔 ユーザーID", value=UserFormatter.format_id(user.id), inline=True)
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
        embed.add_field(name="🆔 ユーザーID", value=UserFormatter.format_id(user.id), inline=True)
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

    # ===== チャンネル関連イベント =====

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        """チャンネル作成イベント"""
        if not hasattr(channel, 'guild') or not channel.guild:
            return

        # チャンネルタイプを判定
        channel_type_map = {
            discord.TextChannel: "テキストチャンネル",
            discord.VoiceChannel: "ボイスチャンネル",
            discord.CategoryChannel: "カテゴリ",
            discord.ForumChannel: "フォーラムチャンネル",
            discord.StageChannel: "ステージチャンネル",
            discord.Thread: "スレッド"
        }
        channel_type = channel_type_map.get(type(channel), "不明なチャンネル")

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.CHANNEL_CREATE)} チャンネル作成",
            color=LogUtils.get_log_color(LogType.CHANNEL_CREATE)
        )
        embed.add_field(name="📝 チャンネル名", value=UserFormatter.format_channel_name(channel), inline=True)
        embed.add_field(name="🆔 チャンネルID", value=UserFormatter.format_id(channel.id), inline=True)
        embed.add_field(name="📋 タイプ", value=channel_type, inline=True)
        embed.add_field(name="🕐 作成時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        # カテゴリ情報
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="📁 カテゴリ", value=channel.category.name, inline=True)

        # ポジション情報
        if hasattr(channel, 'position'):
            embed.add_field(name="📍 ポジション", value=str(channel.position), inline=True)

        await self.send_log(channel.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=channel.guild.id,
            log_type=LogType.CHANNEL_CREATE,
            action="Channel Created",
            channel_id=channel.id,
            details=f"Name: {getattr(channel, 'name', 'Unknown')}, Type: {channel_type}, Position: {getattr(channel, 'position', 'N/A')}"
        )

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        """チャンネル削除イベント"""
        if not hasattr(channel, 'guild') or not channel.guild:
            return

        # チャンネルタイプを判定
        channel_type_map = {
            discord.TextChannel: "テキストチャンネル",
            discord.VoiceChannel: "ボイスチャンネル",
            discord.CategoryChannel: "カテゴリ",
            discord.ForumChannel: "フォーラムチャンネル",
            discord.StageChannel: "ステージチャンネル",
            discord.Thread: "スレッド"
        }
        channel_type = channel_type_map.get(type(channel), "不明なチャンネル")

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.CHANNEL_DELETE)} チャンネル削除",
            color=LogUtils.get_log_color(LogType.CHANNEL_DELETE)
        )
        embed.add_field(name="📝 チャンネル名", value=UserFormatter.format_channel_name(channel), inline=True)
        embed.add_field(name="🆔 チャンネルID", value=UserFormatter.format_id(channel.id), inline=True)
        embed.add_field(name="📋 タイプ", value=channel_type, inline=True)
        embed.add_field(name="🕐 削除時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        # カテゴリ情報
        if hasattr(channel, 'category') and channel.category:
            embed.add_field(name="📁 カテゴリ", value=channel.category.name, inline=True)

        # ポジション情報
        if hasattr(channel, 'position'):
            embed.add_field(name="📍 ポジション", value=str(channel.position), inline=True)

        await self.send_log(channel.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=channel.guild.id,
            log_type=LogType.CHANNEL_DELETE,
            action="Channel Deleted",
            channel_id=channel.id,
            details=f"Name: {getattr(channel, 'name', 'Unknown')}, Type: {channel_type}, Position: {getattr(channel, 'position', 'N/A')}"
        )

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before, after):
        """チャンネル更新イベント"""
        if not hasattr(before, 'guild') or not before.guild:
            return

        changes = []

        # 名前変更チェック
        if before.name != after.name:
            changes.append(f"名前: `{before.name}` → `{after.name}`")

        # トピック変更チェック（テキストチャンネル）
        if hasattr(before, 'topic') and hasattr(after, 'topic'):
            if before.topic != after.topic:
                before_topic = before.topic or "なし"
                after_topic = after.topic or "なし"
                changes.append(f"トピック: `{UserFormatter.truncate_text(before_topic, 50)}` → `{UserFormatter.truncate_text(after_topic, 50)}`")

        # ポジション変更チェック
        if hasattr(before, 'position') and hasattr(after, 'position'):
            if before.position != after.position:
                changes.append(f"ポジション: `{before.position}` → `{after.position}`")

        # カテゴリ変更チェック
        if hasattr(before, 'category') and hasattr(after, 'category'):
            if before.category != after.category:
                before_category = before.category.name if before.category else "なし"
                after_category = after.category.name if after.category else "なし"
                changes.append(f"カテゴリ: `{before_category}` → `{after_category}`")

        # nsfw設定変更チェック（テキストチャンネル）
        if hasattr(before, 'nsfw') and hasattr(after, 'nsfw'):
            if before.nsfw != after.nsfw:
                changes.append(f"NSFW: `{before.nsfw}` → `{after.nsfw}`")

        # slowmode変更チェック（テキストチャンネル）
        if hasattr(before, 'slowmode_delay') and hasattr(after, 'slowmode_delay'):
            if before.slowmode_delay != after.slowmode_delay:
                changes.append(f"低速モード: `{before.slowmode_delay}秒` → `{after.slowmode_delay}秒`")

        # 変更がない場合は終了
        if not changes:
            return

        # チャンネルタイプを判定
        channel_type_map = {
            discord.TextChannel: "テキストチャンネル",
            discord.VoiceChannel: "ボイスチャンネル",
            discord.CategoryChannel: "カテゴリ",
            discord.ForumChannel: "フォーラムチャンネル",
            discord.StageChannel: "ステージチャンネル",
            discord.Thread: "スレッド"
        }
        channel_type = channel_type_map.get(type(after), "不明なチャンネル")

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.CHANNEL_UPDATE)} チャンネル更新",
            color=LogUtils.get_log_color(LogType.CHANNEL_UPDATE)
        )
        embed.add_field(name="📝 チャンネル", value=f"{after.mention} (`{after.name}`)", inline=True)
        embed.add_field(name="🆔 チャンネルID", value=UserFormatter.format_id(after.id), inline=True)
        embed.add_field(name="📋 タイプ", value=channel_type, inline=True)
        embed.add_field(name="🕐 更新時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        # 変更内容を表示
        embed.add_field(
            name="📝 変更内容",
            value="\n".join([f"• {change}" for change in changes[:10]]),  # 最大10項目
            inline=False
        )

        await self.send_log(after.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=after.guild.id,
            log_type=LogType.CHANNEL_UPDATE,
            action="Channel Updated",
            channel_id=after.id,
            details=f"Changes: {', '.join(changes[:5])}"  # データベースには最大5項目
        )

    # ===== WebSocket関連イベント =====

    @commands.Cog.listener()
    async def on_connect(self):
        """WebSocket接続イベント"""
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.WEBSOCKET_CONNECT)} WebSocket接続",
            color=LogUtils.get_log_color(LogType.WEBSOCKET_CONNECT)
        )
        embed.add_field(name="🔗 ステータス", value="Discordに接続しました", inline=True)
        embed.add_field(name="🕐 接続時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)
        embed.add_field(name="🤖 BOT情報", value=UserFormatter.format_user_mention_and_tag(self.bot.user), inline=True)

        # 全てのサーバーにログ送信
        for guild in self.bot.guilds:
            await self.send_log(guild.id, embed)
            await self.bot.database.create_log(
                guild_id=guild.id,
                log_type=LogType.WEBSOCKET_CONNECT,
                action="WebSocket Connected",
                details=f"Bot: {self.bot.user.name}#{self.bot.user.discriminator}"
            )

    @commands.Cog.listener()
    async def on_disconnect(self):
        """WebSocket切断イベント"""
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.WEBSOCKET_DISCONNECT)} WebSocket切断",
            color=LogUtils.get_log_color(LogType.WEBSOCKET_DISCONNECT)
        )
        embed.add_field(name="🔌 ステータス", value="Discordから切断されました", inline=True)
        embed.add_field(name="🕐 切断時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)
        embed.add_field(name="🤖 BOT情報", value=UserFormatter.format_user_mention_and_tag(self.bot.user), inline=True)

        # 全てのサーバーにログ送信
        for guild in self.bot.guilds:
            await self.send_log(guild.id, embed)
            await self.bot.database.create_log(
                guild_id=guild.id,
                log_type=LogType.WEBSOCKET_DISCONNECT,
                action="WebSocket Disconnected",
                details=f"Bot: {self.bot.user.name}#{self.bot.user.discriminator}"
            )

    @commands.Cog.listener()
    async def on_resumed(self):
        """WebSocket再接続イベント"""
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.WEBSOCKET_RECONNECT)} WebSocket再接続",
            color=LogUtils.get_log_color(LogType.WEBSOCKET_RECONNECT)
        )
        embed.add_field(name="🔄 ステータス", value="Discordに再接続しました", inline=True)
        embed.add_field(name="🕐 再接続時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)
        embed.add_field(name="🤖 BOT情報", value=UserFormatter.format_user_mention_and_tag(self.bot.user), inline=True)

        # 全てのサーバーにログ送信
        for guild in self.bot.guilds:
            await self.send_log(guild.id, embed)
            await self.bot.database.create_log(
                guild_id=guild.id,
                log_type=LogType.WEBSOCKET_RECONNECT,
                action="WebSocket Reconnected",
                details=f"Bot: {self.bot.user.name}#{self.bot.user.discriminator}"
            )

    # ===== ロール関連イベント =====

    @commands.Cog.listener()
    async def on_guild_role_create(self, role):
        """ロール作成イベント"""
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.ROLE_CREATE)} ロール作成",
            color=LogUtils.get_log_color(LogType.ROLE_CREATE)
        )
        embed.add_field(name="🏷️ ロール名", value=role.mention, inline=True)
        embed.add_field(name="🆔 ロールID", value=UserFormatter.format_id(role.id), inline=True)
        embed.add_field(name="🎨 色", value=UserFormatter.format_code_inline(str(role.color)), inline=True)
        embed.add_field(name="📍 ポジション", value=str(role.position), inline=True)
        embed.add_field(name="🔒 権限", value="管理者" if role.permissions.administrator else "一般", inline=True)
        embed.add_field(name="🕐 作成時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        await self.send_log(role.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=role.guild.id,
            log_type=LogType.ROLE_CREATE,
            action="Role Created",
            details=f"Name: {role.name}, Color: {role.color}, Position: {role.position}, Admin: {role.permissions.administrator}"
        )

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role):
        """ロール削除イベント"""
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.ROLE_DELETE)} ロール削除",
            color=LogUtils.get_log_color(LogType.ROLE_DELETE)
        )
        embed.add_field(name="🏷️ ロール名", value=UserFormatter.format_code_inline(role.name), inline=True)
        embed.add_field(name="🆔 ロールID", value=UserFormatter.format_id(role.id), inline=True)
        embed.add_field(name="🎨 色", value=UserFormatter.format_code_inline(str(role.color)), inline=True)
        embed.add_field(name="📍 ポジション", value=str(role.position), inline=True)
        embed.add_field(name="👥 メンバー数", value=f"{len(role.members)}人", inline=True)
        embed.add_field(name="🕐 削除時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        await self.send_log(role.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=role.guild.id,
            log_type=LogType.ROLE_DELETE,
            action="Role Deleted",
            details=f"Name: {role.name}, Color: {role.color}, Members: {len(role.members)}"
        )

    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        """ロール更新イベント"""
        changes = []

        # 名前変更チェック
        if before.name != after.name:
            changes.append(f"名前: `{before.name}` → `{after.name}`")

        # 色変更チェック
        if before.color != after.color:
            changes.append(f"色: `{before.color}` → `{after.color}`")

        # ポジション変更チェック
        if before.position != after.position:
            changes.append(f"ポジション: `{before.position}` → `{after.position}`")

        # 権限変更チェック
        if before.permissions != after.permissions:
            # 主要な権限の変更をチェック
            permission_changes = []
            if before.permissions.administrator != after.permissions.administrator:
                permission_changes.append(f"管理者: {before.permissions.administrator} → {after.permissions.administrator}")
            if before.permissions.manage_guild != after.permissions.manage_guild:
                permission_changes.append(f"サーバー管理: {before.permissions.manage_guild} → {after.permissions.manage_guild}")
            if before.permissions.manage_roles != after.permissions.manage_roles:
                permission_changes.append(f"ロール管理: {before.permissions.manage_roles} → {after.permissions.manage_roles}")
            if before.permissions.manage_channels != after.permissions.manage_channels:
                permission_changes.append(f"チャンネル管理: {before.permissions.manage_channels} → {after.permissions.manage_channels}")

            if permission_changes:
                changes.append(f"権限: {', '.join(permission_changes[:3])}")

        # メンション可能設定チェック
        if before.mentionable != after.mentionable:
            changes.append(f"メンション可能: `{before.mentionable}` → `{after.mentionable}`")

        # ホイスト設定チェック
        if before.hoist != after.hoist:
            changes.append(f"別表示: `{before.hoist}` → `{after.hoist}`")

        # 変更がない場合は終了
        if not changes:
            return

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.ROLE_UPDATE)} ロール更新",
            color=LogUtils.get_log_color(LogType.ROLE_UPDATE)
        )
        embed.add_field(name="🏷️ ロール", value=after.mention, inline=True)
        embed.add_field(name="🆔 ロールID", value=UserFormatter.format_id(after.id), inline=True)
        embed.add_field(name="🕐 更新時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        # 変更内容を表示
        embed.add_field(
            name="📝 変更内容",
            value="\n".join([f"• {change}" for change in changes[:8]]),  # 最大8項目
            inline=False
        )

        await self.send_log(after.guild.id, embed)

        await self.bot.database.create_log(
            guild_id=after.guild.id,
            log_type=LogType.ROLE_UPDATE,
            action="Role Updated",
            details=f"Role: {after.name}, Changes: {', '.join(changes[:5])}"
        )

    # ===== サーバー関連イベント =====

    @commands.Cog.listener()
    async def on_guild_update(self, before, after):
        """サーバー更新イベント"""
        changes = []

        # 名前変更チェック
        if before.name != after.name:
            changes.append(f"名前: `{before.name}` → `{after.name}`")

        # アイコン変更チェック
        if before.icon != after.icon:
            changes.append("アイコンが変更されました")

        # バナー変更チェック
        if before.banner != after.banner:
            changes.append("バナーが変更されました")

        # 説明変更チェック
        if before.description != after.description:
            before_desc = before.description or "なし"
            after_desc = after.description or "なし"
            changes.append(f"説明: `{UserFormatter.truncate_text(before_desc, 30)}` → `{UserFormatter.truncate_text(after_desc, 30)}`")

        # 認証レベル変更チェック
        if before.verification_level != after.verification_level:
            changes.append(f"認証レベル: `{before.verification_level.name}` → `{after.verification_level.name}`")

        # MFA要求変更チェック
        if before.mfa_level != after.mfa_level:
            changes.append(f"MFA要求: `{before.mfa_level.name}` → `{after.mfa_level.name}`")

        # 変更がない場合は終了
        if not changes:
            return

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.GUILD_UPDATE)} サーバー更新",
            color=LogUtils.get_log_color(LogType.GUILD_UPDATE)
        )
        embed.add_field(name="🏛️ サーバー", value=UserFormatter.format_code_inline(after.name), inline=True)
        embed.add_field(name="🆔 サーバーID", value=UserFormatter.format_id(after.id), inline=True)
        embed.add_field(name="🕐 更新時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)

        # 変更内容を表示
        embed.add_field(
            name="📝 変更内容",
            value="\n".join([f"• {change}" for change in changes[:8]]),
            inline=False
        )

        # 新しいアイコンがある場合はサムネイル設定
        if after.icon:
            embed.set_thumbnail(url=after.icon.url)

        await self.send_log(after.id, embed)

        await self.bot.database.create_log(
            guild_id=after.id,
            log_type=LogType.GUILD_UPDATE,
            action="Guild Updated",
            details=f"Changes: {', '.join(changes[:5])}"
        )

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild, before, after):
        """絵文字更新イベント"""
        added_emojis = [emoji for emoji in after if emoji not in before]
        removed_emojis = [emoji for emoji in before if emoji not in after]

        if not added_emojis and not removed_emojis:
            return

        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.GUILD_EMOJIS_UPDATE)} 絵文字更新",
            color=LogUtils.get_log_color(LogType.GUILD_EMOJIS_UPDATE)
        )
        embed.add_field(name="🏛️ サーバー", value=UserFormatter.format_code_inline(guild.name), inline=True)
        embed.add_field(name="🕐 更新時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)
        embed.add_field(name="📊 絵文字数", value=f"{len(after)}個", inline=True)

        if added_emojis:
            emoji_list = [f"{emoji} (`{emoji.name}`)" for emoji in added_emojis[:5]]
            if len(added_emojis) > 5:
                emoji_list.append(f"... 他{len(added_emojis) - 5}個")
            embed.add_field(
                name="➕ 追加された絵文字",
                value="\n".join(emoji_list),
                inline=False
            )

        if removed_emojis:
            emoji_list = [UserFormatter.format_code_inline(emoji.name) for emoji in removed_emojis[:5]]
            if len(removed_emojis) > 5:
                emoji_list.append(f"... 他{len(removed_emojis) - 5}個")
            embed.add_field(
                name="➖ 削除された絵文字",
                value="\n".join(emoji_list),
                inline=False
            )

        await self.send_log(guild.id, embed)

        await self.bot.database.create_log(
            guild_id=guild.id,
            log_type=LogType.GUILD_EMOJIS_UPDATE,
            action="Guild Emojis Updated",
            details=f"Added: {len(added_emojis)}, Removed: {len(removed_emojis)}"
        )

    @commands.Cog.listener()
    async def on_ready(self):
        """BOT起動完了イベント"""
        embed = EmbedBuilder.create_base_embed(
            title=f"{LogUtils.get_log_emoji(LogType.BOT_READY)} BOT起動完了",
            color=LogUtils.get_log_color(LogType.BOT_READY)
        )
        embed.add_field(name="🚀 ステータス", value="BOTが正常に起動しました", inline=True)
        embed.add_field(name="🕐 起動時刻", value=UserFormatter.format_timestamp(datetime.now(), "F"), inline=True)
        embed.add_field(name="🤖 BOT情報", value=UserFormatter.format_user_mention_and_tag(self.bot.user), inline=True)
        embed.add_field(name="🌐 サーバー数", value=f"{len(self.bot.guilds)}サーバー", inline=True)
        embed.add_field(name="👥 総ユーザー数", value=f"{len(self.bot.users)}ユーザー", inline=True)

        # レイテンシ情報
        latency_ms = round(self.bot.latency * 1000)
        embed.add_field(name="📡 レイテンシ", value=f"{latency_ms}ms", inline=True)

        # 全てのサーバーにログ送信
        for guild in self.bot.guilds:
            await self.send_log(guild.id, embed)
            await self.bot.database.create_log(
                guild_id=guild.id,
                log_type=LogType.BOT_READY,
                action="Bot Ready",
                details=f"Guilds: {len(self.bot.guilds)}, Users: {len(self.bot.users)}, Latency: {latency_ms}ms"
            )


async def setup(bot):
    await bot.add_cog(LoggingCog(bot))
