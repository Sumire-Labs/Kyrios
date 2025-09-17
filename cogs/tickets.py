# type: ignore
import discord
from discord import app_commands
from discord.ext import commands
import logging

from common import EmbedBuilder, UIColors, UIEmojis, UserFormatter, ButtonStyles


class TicketView(discord.ui.View):
    def __init__(self, bot):  # type: ignore
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label=f"{UIEmojis.TICKET} チケット作成", style=ButtonStyles.CREATE, custom_id="create_ticket")  # type: ignore
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        user = interaction.user

        if not guild:
            await interaction.followup.send("❌ このコマンドはサーバー内でのみ使用可能です", ephemeral=True)
            return

        existing_tickets = await self.bot.database.get_tickets_by_user(guild.id, user.id)  # type: ignore
        max_tickets = self.bot.settings.tickets_max_per_user  # type: ignore

        if len(existing_tickets) >= max_tickets:
            await interaction.followup.send(
                f"❌ 1ユーザーあたり最大{max_tickets}つまでのチケットしか作成できません。",
                ephemeral=True
            )
            return

        category_id = self.bot.settings.tickets_category_id  # type: ignore
        category = None
        if category_id:
            category_channel = guild.get_channel(category_id)
            if isinstance(category_channel, discord.CategoryChannel):
                category = category_channel

        if not guild.me:
            await interaction.followup.send("❌ ボットの権限が不足しています", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True),
            guild.me: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)
        }

        if guild.roles:
            for role in guild.roles:
                if role.permissions.administrator:
                    overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_messages=True)

        # Discord discriminatorが廃止されているため、display_nameを使用
        channel_name = f"ticket-{user.display_name.lower().replace(' ', '-')[:20]}"
        channel = await guild.create_text_channel(
            name=channel_name,
            category=category,
            overwrites=overwrites,
            topic=f"サポートチケット - {user.mention}" if hasattr(user, 'mention') else "サポートチケット"
        )

        ticket = await self.bot.database.create_ticket(  # type: ignore
            guild_id=guild.id,
            channel_id=channel.id,
            user_id=user.id,
            title="新規サポートチケット"
        )

        embed = EmbedBuilder.create_base_embed(
            title=f"{UIEmojis.TICKET} サポートチケット",
            description=f"こんにちは {user.mention}！\n\nこちらはあなた専用のサポートチケットです。\n以下のボタンを使用して、チケットの管理や詳細情報の追加ができます。",
            color=UIColors.TICKET
        )
        EmbedBuilder.add_ticket_info_fields(
            embed,
            ticket_id=ticket.id,
            status=f"{UIEmojis.TICKET_OPEN} オープン",
            assigned_to="未割り当て",
            created_at=ticket.created_at
        )

        view = TicketManagementView(self.bot, ticket.id)  # type: ignore
        await channel.send(embed=embed, view=view)

        await interaction.followup.send(
            f"✅ チケットを作成しました: {channel.mention}",
            ephemeral=True
        )

        await self.bot.event_bus.emit_event("ticket_created", {  # type: ignore
            "ticket_id": ticket.id,
            "user_id": user.id,
            "guild_id": guild.id,
            "channel_id": channel.id
        })


class TicketManagementView(discord.ui.View):
    def __init__(self, bot, ticket_id: int):  # type: ignore
        super().__init__(timeout=None)
        self.bot = bot
        self.ticket_id = ticket_id

    @discord.ui.button(label="👤 アサイン", style=ButtonStyles.ASSIGN)  # type: ignore
    async def assign_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore
        await interaction.response.send_modal(AssignModal(self.bot, self.ticket_id))

    @discord.ui.button(label="🔒 クローズ", style=ButtonStyles.CLOSE)  # type: ignore
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):  # type: ignore
        if not (isinstance(interaction.user, discord.Member) and interaction.user.guild_permissions.manage_messages):
            ticket = await self.bot.database.get_ticket(self.ticket_id)
            if ticket and interaction.user.id != ticket.user_id:
                await interaction.response.send_message("❌ チケットをクローズする権限がありません。", ephemeral=True)
                return

        await interaction.response.send_modal(CloseModal(self.bot, self.ticket_id))


