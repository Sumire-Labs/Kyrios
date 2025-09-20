# type: ignore
import asyncio
import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional

from common import EmbedBuilder, UIColors, UIEmojis, UserFormatter, ButtonStyles
from core import DatabaseDep, EventBusDep, ConfigDep, container
from dependency_injector.wiring import inject, Provide
from database.models import LoopMode
from music.music_service import MusicService
from music.youtube_extractor import YouTubeExtractor
from music.spotify_extractor import SpotifyExtractor
from music.url_detector import URLDetector


class QuickAddModal(discord.ui.Modal):
    """楽曲追加用モーダル - Lunaスタイル"""

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
        try:
            self.bot.logger.info(f"QuickAdd modal submitted by {interaction.user.name} with query: {self.query.value}")
            await interaction.response.defer(ephemeral=True)

            # ローディングEmbed表示
            loading_embed = EmbedBuilder.create_loading_embed("楽曲検索中", "YouTubeから楽曲を検索しています...")
            message = await interaction.followup.send(embed=loading_embed, ephemeral=True)

            # ボイスチャンネルチェック
            if not interaction.user.voice:
                error_embed = EmbedBuilder.create_error_embed("接続エラー", "ボイスチャンネルに参加してから使用してください")
                await message.edit(embed=error_embed)
                return

            # 楽曲検索・追加
            self.bot.logger.info(f"Searching for track: {self.query.value}")
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
            self.bot.logger.info(f"Successfully added track: {track_info.title}")

            # 楽曲追加後にUIを更新
            await MusicPlayerView.cleanup_old_player_ui(self.guild_id)
            await self._refresh_player_ui(interaction)

        except Exception as e:
            self.bot.logger.error(f"Modal submit error: {e}")
            try:
                error_embed = EmbedBuilder.create_error_embed("追加失敗", f"楽曲の追加に失敗しました: {str(e)}")
                if 'message' in locals():
                    await message.edit(embed=error_embed)
                else:
                    await interaction.followup.send(embed=error_embed, ephemeral=True)
            except Exception as e2:
                self.bot.logger.error(f"Error handling error: {e2}")

    async def _refresh_player_ui(self, interaction: discord.Interaction):
        """プレイヤーUIを新しくチャンネルの下に表示"""
        try:
            # 現在の状態取得
            track_data = await self.bot.music_service.get_current_track(self.guild_id)
            session_data = await self.bot.music_service.get_session_info(self.guild_id)
            queue_data = await self.bot.music_service.get_queue(self.guild_id)

            if not track_data:
                return

            # 新しいプレイヤーEmbed作成
            embed = EmbedBuilder.create_music_player_embed(track_data, session_data, queue_data)
            view = MusicPlayerView(self.bot, self.guild_id)

            # チャンネルに新しいメッセージとして送信
            new_message = await interaction.channel.send(embed=embed, view=view)

            # 自動更新開始
            view.start_auto_update(new_message)

        except Exception as e:
            self.bot.logger.error(f"Player UI refresh error: {e}")


