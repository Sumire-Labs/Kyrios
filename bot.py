import discord
from discord.ext import commands
import logging
import asyncio
from pathlib import Path
import sys

from di import container, inject_dependencies, ConfigDep, DatabaseDep, EventBusDep, CogFactoryDep
from dependency_injector.wiring import inject, Provide


class KyriosBot(commands.Bot):
    @inject
    def __init__(
        self,
        config=Provide[container.config],
        database=Provide[container.database_manager],
        event_bus=Provide[container.wired_event_bus],
        cog_factory=Provide[container.cog_factory]
    ):
        self.settings = config
        self.database = database
        self.event_bus = event_bus
        self.cog_factory = cog_factory

        self._setup_logging()

        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True

        super().__init__(
            command_prefix=self.settings.bot_prefix,
            description=self.settings.bot_description,
            intents=intents,
            case_insensitive=True
        )

        self.logger = logging.getLogger(__name__)

    def _setup_logging(self) -> None:
        log_file_path = Path(self.settings.logging_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, self.settings.logging_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    async def setup_hook(self) -> None:
        self.logger.info("Setting up Kyrios Bot...")
        await self._load_cogs()
        self.logger.info("Kyrios Bot setup completed")

    async def _load_cogs(self) -> None:
        cog_files: list[str] = [
            "cogs.ping",
            "cogs.tickets",
            "cogs.logging"
        ]

        for cog_file in cog_files:
            try:
                if cog_file.endswith("tickets") and not self.settings.features_tickets:
                    self.logger.info(f"Skipping {cog_file} (feature disabled)")
                    continue

                if cog_file.endswith("logging") and not self.settings.features_logger:
                    self.logger.info(f"Skipping {cog_file} (feature disabled)")
                    continue

                await self.load_extension(cog_file)
                self.logger.info(f"Loaded cog: {cog_file}")
            except Exception as e:
                self.logger.error(f"Failed to load cog {cog_file}: {e}")

    async def on_ready(self) -> None:
        self.logger.info(f"{self.user} has connected to Discord!")
        self.logger.info(f"Bot is in {len(self.guilds)} guilds")

        if self.user:
            await self.event_bus.emit_event("bot_ready", {
                "bot_id": self.user.id,
                "guild_count": len(self.guilds)
            })

        activity = discord.Game(name="Managing your server 🛡️")
        await self.change_presence(activity=activity)

    async def on_guild_join(self, guild: discord.Guild) -> None:
        self.logger.info(f"Joined guild: {guild.name} ({guild.id})")
        await self.event_bus.emit_event("guild_join", {
            "guild_id": guild.id,
            "guild_name": guild.name,
            "member_count": guild.member_count
        })

    async def on_guild_remove(self, guild: discord.Guild) -> None:
        self.logger.info(f"Left guild: {guild.name} ({guild.id})")
        await self.event_bus.emit_event("guild_remove", {
            "guild_id": guild.id,
            "guild_name": guild.name
        })

    async def on_command_error(self, context: commands.Context, exception: commands.CommandError) -> None:
        if isinstance(exception, commands.CommandNotFound):
            return

        if isinstance(exception, commands.MissingPermissions):
            await context.send("❌ あなたはこのコマンドを実行する権限がありません。")
            return

        if isinstance(exception, commands.CommandOnCooldown):
            await context.send(f"⏰ このコマンドは {exception.retry_after:.2f} 秒後に使用できます。")
            return

        self.logger.error(f"Command error in {context.command}: {exception}", exc_info=True)
        await context.send("❌ コマンドの実行中にエラーが発生しました。")

        await self.event_bus.emit_event("command_error", {
            "command": str(context.command),
            "error": str(exception),
            "user_id": context.author.id,
            "guild_id": context.guild.id if context.guild else None
        })

    async def close(self) -> None:
        self.logger.info("Shutting down Kyrios Bot...")
        await self.event_bus.emit_event("bot_shutdown", {})
        await super().close()


async def main():
    # DIコンテナを初期化・ワイヤリング
    container.init_resources()
    container.wire(modules=[__name__, "cogs.ping", "cogs.tickets", "cogs.logging"])

    bot = None
    try:
        bot = KyriosBot()
        await bot.start(bot.settings.bot_token)
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, shutting down...")
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")
    finally:
        container.shutdown_resources()
        if bot is not None and not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutdown by user")