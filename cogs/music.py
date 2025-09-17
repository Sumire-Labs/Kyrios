# type: ignore
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from common import EmbedBuilder, UIColors, UIEmojis, UserFormatter, ButtonStyles
from di import DatabaseDep, EventBusDep, ConfigDep
from dependency_injector.wiring import inject, Provide
from database.models import LoopMode
from music.music_service import MusicService
from music.youtube_extractor import YouTubeExtractor


class QuickAddModal(discord.ui.Modal):
    """楽曲追加用モーダル - Kyriosスタイル"""

    def __init__(self, bot, guild_id: int):
        super().__init__(title="🎵 楽曲をキューに追加")
        self.bot = bot
        self.guild_id = guild_id

    query = discord.ui.TextInput(
        label="YouTubeURL または 検索キーワード",
        placeholder="楽曲のURLまたはタイトル・アーティスト名を入力...",
        max_length=200
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)

        # ローディングEmbed表示
        loading_embed = EmbedBuilder.create_loading_embed("楽曲検索中", "YouTubeから楽曲を検索しています...")
        message = await interaction.followup.send(embed=loading_embed, ephemeral=True)

        try:
            # ボイスチャンネルチェック
            if not interaction.user.voice:
                error_embed = EmbedBuilder.create_error_embed("接続エラー", "ボイスチャンネルに参加してから使用してください")
                await message.edit(embed=error_embed)
                return

            # 楽曲検索・追加
            track_info = await self.bot.music_service.search_and_add(
                guild_id=self.guild_id,
                query=self.query.value,
                requested_by=interaction.user.id,
                voice_channel=interaction.user.voice.channel
            )

            success_embed = EmbedBuilder.create_success_embed(
                "キューに追加",
                f"🎵 **{track_info.title}** をキューに追加しました"
            )
            await message.edit(embed=success_embed)

        except Exception as e:
            error_embed = EmbedBuilder.create_error_embed("追加失敗", f"楽曲の追加に失敗しました: {str(e)}")
            await message.edit(embed=error_embed)