class MusicPlayerView(discord.ui.View):
    """オールインワン音楽プレイヤー - Lunaパターン準拠"""

    # クラス変数でアクティブなインスタンスを追跡
    _active_instances = set()
    # ギルドごとのアクティブプレイヤーメッセージを追跡
    _guild_messages = {}

    def __init__(self, bot, guild_id: int):
        super().__init__(timeout=None)  # 永続View
        self.bot = bot
        self.guild_id = guild_id
        self.message = None  # Embedメッセージの参照
        self.update_task = None  # 自動更新タスク

        # このインスタンスをアクティブリストに追加
        MusicPlayerView._active_instances.add(self)

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
        try:
            self.bot.logger.info(f"Add to queue button pressed by {interaction.user.name}")
            modal = QuickAddModal(self.bot, self.guild_id)
            await interaction.response.send_modal(modal)
            self.bot.logger.info("Modal sent successfully")
        except Exception as e:
            self.bot.logger.error(f"Add to queue button error: {e}")
            await interaction.response.send_message("❌ 楽曲追加モーダルの表示に失敗しました", ephemeral=True)

    # 🔧 内部メソッド - Lunaパターン準拠
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
                # MusicServiceの新しいスキップメソッドを使用
                success = await self.bot.music_service.skip_to_next(self.guild_id)
                if success:
                    embed = EmbedBuilder.create_success_embed("スキップ", "次の楽曲にスキップしました")
                    # スキップ後にUIを更新
                    await MusicPlayerView.cleanup_old_player_ui(self.guild_id)
                    await self._refresh_player_ui_after_skip(interaction)
                else:
                    embed = EmbedBuilder.create_error_embed("スキップエラー", "次の楽曲への移行に失敗しました")
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action == "loop":
                await player.cycle_loop_mode()
                mode_text = player.loop_mode.value.upper()
                embed = EmbedBuilder.create_success_embed("ループモード", f"ループモードを **{mode_text}** に変更しました")
                await interaction.followup.send(embed=embed, ephemeral=True)

            elif action == "stop":
                try:
                    if player:
                        await player.stop()
                        await self.bot.music_service.disconnect_voice(self.guild_id, auto_cleanup=False)

                    # 自動更新停止
                    self.stop_auto_update()

                    embed = EmbedBuilder.create_success_embed("停止", "音楽を停止し、ボイスチャンネルから退出しました")
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return  # Embed更新しない
                except Exception as stop_error:
                    self.bot.logger.error(f"Stop action error: {stop_error}")
                    # 停止処理は成功扱いにする（ユーザー体験優先）
                    embed = EmbedBuilder.create_success_embed("停止", "音楽を停止し、ボイスチャンネルから退出しました")
                    await interaction.followup.send(embed=embed, ephemeral=True)
                    return

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

    def start_auto_update(self, message):
        """プログレスバー自動更新開始"""
        self.message = message
        # このギルドのアクティブメッセージとして登録
        MusicPlayerView._guild_messages[self.guild_id] = message
        if self.update_task is None or self.update_task.done():
            self.update_task = asyncio.create_task(self._auto_update_loop())

    def stop_auto_update(self):
        """自動更新停止"""
        if self.update_task and not self.update_task.done():
            self.update_task.cancel()

        # インスタンスをアクティブリストから削除
        MusicPlayerView._active_instances.discard(self)
        # ギルドメッセージからも削除
        if self.guild_id in MusicPlayerView._guild_messages:
            del MusicPlayerView._guild_messages[self.guild_id]

    @classmethod
    def cleanup_all_tasks(cls):
        """全てのアクティブなViewのタスクを停止"""
        try:
            for instance in cls._active_instances.copy():
                if instance.update_task and not instance.update_task.done():
                    instance.update_task.cancel()
            cls._active_instances.clear()
            cls._guild_messages.clear()
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error during cleanup_all_tasks: {e}")

    @classmethod
    async def cleanup_old_player_ui(cls, guild_id: int):
        """古いプレイヤーUIを削除"""
        try:
            if guild_id in cls._guild_messages:
                old_message = cls._guild_messages[guild_id]
                try:
                    # 古いメッセージのViewを無効化
                    await old_message.edit(view=None)
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).debug(f"Could not disable old view: {e}")

                # ギルドメッセージリストから削除
                del cls._guild_messages[guild_id]
        except Exception as e:
            import logging
            logging.getLogger(__name__).error(f"Error cleaning up old player UI: {e}")

    async def _auto_update_loop(self):
        """プログレスバー自動更新ループ"""
        try:
            while True:
                # 3秒間隔で更新
                await asyncio.sleep(3)

                # プレイヤーが存在するかチェック
                player = self.bot.music_service.get_player(self.guild_id)
                if not player or not player.is_playing():
                    # 再生停止時は更新停止
                    break

                # Embed更新
                await self._update_progress_only()

        except asyncio.CancelledError:
            # タスクキャンセル時 - 正常終了
            self.bot.logger.debug(f"Auto update task cancelled for guild {self.guild_id}")
        except Exception as e:
            self.bot.logger.error(f"Auto update error: {e}")
        finally:
            # 終了時はインスタンスをクリーンアップ
            MusicPlayerView._active_instances.discard(self)

    async def _update_progress_only(self):
        """プログレスバーのみ更新（軽量版）"""
        try:
            if not self.message:
                return

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

            # メッセージ更新
            await self.message.edit(embed=embed, view=self)

        except discord.NotFound:
            # メッセージが削除された場合、更新停止
            self.stop_auto_update()
        except discord.HTTPException:
            # レート制限等は無視
            pass
        except Exception as e:
            self.bot.logger.error(f"Progress update error: {e}")

    async def _refresh_player_ui_after_skip(self, interaction: discord.Interaction):
        """スキップ後にプレイヤーUIを更新（プログレスバー継続）"""
        try:
            # 現在の状態取得
            track_data = await self.bot.music_service.get_current_track(self.guild_id)
            session_data = await self.bot.music_service.get_session_info(self.guild_id)
            queue_data = await self.bot.music_service.get_queue(self.guild_id)

            if not track_data:
                return

            # 新しいプレイヤーEmbed作成
            embed = EmbedBuilder.create_music_player_embed(track_data, session_data, queue_data)
            view = MusicPlayerView(self.bot, self.guild_id)

            # チャンネルに新しいメッセージとして送信
            new_message = await interaction.channel.send(embed=embed, view=view)

            # 自動更新開始（重要：プログレスバーを継続）
            view.start_auto_update(new_message)

            self.bot.logger.info(f"Player UI refreshed after skip for guild {self.guild_id}")

        except Exception as e:
            self.bot.logger.error(f"Player UI refresh after skip error: {e}")


