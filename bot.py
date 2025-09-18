import discord
from discord.ext import commands
import logging
import asyncio
from pathlib import Path
import sys
from typing import Union

from di import container, inject_dependencies, ConfigDep, DatabaseDep, EventBusDep, CogFactoryDep
from dependency_injector.wiring import inject, Provide


class LunaBot(commands.Bot):
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

    def _create_activity(self) -> Union[discord.Activity, discord.Game, discord.Streaming]:
        """設定に基づいてDiscordアクティビティを作成"""
        activity_type = self.settings.status_type.lower()
        message = self.settings.status_message

        self.logger.info(f"Creating activity - Type: '{activity_type}', Message: '{message}'")

        if activity_type == "game":
            activity = discord.Game(name=message)
        elif activity_type == "watching":
            activity = discord.Activity(type=discord.ActivityType.watching, name=message)
        elif activity_type == "listening":
            activity = discord.Activity(type=discord.ActivityType.listening, name=message)
        elif activity_type == "streaming":
            url = self.settings.status_streaming_url
            if not url:
                self.logger.warning("Streaming URL not configured, falling back to Game activity")
                activity = discord.Game(name=message)
            else:
                activity = discord.Streaming(name=message, url=url)
        elif activity_type == "custom":
            # カスタムステータスはBOTでは制限があるため、Gameに変更
            self.logger.warning("Custom activity type is not fully supported for bots, using Game instead")
            activity = discord.Game(name=message)
        else:
            self.logger.warning(f"Unknown activity type: {activity_type}, falling back to Game")
            activity = discord.Game(name=message)

        self.logger.info(f"Created activity: {activity}")
        return activity

    def _setup_logging(self) -> None:
        # 設定オブジェクトが注入されていない場合はデフォルト値を使用
        try:
            log_file = self.settings.logging_file
            log_level = self.settings.logging_level
        except AttributeError:
            # フォールバック設定
            log_file = "kyrios.log"
            log_level = "INFO"
            print("Warning: Using fallback logging configuration")

        log_file_path = Path(log_file)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)

        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file_path, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )

    async def setup_hook(self) -> None:
        self.logger.info("Setting up Luna Bot...")
        await self._load_cogs()

        # スラッシュコマンドをDiscordに同期
        try:
            self.logger.info("Syncing slash commands...")
            synced = await self.tree.sync()
            self.logger.info(f"Synced {len(synced)} slash commands to Discord")
        except Exception as e:
            self.logger.error(f"Failed to sync slash commands: {e}")

        self.logger.info("Luna Bot setup completed")

    async def _load_cogs(self) -> None:
        cog_files: list[str] = [
            "cogs.ping",
            "cogs.tickets",
            "cogs.logging",
            "cogs.avatar",
            "cogs.music"
        ]

        for cog_file in cog_files:
            try:
                if cog_file.endswith("tickets") and not self.settings.features_tickets:
                    self.logger.info(f"Skipping {cog_file} (feature disabled)")
                    continue

                if cog_file.endswith("logging") and not self.settings.features_logger:
                    self.logger.info(f"Skipping {cog_file} (feature disabled)")
                    continue

                if cog_file.endswith("music") and not getattr(self.settings, 'features_music', True):
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

        # 設定可能なステータスメッセージ
        self.logger.info("Setting bot presence...")
        activity = self._create_activity()
        await self.change_presence(activity=activity)
        self.logger.info("Bot presence set successfully")

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
        self.logger.info("Shutting down Luna Bot...")
        await self.event_bus.emit_event("bot_shutdown", {})
        await super().close()


async def main():
    # DIコンテナをワイヤリング
    container.wire(modules=[__name__, "cogs.ping", "cogs.tickets", "cogs.logging", "cogs.avatar", "cogs.music"])

    bot = None
    try:
        # 設定を直接取得してボット初期化
        config = container.config()
        database_manager = container.database_manager_raw()
        event_bus = container.wired_event_bus()
        cog_factory = container.cog_factory()

        # ボット初期化
        bot = LunaBot(
            config=config,
            database=database_manager,
            event_bus=event_bus,
            cog_factory=cog_factory
        )

        # 非同期リソース初期化
        await container.init_resources()

        # ボット起動
        await bot.start(bot.settings.bot_token)
    except KeyboardInterrupt:
        print("\nReceived interrupt signal, shutting down...")
    except Exception as e:
        logging.error(f"Failed to start bot: {e}")
    finally:
        await container.shutdown_resources()
        if bot is not None and not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot shutdown by user")