class AssignModal(discord.ui.Modal):
    def __init__(self, bot, ticket_id: int):  # type: ignore
        super().__init__(title="担当者アサイン")
        self.bot = bot
        self.ticket_id = ticket_id

        self.user_input = discord.ui.TextInput(
            label="ユーザーID またはメンション",
            placeholder="@user または 123456789012345678",
            max_length=100
        )
        self.add_item(self.user_input)

    async def on_submit(self, interaction: discord.Interaction):
        user_input = self.user_input.value.strip()

        if user_input.startswith('<@') and user_input.endswith('>'):
            user_id = int(user_input[2:-1].replace('!', ''))
        else:
            try:
                user_id = int(user_input)
            except ValueError:
                await interaction.response.send_message("❌ 無効なユーザーIDまたはメンションです。", ephemeral=True)
                return

        user = interaction.guild.get_member(user_id)
        if not user:
            await interaction.response.send_message("❌ 指定されたユーザーがサーバーに見つかりません。", ephemeral=True)
            return

        await self.bot.database.update_ticket(self.ticket_id, assigned_to=user_id)
        await interaction.response.send_message(f"✅ チケットを {user.mention} にアサインしました。", ephemeral=True)


class CloseModal(discord.ui.Modal):
    def __init__(self, bot, ticket_id: int):  # type: ignore
        super().__init__(title="チケットクローズ")
        self.bot = bot
        self.ticket_id = ticket_id

        self.reason_input = discord.ui.TextInput(
            label="クローズ理由 (任意)",
            style=discord.TextStyle.paragraph,
            placeholder="解決済み、重複、その他...",
            required=False,
            max_length=500
        )
        self.add_item(self.reason_input)

    async def on_submit(self, interaction: discord.Interaction):
        reason = self.reason_input.value or "理由なし"

        ticket = await self.bot.database.close_ticket(self.ticket_id)
        if not ticket:
            await interaction.response.send_message("❌ チケットが見つかりません。", ephemeral=True)
            return

        embed = EmbedBuilder.create_base_embed(
            title=f"{UIEmojis.TICKET_CLOSED} チケットクローズ",
            description=f"チケット #{ticket.id} がクローズされました。",
            color=UIColors.ERROR
        )
        embed.add_field(name="📝 理由", value=reason, inline=False)
        embed.add_field(name=f"{UIEmojis.USER} クローズ実行者", value=UserFormatter.format_user_mention_and_tag(interaction.user), inline=True)
        embed.add_field(name="📅 クローズ日時", value=UserFormatter.format_timestamp(ticket.closed_at), inline=True)

        await interaction.response.send_message(embed=embed)

        await self.bot.event_bus.emit_event("ticket_closed", {
            "ticket_id": ticket.id,
            "closed_by": interaction.user.id,
            "reason": reason
        })

        await interaction.channel.edit(name=f"closed-{interaction.channel.name}")

        archive_category_id = self.bot.settings.tickets_archive_category_id
        if archive_category_id:
            archive_category = interaction.guild.get_channel(archive_category_id)
            if archive_category:
                await interaction.channel.edit(category=archive_category)


class TicketsCog(commands.Cog):
    def __init__(self, bot):  # type: ignore
        self.bot = bot
        self.logger = logging.getLogger(__name__)

    @app_commands.command(name="ticket", description="チケットパネルを設置します")
    @app_commands.default_permissions(manage_guild=True)
    async def ticket_panel(self, interaction: discord.Interaction):
        embed = EmbedBuilder.create_info_embed(
            "サポートチケット",
            "サポートが必要な場合は下のボタンをクリックしてください\n\n⚠️ **注意事項:**\n• 不適切な利用は禁止されています\n• 1人あたり最大3つまでのチケットを作成できます"
        )
        embed.color = UIColors.TICKET

        view = TicketView(self.bot)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot):  # type: ignore
    await bot.add_cog(TicketsCog(bot))  # type: ignore