class MusicPlayerView(discord.ui.View):
    """オールインワン音楽プレイヤー - Kyriosパターン準拠"""

    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)  # 永続View
        self.bot = bot
        self.guild_id = guild_id

    # 🎮 Row 1: メイン再生コントロール
    @discord.ui.button(emoji="⏮️", style=ButtonStyles.SECONDARY, row=0)
    async def previous_track(self, interaction: discord.Interaction, button: discord.ui.Button):
        """前の曲 (未実装)"""
        await interaction.response.send_message("⏮️ 前の曲機能は未実装です", ephemeral=True)

    @discord.ui.button(emoji="⏸️", style=ButtonStyles.PRIMARY, row=0)
    async def play_pause_toggle(self, interaction: discord.Interaction, button: discord.ui.Button):
        """再生/一時停止トグル"""
        await self._handle_player_action(interaction, "toggle")

    @discord.ui.button(emoji="⏭️", style=ButtonStyles.SECONDARY, row=0)
    async def next_track(self, interaction: discord.Interaction, button: discord.ui.Button):
        """次の曲"""
        await self._handle_player_action(interaction, "skip")

    @discord.ui.button(emoji="🔄", style=ButtonStyles.SECONDARY, row=0)
    async def loop_mode(self, interaction: discord.Interaction, button: discord.ui.Button):
        """ループモード切り替え"""
        await self._handle_player_action(interaction, "loop")

    @discord.ui.button(emoji="⏹️", style=ButtonStyles.DANGER, row=0)
    async def stop_player(self, interaction: discord.Interaction, button: discord.ui.Button):
        """停止"""
        await self._handle_player_action(interaction, "stop")

    # 🔊 Row 2: キュー・追加操作 (中央寄せ)
    @discord.ui.button(emoji="🗑️", label="キュークリア", style=ButtonStyles.SECONDARY, row=1)
    async def clear_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """キュークリア"""
        await self._handle_queue_action(interaction, "clear")

    @discord.ui.button(emoji="➕", label="楽曲追加", style=ButtonStyles.SUCCESS, row=1)
    async def add_to_queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        """楽曲追加モーダル"""
        modal = QuickAddModal(self.bot, self.guild_id)
        await interaction.response.send_modal(modal)

    # 🔧 内部メソッド - Kyriosパターン準拠
    async def _handle_player_action(self, interaction: discord.Interaction, action: str):
        """プレイヤー操作統一ハンドラー"""
        await interaction.response.defer()

        try:
            player = self.bot.music_service.get_player(self.guild_id)
            if not player and action != "stop":
                await interaction.followup.send("❌ 音楽が再生されていません", ephemeral=True)
                return

            # アクション実行
            if action == "toggle":
                if player.is_playing():
                    await player.pause()
                    embed = EmbedBuilder.create_info_embed("一時停止", "音楽を一時停止しました")
                else:
                    await player.resume()
                    embed = EmbedBuilder.create_success_embed("再生", "音楽を再開しました")
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action == "skip":
                await player.skip()
                embed = EmbedBuilder.create_success_embed("スキップ", "次の楽曲にスキップしました")
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action == "loop":
                await player.cycle_loop_mode()
                mode_text = player.loop_mode.value.upper()
                embed = EmbedBuilder.create_success_embed("ループモード", f"ループモードを **{mode_text}** に変更しました")
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action == "stop":
                if player:
                    await player.stop()
                    await self.bot.music_service.disconnect_voice(self.guild_id)
                embed = EmbedBuilder.create_success_embed("停止", "音楽を停止し、ボイスチャンネルから退出しました")
                await interaction.followup.send(embed=embed, ephemeral=True)
                return  # Embed更新しない

            # Embed更新
            await self._update_player_embed(interaction)

        except Exception as e:
            self.bot.logger.error(f"Player action error: {e}")
            embed = EmbedBuilder.create_error_embed("操作エラー", "操作の実行に失敗しました")
            await interaction.followup.send(embed=embed, ephemeral=True)


    async def _handle_queue_action(self, interaction: discord.Interaction, action: str):
        """キュー操作処理"""
        await interaction.response.defer(ephemeral=True)

        try:
            if action == "clear":
                cleared_count = await self.bot.database.clear_queue(self.guild_id)
                embed = EmbedBuilder.create_success_embed("キュークリア", f"{cleared_count}曲をキューから削除しました")
                await interaction.followup.send(embed=embed, ephemeral=True)

                # メインEmbed更新
                await self._update_player_embed(interaction)

        except Exception as e:
            self.bot.logger.error(f"Queue action error: {e}")
            await interaction.followup.send("❌ キュー操作に失敗しました", ephemeral=True)

    async def _update_player_embed(self, interaction: discord.Interaction):
        """プレイヤーEmbed更新"""
        try:
            # 最新状態取得
            track_data = await self.bot.music_service.get_current_track(self.guild_id)
            session_data = await self.bot.music_service.get_session_info(self.guild_id)
            queue_data = await self.bot.music_service.get_queue(self.guild_id)

            if not track_data:
                return

            # Embed再構築
            embed = EmbedBuilder.create_music_player_embed(track_data, session_data, queue_data)

            # ボタンの状態更新
            self._update_button_states(session_data)

            await interaction.edit_original_response(embed=embed, view=self)

        except Exception as e:
            self.bot.logger.error(f"Embed update error: {e}")

    def _update_button_states(self, session_data: dict):
        """ボタンの見た目を動的更新"""
        try:
            # 再生/一時停止ボタンの絵文字切り替え
            play_pause_button = self.children[1]  # 2番目のボタン
            if session_data.get('is_paused', False):
                play_pause_button.emoji = "▶️"
            else:
                play_pause_button.emoji = "⏸️"

            # ループボタンの色変更
            loop_button = self.children[3]  # 4番目のボタン
            loop_mode = session_data.get('loop_mode', 'none')
            if loop_mode == 'none':
                loop_button.style = ButtonStyles.SECONDARY
            else:
                loop_button.style = ButtonStyles.SUCCESS
        except Exception as e:
            self.bot.logger.error(f"Button state update error: {e}")