class MusicCog(commands.Cog):
    """音楽システムCog - Lunaパターン準拠"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        # DIコンテナから直接取得
        self.database = container.database_manager_raw()
        self.event_bus = container.wired_event_bus()
        self.config = container.config()

        # データベースの初期化確認（通常は既にbot.pyで初期化済み）
        # self.database.initialize() は必要に応じて後で呼び出される

        # DI デバッグ情報
        self.logger.info(f"MusicCog - Database type: {type(self.database)}")
        self.logger.info(f"MusicCog - EventBus type: {type(self.event_bus)}")

        # DIコンテナから音楽システムを取得
        try:
            self.youtube_extractor = container.youtube_extractor()

            # Spotify統合の確認
            if self.config.spotify_enabled:
                self.spotify_extractor = container.spotify_extractor()
                self.logger.info("Spotify integration enabled via DI")
            else:
                self.spotify_extractor = None
                self.logger.info("Spotify integration disabled (credentials not configured)")

            # MusicServiceを手動で作成（DIの循環依存を回避）
            self.music_service = MusicService(
                database_manager=self.database,
                event_bus=self.event_bus,
                youtube_extractor=self.youtube_extractor,
                spotify_extractor=self.spotify_extractor
            )

        except Exception as e:
            self.logger.error(f"Failed to initialize music system from DI: {e}")
            # フォールバック処理
            self.youtube_extractor = YouTubeExtractor()
            self.music_service = MusicService(self.database, self.event_bus, self.youtube_extractor)
            self.spotify_extractor = None

        # botにmusic_serviceを追加
        bot.music_service = self.music_service

    @app_commands.command(name="play", description="音楽を再生します - YouTube/Spotifyプレイリスト対応")
    @app_commands.describe(query="YouTube/SpotifyのURL・プレイリスト、または検索キーワード")
    async def play(self, interaction: discord.Interaction, query: str):
        """拡張音楽再生コマンド - Spotify対応版"""
        await interaction.response.defer()

        # 1️⃣ URL種別検出
        url_info = URLDetector.detect_url_type(query)

        # 2️⃣ ソース別ローディングメッセージ
        loading_messages = {
            "youtube": f"🔍 YouTubeから `{query[:50]}` を検索中...",
            "youtube_playlist": "📋 YouTubeプレイリストを読み込み中...",
            "spotify_track": "🎵 Spotify楽曲を処理中...",
            "spotify_playlist": "📋 Spotifyプレイリストを読み込み中...",
            "spotify_album": "💿 Spotifyアルバムを読み込み中...",
            "search": f"🔍 `{query[:50]}` を検索中..."
        }

        loading_embed = EmbedBuilder.create_loading_embed(
            "音楽処理中",
            loading_messages.get(url_info.source, loading_messages["search"])
        )
        message = await interaction.followup.send(embed=loading_embed)

        try:
            # 3️⃣ ボイスチャンネルチェック
            if not interaction.user.voice:
                error_embed = EmbedBuilder.create_error_embed(
                    "接続エラー",
                    "ボイスチャンネルに参加してから使用してください"
                )
                await message.edit(embed=error_embed)
                return

            # 4️⃣ Spotify機能チェック
            if url_info.source.startswith("spotify") and not self.spotify_extractor:
                error_embed = EmbedBuilder.create_error_embed(
                    "Spotify未対応",
                    "Spotify機能が無効です。管理者に設定を確認してもらってください"
                )
                await message.edit(embed=error_embed)
                return

            # 5️⃣ ソース別処理分岐
            if url_info.source == "youtube_playlist":
                await self._handle_youtube_playlist(interaction, message, url_info)
            elif url_info.source == "spotify_track":
                await self._handle_spotify_track(interaction, message, url_info)
            elif url_info.source == "spotify_playlist":
                await self._handle_spotify_playlist(interaction, message, url_info)
            elif url_info.source == "spotify_album":
                await self._handle_spotify_album(interaction, message, url_info)
            else:
                # 既存のYouTube/検索処理
                await self._handle_youtube_or_search(interaction, message, query)

        except Exception as e:
            self.logger.error(f"Play command error: {e}")
            error_embed = EmbedBuilder.create_error_embed(
                "再生エラー",
                f"処理中にエラーが発生しました: {str(e)}"
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
            await self.music_service.disconnect_voice(interaction.guild.id, auto_cleanup=False)

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

            # 自動更新開始
            view.start_auto_update(message)

            # EventBus通知
            await self.event_bus.emit_event("music_player_displayed", {
                "guild_id": guild_id,
                "track_title": track_data.get('title', 'Unknown'),
                "message_id": message.id
            })

        except Exception as e:
            self.logger.error(f"Music player display error: {e}")

    async def _display_music_player_refresh(self, channel, guild_id: int):
        """音楽プレイヤーをチャンネルの下に新しく表示（UI更新用）"""
        try:
            # 現在の状態取得
            track_data = await self.music_service.get_current_track(guild_id)
            session_data = await self.music_service.get_session_info(guild_id)
            queue_data = await self.music_service.get_queue(guild_id)

            if not track_data:
                return

            # 統合プレイヤーEmbed作成
            embed = EmbedBuilder.create_music_player_embed(track_data, session_data, queue_data)
            view = MusicPlayerView(self.bot, guild_id)

            # チャンネルに新しいメッセージとして送信
            new_message = await channel.send(embed=embed, view=view)

            # 自動更新開始
            view.start_auto_update(new_message)

            # EventBus通知
            await self.event_bus.emit_event("music_player_refreshed", {
                "guild_id": guild_id,
                "track_title": track_data.get('title', 'Unknown'),
                "message_id": new_message.id
            })

        except Exception as e:
            self.logger.error(f"Music player refresh display error: {e}")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """ボイス状態変更の監視（自動切断・クリーンアップ）"""
        try:
            # BOT自身の状態変更のみ監視
            if member.id != self.bot.user.id:
                return

            guild_id = member.guild.id

            # BOTがボイスチャンネルから切断された場合
            if before.channel and not after.channel:
                self.logger.info(f"Bot disconnected from voice channel in guild {guild_id}")

                # 音楽サービスのクリーンアップ
                if hasattr(self.bot, 'music_service') and self.bot.music_service:
                    player = self.bot.music_service.get_player(guild_id)
                    if player:
                        # プレイヤー停止
                        await player.stop()
                        # プレイヤーを削除
                        if guild_id in self.bot.music_service.players:
                            del self.bot.music_service.players[guild_id]

                        # キューと履歴の自動クリーンアップ
                        await self.bot.music_service._cleanup_guild_data(guild_id)

                        # セッション削除
                        await self.bot.music_service.database.delete_session(guild_id)

                        self.logger.info(f"Auto cleanup completed for guild {guild_id}")

            # BOTがボイスチャンネルに接続された場合のログ
            elif not before.channel and after.channel:
                self.logger.info(f"Bot connected to voice channel {after.channel.name} in guild {guild_id}")

        except Exception as e:
            self.logger.error(f"Voice state update handling error: {e}")

    async def cog_unload(self):
        """Cog終了時のクリーンアップ"""
        try:
            self.logger.info("Cleaning up MusicCog...")

            # 全てのアクティブプレイヤーのタスクを停止
            if hasattr(self.bot, 'music_service') and self.bot.music_service:
                for guild_id, player in self.bot.music_service.players.items():
                    try:
                        # 音楽停止
                        await player.stop()
                        # ボイスチャンネル切断
                        if player.voice_client.is_connected():
                            await player.voice_client.disconnect()
                    except Exception as e:
                        self.logger.error(f"Error stopping player for guild {guild_id}: {e}")

            # MusicPlayerViewの全タスク停止
            MusicPlayerView.cleanup_all_tasks()

            self.logger.info("MusicCog cleanup completed")

        except Exception as e:
            self.logger.error(f"Error during MusicCog cleanup: {e}")

    # =========================
    # プレイリスト処理メソッド
    # =========================

    async def _handle_youtube_playlist(self, interaction: discord.Interaction, message: discord.WebhookMessage, url_info):
        """YouTubeプレイリストの処理"""
        # プレイリスト情報取得
        playlist_data = await self.youtube_extractor.get_playlist_info(url_info.id)
        if not playlist_data:
            raise Exception("YouTubeプレイリストが見つかりません")

        tracks = await self.youtube_extractor.get_playlist_tracks(url_info.id)
        total_tracks = len(tracks)

        if total_tracks == 0:
            raise Exception("プレイリストに楽曲が見つかりません")

        # プログレス更新用
        progress_embed = EmbedBuilder.create_loading_embed(
            "プレイリスト処理中",
            f"📋 **{playlist_data.get('title', 'Unknown Playlist')}** ({total_tracks}曲)\n⏳ 0/{total_tracks} 曲処理完了"
        )
        await message.edit(embed=progress_embed)

        added_tracks = []
        failed_tracks = []

        # 各楽曲を順次処理
        for i, track_info in enumerate(tracks):
            try:
                # YouTubeの場合は直接キューに追加可能
                await self._add_track_to_queue(interaction, track_info)
                added_tracks.append(track_info)

                # プログレス更新（5曲ごと）
                if (i + 1) % 5 == 0 or i == total_tracks - 1:
                    progress_embed.description = f"📋 **{playlist_data.get('title', 'Unknown Playlist')}** ({total_tracks}曲)\n⏳ {i+1}/{total_tracks} 曲処理完了"
                    await message.edit(embed=progress_embed)

            except Exception as e:
                self.logger.error(f"Failed to process track {i}: {e}")
                failed_tracks.append(f"{track_info.title} - {track_info.artist}")

        # 完了メッセージ
        success_description = f"📋 **{playlist_data.get('title', 'Unknown Playlist')}** をキューに追加\n"
        success_description += f"✅ 成功: {len(added_tracks)}曲\n"
        if failed_tracks:
            success_description += f"❌ 失敗: {len(failed_tracks)}曲\n"
        success_description += f"🔗 [YouTube]({url_info.url})"

        final_embed = EmbedBuilder.create_success_embed(
            "プレイリスト追加完了",
            success_description
        )

        # 失敗した楽曲があれば詳細表示
        if failed_tracks and len(failed_tracks) <= 10:
            final_embed.add_field(
                name="❌ 追加に失敗した楽曲",
                value="\n".join(failed_tracks[:10]),
                inline=False
            )

        await message.edit(embed=final_embed)
        await self._update_player_ui_if_needed(interaction)

    # =========================
    # Spotify処理メソッド
    # =========================

    async def _handle_spotify_track(self, interaction: discord.Interaction, message: discord.WebhookMessage, url_info):
        """Spotify楽曲の処理"""
        # Spotify API で楽曲情報取得
        spotify_track = await self.spotify_extractor.get_track(url_info.id)
        if not spotify_track:
            raise Exception("Spotify楽曲が見つかりません")

        # YouTube変換
        track_info = await self.spotify_extractor.spotify_to_youtube(spotify_track)
        if not track_info:
            raise Exception("YouTube上に対応する楽曲が見つかりません")

        # 既存の音楽システムを使用してキューに追加
        added_track_info = await self._add_track_to_queue(
            interaction, track_info, spotify_track, url_info.url
        )

        # 成功メッセージ
        success_embed = EmbedBuilder.create_success_embed(
            "Spotify楽曲追加",
            f"🎵 **{track_info.title}** - {track_info.artist}\n"
            f"💿 {spotify_track['album']['name']}\n"
            f"🎵 [Spotify]({url_info.url}) → 🔗 [YouTube]({track_info.url})"
        )
        await message.edit(embed=success_embed)
        await self._update_player_ui_if_needed(interaction)

    async def _handle_spotify_playlist(self, interaction: discord.Interaction, message: discord.WebhookMessage, url_info):
        """Spotifyプレイリストの処理"""
        # プレイリスト情報取得
        playlist_data = await self.spotify_extractor.get_playlist(url_info.id)
        if not playlist_data:
            raise Exception("Spotifyプレイリストが見つかりません")

        tracks = await self.spotify_extractor.get_playlist_tracks(url_info.id)
        total_tracks = len(tracks)

        if total_tracks == 0:
            raise Exception("プレイリストに楽曲が見つかりません")

        # プログレス更新用
        progress_embed = EmbedBuilder.create_loading_embed(
            "プレイリスト処理中",
            f"📋 **{playlist_data['name']}** ({total_tracks}曲)\n⏳ 0/{total_tracks} 曲処理完了"
        )
        await message.edit(embed=progress_embed)

        added_tracks = []
        failed_tracks = []

        # 各楽曲を順次処理
        for i, spotify_track in enumerate(tracks):
            try:
                # YouTube変換
                track_info = await self.spotify_extractor.spotify_to_youtube(spotify_track)
                if track_info:
                    # キューに追加
                    await self._add_track_to_queue(interaction, track_info, spotify_track)
                    added_tracks.append(track_info)
                else:
                    failed_tracks.append(f"{spotify_track['name']} - {spotify_track['artists'][0]['name']}")

                # プログレス更新（5曲ごと）
                if (i + 1) % 5 == 0 or i == total_tracks - 1:
                    progress_embed.description = f"📋 **{playlist_data['name']}** ({total_tracks}曲)\n⏳ {i+1}/{total_tracks} 曲処理完了"
                    await message.edit(embed=progress_embed)

            except Exception as e:
                self.logger.error(f"Failed to process track {i}: {e}")
                failed_tracks.append(f"{spotify_track['name']} - {spotify_track['artists'][0]['name']}")

        # 完了メッセージ
        success_description = f"📋 **{playlist_data['name']}** をキューに追加\n"
        success_description += f"✅ 成功: {len(added_tracks)}曲\n"
        if failed_tracks:
            success_description += f"❌ 失敗: {len(failed_tracks)}曲\n"
        success_description += f"🎵 [Spotify]({url_info.url})"

        final_embed = EmbedBuilder.create_success_embed(
            "プレイリスト追加完了",
            success_description
        )

        # 失敗した楽曲があれば詳細表示
        if failed_tracks and len(failed_tracks) <= 10:
            final_embed.add_field(
                name="❌ 追加に失敗した楽曲",
                value="\n".join(failed_tracks[:10]),
                inline=False
            )

        await message.edit(embed=final_embed)
        await self._update_player_ui_if_needed(interaction)

    async def _handle_spotify_album(self, interaction: discord.Interaction, message: discord.WebhookMessage, url_info):
        """Spotifyアルバムの処理 - プレイリストと同様の処理"""
        album_data = await self.spotify_extractor.get_album(url_info.id)
        if not album_data:
            raise Exception("Spotifyアルバムが見つかりません")

        tracks = await self.spotify_extractor.get_album_tracks(url_info.id)
        total_tracks = len(tracks)

        if total_tracks == 0:
            raise Exception("アルバムに楽曲が見つかりません")

        # プログレス更新用
        progress_embed = EmbedBuilder.create_loading_embed(
            "アルバム処理中",
            f"💿 **{album_data['name']}** ({total_tracks}曲)\n⏳ 0/{total_tracks} 曲処理完了"
        )
        await message.edit(embed=progress_embed)

        added_tracks = []
        failed_tracks = []

        # 各楽曲を順次処理
        for i, spotify_track in enumerate(tracks):
            try:
                # YouTube変換
                track_info = await self.spotify_extractor.spotify_to_youtube(spotify_track)
                if track_info:
                    # キューに追加
                    await self._add_track_to_queue(interaction, track_info, spotify_track)
                    added_tracks.append(track_info)
                else:
                    failed_tracks.append(f"{spotify_track['name']} - {spotify_track['artists'][0]['name']}")

                # プログレス更新（5曲ごと）
                if (i + 1) % 5 == 0 or i == total_tracks - 1:
                    progress_embed.description = f"💿 **{album_data['name']}** ({total_tracks}曲)\n⏳ {i+1}/{total_tracks} 曲処理完了"
                    await message.edit(embed=progress_embed)

            except Exception as e:
                self.logger.error(f"Failed to process track {i}: {e}")
                failed_tracks.append(f"{spotify_track['name']} - {spotify_track['artists'][0]['name']}")

        # 完了メッセージ
        success_description = f"💿 **{album_data['name']}** をキューに追加\n"
        success_description += f"✅ 成功: {len(added_tracks)}曲\n"
        if failed_tracks:
            success_description += f"❌ 失敗: {len(failed_tracks)}曲\n"
        success_description += f"🎵 [Spotify]({url_info.url})"

        final_embed = EmbedBuilder.create_success_embed(
            "アルバム追加完了",
            success_description
        )

        await message.edit(embed=final_embed)
        await self._update_player_ui_if_needed(interaction)

    async def _handle_youtube_or_search(self, interaction: discord.Interaction, message: discord.WebhookMessage, query: str):
        """既存のYouTube/検索処理"""
        # 既存プレイヤーチェック
        existing_player = self.music_service.get_player(interaction.guild.id)

        if not existing_player:
            # ボイスチャンネル接続
            connected = await self.music_service.connect_voice(interaction.user.voice.channel, interaction.channel)
            if not connected:
                error_embed = EmbedBuilder.create_error_embed("接続エラー", "ボイスチャンネルへの接続に失敗しました")
                await message.edit(embed=error_embed)
                return

        # 楽曲検索・追加
        track_info = await self.music_service.search_and_add(
            guild_id=interaction.guild.id,
            query=query,
            requested_by=interaction.user.id,
            voice_channel=interaction.user.voice.channel
        )

        if existing_player and existing_player.is_playing():
            # キューに追加 + UI更新
            embed = EmbedBuilder.create_success_embed(
                "キューに追加",
                f"🎵 **{track_info.title}** をキューに追加しました"
            )
            await message.edit(embed=embed)

            # 古いプレイヤーUIを削除して新しいUIを下に表示
            await MusicPlayerView.cleanup_old_player_ui(interaction.guild.id)
            await self._display_music_player_refresh(interaction.channel, interaction.guild.id)
        else:
            # 新規プレイヤー起動 + UIマネージャー表示
            await self.music_service.start_player(interaction.guild.id)

            # 統合プレイヤーUI表示
            await self._display_music_player(message, interaction.guild.id)

    async def _add_track_to_queue(self, interaction: discord.Interaction, track_info, spotify_track=None, spotify_url=None):
        """楽曲をキューに追加する共通処理"""
        # 既存プレイヤーチェック
        existing_player = self.music_service.get_player(interaction.guild.id)

        if not existing_player:
            # ボイスチャンネル接続
            connected = await self.music_service.connect_voice(interaction.user.voice.channel, interaction.channel)
            if not connected:
                raise Exception("ボイスチャンネルへの接続に失敗しました")

        # 楽曲検索・追加（SpotifyからYouTube変換済みのtrack_infoを使用）
        added_track_info = await self.music_service.search_and_add(
            guild_id=interaction.guild.id,
            query=track_info.url,  # YouTube URL を使用
            requested_by=interaction.user.id,
            voice_channel=interaction.user.voice.channel
        )

        # プレイヤーが停止中なら開始
        if not existing_player or not existing_player.is_playing():
            await self.music_service.start_player(interaction.guild.id)

        return added_track_info

    async def _update_player_ui_if_needed(self, interaction: discord.Interaction):
        """必要に応じてプレイヤーUIを更新"""
        existing_player = self.music_service.get_player(interaction.guild.id)
        if existing_player and existing_player.is_playing():
            # 古いプレイヤーUIを削除して新しいUIを下に表示
            await MusicPlayerView.cleanup_old_player_ui(interaction.guild.id)
            await self._display_music_player_refresh(interaction.channel, interaction.guild.id)


async def setup(bot):
    await bot.add_cog(MusicCog(bot))