class MusicCog(commands.Cog):
    """音楽システムCog - Kyriosパターン準拠"""

    @inject
    def __init__(
        self,
        bot,
        database=DatabaseDep,
        event_bus=EventBusDep,
        config=ConfigDep
    ):
        self.bot = bot
        self.database = database
        self.event_bus = event_bus
        self.config = config
        self.logger = logging.getLogger(__name__)

        # 音楽システム初期化
        self.youtube_extractor = YouTubeExtractor()
        self.music_service = MusicService(self.database, self.event_bus, self.youtube_extractor)

        # botにmusic_serviceを追加
        bot.music_service = self.music_service

    @app_commands.command(name="play", description="音楽を再生します")
    @app_commands.describe(query="YouTubeURL または 検索キーワード")
    async def play(self, interaction: discord.Interaction, query: str):
        """メインの音楽再生コマンド"""
        await interaction.response.defer()

        # 1️⃣ ローディング表示
        loading_embed = EmbedBuilder.create_loading_embed(
            "音楽検索中",
            f"🔍 `{query[:50]}{'...' if len(query) > 50 else ''}` を検索中..."
        )
        message = await interaction.followup.send(embed=loading_embed)

        try:
            # 2️⃣ ボイスチャンネルチェック
            if not interaction.user.voice:
                error_embed = EmbedBuilder.create_error_embed(
                    "接続エラー",
                    "ボイスチャンネルに参加してから使用してください"
                )
                await message.edit(embed=error_embed)
                return

            # 3️⃣ 既存プレイヤーチェック
            existing_player = self.music_service.get_player(interaction.guild.id)

            if not existing_player:
                # ボイスチャンネル接続
                connected = await self.music_service.connect_voice(interaction.user.voice.channel, interaction.channel)
                if not connected:
                    error_embed = EmbedBuilder.create_error_embed("接続エラー", "ボイスチャンネルへの接続に失敗しました")
                    await message.edit(embed=error_embed)
                    return

            # 4️⃣ 楽曲検索・追加
            track_info = await self.music_service.search_and_add(
                guild_id=interaction.guild.id,
                query=query,
                requested_by=interaction.user.id,
                voice_channel=interaction.user.voice.channel
            )

            if existing_player and existing_player.is_playing():
                # キューに追加のみ
                embed = EmbedBuilder.create_success_embed(
                    "キューに追加",
                    f"🎵 **{track_info.title}** をキューに追加しました"
                )
                await message.edit(embed=embed)
            else:
                # 5️⃣ 新規プレイヤー起動 + UIマネージャー表示
                await self.music_service.start_player(interaction.guild.id)

                # 6️⃣ 統合プレイヤーUI表示
                await self._display_music_player(message, interaction.guild.id)

        except Exception as e:
            self.logger.error(f"Play command error: {e}")
            error_embed = EmbedBuilder.create_error_embed(
                "再生エラー",
                f"楽曲の検索または再生に失敗しました: {str(e)}"
            )
            await message.edit(embed=error_embed)

    @app_commands.command(name="stop", description="音楽を停止し、ボイスチャンネルから退出します")
    async def stop(self, interaction: discord.Interaction):
        """音楽停止コマンド"""
        await interaction.response.defer()

        try:
            player = self.music_service.get_player(interaction.guild.id)
            if not player:
                embed = EmbedBuilder.create_warning_embed("停止", "再生中の音楽がありません")
                await interaction.followup.send(embed=embed)
                return

            await player.stop()
            await self.music_service.disconnect_voice(interaction.guild.id)

            embed = EmbedBuilder.create_success_embed("停止完了", "音楽を停止し、ボイスチャンネルから退出しました")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            self.logger.error(f"Stop command error: {e}")
            embed = EmbedBuilder.create_error_embed("停止エラー", "音楽の停止に失敗しました")
            await interaction.followup.send(embed=embed)

    @app_commands.command(name="loop", description="ループモードを切り替えます")
    @app_commands.describe(mode="ループモード (none/track/queue)")
    @app_commands.choices(mode=[
        app_commands.Choice(name="なし", value="none"),
        app_commands.Choice(name="楽曲リピート", value="track"),
        app_commands.Choice(name="キューリピート", value="queue")
    ])
    async def loop(self, interaction: discord.Interaction, mode: Optional[str] = None):
        """ループモード設定コマンド"""
        await interaction.response.defer()

        try:
            player = self.music_service.get_player(interaction.guild.id)
            if not player:
                embed = EmbedBuilder.create_warning_embed("ループ設定", "再生中の音楽がありません")
                await interaction.followup.send(embed=embed)
                return

            if mode:
                # 指定モードに設定
                loop_mode = LoopMode(mode)
                await player.set_loop_mode(loop_mode)
                mode_text = loop_mode.value.upper()
            else:
                # 循環切り替え
                await player.cycle_loop_mode()
                mode_text = player.loop_mode.value.upper()

            embed = EmbedBuilder.create_success_embed("ループモード変更", f"ループモードを **{mode_text}** に設定しました")
            await interaction.followup.send(embed=embed)

        except Exception as e:
            self.logger.error(f"Loop command error: {e}")
            embed = EmbedBuilder.create_error_embed("ループ設定エラー", "ループモードの変更に失敗しました")
            await interaction.followup.send(embed=embed)

    async def _display_music_player(self, message: discord.WebhookMessage, guild_id: int):
        """統合音楽プレイヤー表示"""
        try:
            # 現在の状態取得
            track_data = await self.music_service.get_current_track(guild_id)
            session_data = await self.music_service.get_session_info(guild_id)
            queue_data = await self.music_service.get_queue(guild_id)

            # 統合プレイヤーEmbed作成
            embed = EmbedBuilder.create_music_player_embed(track_data, session_data, queue_data)
            view = MusicPlayerView(self.bot, guild_id)

            # ローディングメッセージを置き換え
            await message.edit(embed=embed, view=view)

            # EventBus通知
            await self.event_bus.emit_event("music_player_displayed", {
                "guild_id": guild_id,
                "track_title": track_data.get('title', 'Unknown'),
                "message_id": message.id
            })

        except Exception as e:
            self.logger.error(f"Music player display error: {e}")


async def setup(bot):
    await bot.add_cog(MusicCog(bot))