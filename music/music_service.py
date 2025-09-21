import asyncio
import logging
import discord
from typing import Dict, Optional, List, Any
from datetime import datetime
from discord import VoiceClient

from database.models import Track, Queue, MusicSession, MusicSource, LoopMode
from .youtube_extractor import YouTubeExtractor, TrackInfo
from .spotify_extractor import SpotifyExtractor
from .url_detector import URLDetector, URLInfo


class MusicPlayer:
    """個別ギルド用音楽プレイヤー"""

    def __init__(self, guild_id: int, voice_client: VoiceClient, music_service):
        self.guild_id = guild_id
        self.voice_client = voice_client
        self.music_service = music_service
        self.logger = logging.getLogger(__name__)

        self.current_track: Optional[Track] = None
        self.start_time: Optional[datetime] = None
        self.is_paused_flag = False
        self.loop_mode = LoopMode.NONE

    def is_playing(self) -> bool:
        """再生中かどうか"""
        return self.voice_client.is_playing()

    def is_paused(self) -> bool:
        """一時停止中かどうか"""
        return self.is_paused_flag

    async def play_track(self, track: Track):
        """楽曲再生開始"""
        try:
            # 音声ソース取得
            extractor = self.music_service.youtube_extractor
            audio_url = await extractor.get_audio_source(track.url)

            if not audio_url:
                raise Exception("Audio source not found")

            # FFmpegAudioSource作成
            ffmpeg_opts = extractor.get_ffmpeg_options()
            source = discord.FFmpegPCMAudio(
                audio_url,
                before_options=ffmpeg_opts['before_options'],
                options=ffmpeg_opts['options']
            )

            # 音量を15%に固定
            source = discord.PCMVolumeTransformer(source, volume=0.15)

            # 再生開始
            self.voice_client.play(source, after=self._track_finished)
            self.current_track = track
            self.start_time = datetime.now()
            self.is_paused_flag = False

            self.logger.info(f"Playing: {track.title} in guild {self.guild_id}")

        except Exception as e:
            self.logger.error(f"Play error: {e}")
            raise

    async def pause(self):
        """一時停止"""
        if self.voice_client.is_playing():
            self.voice_client.pause()
            self.is_paused_flag = True

    async def resume(self):
        """再生再開"""
        if self.voice_client.is_paused():
            self.voice_client.resume()
            self.is_paused_flag = False

    async def stop(self):
        """停止"""
        try:
            if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
                self.voice_client.stop()
                self.logger.debug(f"Voice client stopped for guild {self.guild_id}")
            else:
                self.logger.warning(f"Voice client not playing/paused for guild {self.guild_id}")
        except Exception as e:
            self.logger.error(f"Error stopping voice client for guild {self.guild_id}: {e}")
        finally:
            # 状態は確実にリセット
            self.current_track = None
            self.start_time = None
            self.is_paused_flag = False

    async def skip(self):
        """スキップ (次の曲)"""
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()  # これにより_track_finishedが呼ばれる


    async def set_loop_mode(self, mode: LoopMode):
        """ループモード設定"""
        self.loop_mode = mode

    async def cycle_loop_mode(self):
        """ループモード循環切り替え"""
        modes = [LoopMode.NONE, LoopMode.TRACK, LoopMode.QUEUE]
        current_index = modes.index(self.loop_mode)
        next_index = (current_index + 1) % len(modes)
        self.loop_mode = modes[next_index]

    def get_position(self) -> int:
        """現在の再生位置 (秒)"""
        if not self.start_time or self.is_paused_flag:
            return 0
        return int((datetime.now() - self.start_time).total_seconds())

    def _track_finished(self, error):
        """楽曲終了コールバック"""
        if error:
            self.logger.error(f"Player error: {error}")

        # 次の楽曲を非同期で処理（メインループで実行）
        try:
            # メインのイベントループを取得してタスクを作成
            loop = self.music_service.event_loop
            if loop and not loop.is_closed():
                loop.call_soon_threadsafe(self._schedule_track_end)
            else:
                self.logger.warning("Event loop not available for track end handling")
        except Exception as e:
            self.logger.error(f"Failed to schedule track end: {e}")

    def _schedule_track_end(self):
        """メインスレッドでtrack_end処理をスケジュール"""
        try:
            asyncio.create_task(self._handle_track_end())
        except Exception as e:
            self.logger.error(f"Failed to create track end task: {e}")

    async def _handle_track_end(self, retry_count: int = 0):
        """楽曲終了処理（無限ループ防止）"""
        try:
            # 無限ループ防止: 最大3回まで再試行
            if retry_count >= 3:
                self.logger.warning(f"Max retry count reached for track end handling in guild {self.guild_id}")
                # トラックループを無効化して次の楽曲へ
                self.loop_mode = LoopMode.NONE
                await self.music_service.play_next(self.guild_id)
                return

            if self.loop_mode == LoopMode.TRACK and self.current_track:
                # 同じ楽曲をリピート
                try:
                    await self.play_track(self.current_track)
                except Exception as e:
                    self.logger.error(f"Track loop failed (retry {retry_count + 1}): {e}")
                    # リピート再生失敗時は少し待ってから再試行
                    await asyncio.sleep(1)
                    await self._handle_track_end(retry_count + 1)
            else:
                # 次の楽曲へ
                await self.music_service.play_next(self.guild_id)
        except Exception as e:
            self.logger.error(f"Track end handling error: {e}")
            # エラー時は安全のためトラックループを無効化
            if retry_count < 3:
                self.loop_mode = LoopMode.NONE
                await self.music_service.play_next(self.guild_id)


class MusicService:
    """音楽システムメインサービス - Lunaパターン準拠"""

    def __init__(self, database_manager, event_bus, youtube_extractor: YouTubeExtractor, spotify_extractor: Optional[SpotifyExtractor] = None):
        self.database = database_manager
        self.event_bus = event_bus
        self.youtube_extractor = youtube_extractor
        self.spotify_extractor = spotify_extractor
        self.url_detector = URLDetector()
        self.logger = logging.getLogger(__name__)

        # アクティブプレイヤー管理
        self.players: Dict[int, MusicPlayer] = {}

        # イベントループの参照を保存
        try:
            self.event_loop = asyncio.get_event_loop()
        except RuntimeError:
            self.event_loop = None
            self.logger.warning("No event loop available at MusicService initialization")

    async def search_and_add(
        self,
        guild_id: int,
        query: str,
        requested_by: int,
        voice_channel: discord.VoiceChannel
    ) -> TrackInfo:
        """楽曲検索・キュー追加（Spotify対応・制限チェック付き）"""
        track_info = None
        music_source = MusicSource.YOUTUBE

        # URL種別判定
        url_info = self.url_detector.detect_url_type(query)

        # Spotify URL処理
        if url_info.source == "spotify" and self.spotify_extractor:
            self.logger.info(f"Spotify URL detected: {query}")
            track_info = await self._handle_spotify_url(url_info)
            music_source = MusicSource.SPOTIFY

        # YouTube URL処理
        elif url_info.source == "youtube":
            self.logger.info(f"YouTube URL detected: {query}")
            track_info = await self.youtube_extractor.search_track(query)
            music_source = MusicSource.YOUTUBE

            # YouTube URLの制限チェック
            if track_info:
                availability = await self.youtube_extractor.check_video_availability(track_info.url)
                if not availability.get("available", True):
                    restriction_type = availability.get("restriction_type", "unknown")
                    user_message = self.youtube_extractor.get_restriction_message(restriction_type)
                    raise Exception(f"{user_message} (URL: {track_info.url})")

        # 通常の検索（Spotifyフォールバック付き）
        else:
            self.logger.info(f"Performing smart search with fallback for: {query}")
            track_info = await self.youtube_extractor.smart_search_with_fallback(query)

            # sourceを適切に設定
            if track_info and track_info.source == "spotify_via_youtube":
                music_source = MusicSource.SPOTIFY
            else:
                music_source = MusicSource.YOUTUBE

        # 検索結果チェック
        if not track_info:
            raise Exception("楽曲が見つかりませんでした")

        # データベースに保存
        track = await self.database.create_track(
            guild_id=guild_id,
            title=track_info.title,
            artist=track_info.artist,
            url=track_info.url,
            duration=track_info.duration,
            thumbnail_url=track_info.thumbnail_url,
            requested_by=requested_by,
            source=music_source
        )

        # キューに追加
        await self.database.add_to_queue(guild_id, track.id, requested_by)

        # EventBus通知
        await self.event_bus.emit_event("track_added", {
            "guild_id": guild_id,
            "track_id": track.id,
            "title": track_info.title,
            "requested_by": requested_by,
            "source": music_source.value
        })

        self.logger.info(f"Added track via {music_source.value}: {track_info.title}")
        return track_info

    async def start_player(self, guild_id: int) -> bool:
        """プレイヤー起動"""
        try:
            # 次の楽曲を再生
            await self.play_next(guild_id)
            return True
        except Exception as e:
            self.logger.error(f"Player start error: {e}")
            return False

    async def play_next(self, guild_id: int, retry_count: int = 0):
        """次の楽曲を再生（制限動画対応強化版・無限再帰防止）"""
        # 無限再帰防止: 最大5回まで再試行
        if retry_count >= 5:
            self.logger.warning(f"Max retry count reached for guild {guild_id}, stopping playback")
            await self._handle_queue_empty(guild_id)
            return

        player = self.players.get(guild_id)
        if not player:
            return

        # キューから次の楽曲を取得
        queue_item = await self.database.get_next_in_queue(guild_id)
        if not queue_item:
            # キューが空
            await self._handle_queue_empty(guild_id)
            return

        # 楽曲情報を取得
        track = await self.database.get_track_by_id(queue_item.track_id)
        if not track:
            # 楽曲が見つからない場合、キューから削除して次へ（再帰カウント増加）
            await self.database.remove_from_queue(guild_id, queue_item.id)
            self.logger.warning(f"Track not found, trying next track (retry: {retry_count + 1})")
            await self.play_next(guild_id, retry_count + 1)
            return

        try:
            # 再生開始を試行
            await player.play_track(track)

            # 成功時のみキューから削除
            await self.database.remove_from_queue(guild_id, queue_item.id)

            # セッション更新
            await self.database.update_session_current_track(guild_id, track.id)

            # EventBus通知
            await self.event_bus.emit_event("track_started", {
                "guild_id": guild_id,
                "track_id": track.id,
                "title": track.title
            })

        except Exception as e:
            # 再生失敗時の処理
            self.logger.error(f"Failed to play track '{track.title}' in guild {guild_id}: {e}")

            # 失敗した楽曲もキューから削除（無限ループ防止）
            await self.database.remove_from_queue(guild_id, queue_item.id)

            # 失敗通知
            await self._notify_track_failed(guild_id, track, str(e))

            # 次の楽曲に自動移行（再帰カウント増加）
            self.logger.warning(f"Track failed, trying next track (retry: {retry_count + 1})")
            await self.play_next(guild_id, retry_count + 1)

    async def _handle_queue_empty(self, guild_id: int):
        """キュー空の処理"""
        player = self.players.get(guild_id)
        if player and player.loop_mode == LoopMode.QUEUE:
            # キューループの場合、キューを再構築
            await self._rebuild_queue_for_loop(guild_id)
            await self.play_next(guild_id)
        else:
            # 再生終了
            await self.event_bus.emit_event("playback_finished", {
                "guild_id": guild_id
            })

    async def _rebuild_queue_for_loop(self, guild_id: int):
        """キューループ用にキューを再構築"""
        # 履歴から楽曲を取得してキューに追加
        # 実装簡略化のため、基本実装のみ
        pass

    def get_player(self, guild_id: int) -> Optional[MusicPlayer]:
        """プレイヤー取得"""
        return self.players.get(guild_id)

    async def get_current_track(self, guild_id: int) -> Dict[str, Any]:
        """現在の楽曲情報取得"""
        player = self.players.get(guild_id)
        if not player or not player.current_track:
            return {}

        track = player.current_track
        return {
            'title': track.title,
            'artist': track.artist,
            'url': track.url,
            'duration': track.duration,
            'position': player.get_position(),
            'thumbnail_url': track.thumbnail_url,
            'source': track.source,  # ソース情報を追加
            'requested_by_name': 'Unknown',  # ユーザー情報は別途取得
            'requested_by_avatar': None
        }

    async def get_session_info(self, guild_id: int) -> Dict[str, Any]:
        """セッション情報取得"""
        player = self.players.get(guild_id)
        if not player:
            return {}

        return {
            'is_paused': player.is_paused(),
            'loop_mode': player.loop_mode.value
        }

    async def get_queue(self, guild_id: int) -> List[Dict[str, Any]]:
        """キュー取得"""
        queue_items = await self.database.get_guild_queue(guild_id)
        return [
            {
                'title': item.get('title', 'Unknown'),
                'artist': item.get('artist', 'Unknown'),
                'duration': item.get('duration', 0)
            }
            for item in queue_items
        ]

    async def connect_voice(self, voice_channel: discord.VoiceChannel, text_channel: Optional[discord.TextChannel] = None) -> bool:
        """ボイスチャンネル接続"""
        try:
            voice_client = await voice_channel.connect()
            player = MusicPlayer(voice_channel.guild.id, voice_client, self)
            self.players[voice_channel.guild.id] = player

            # セッション作成
            text_channel_id = text_channel.id if text_channel else voice_channel.id
            self.logger.debug(f"Database type: {type(self.database)}")
            await self.database.create_session(
                guild_id=voice_channel.guild.id,
                voice_channel_id=voice_channel.id,
                text_channel_id=text_channel_id
            )

            return True
        except Exception as e:
            self.logger.error(f"Voice connect error: {e}")
            return False

    async def disconnect_voice(self, guild_id: int, auto_cleanup: bool = True):
        """ボイスチャンネル切断（自動クリーンアップ付き）"""
        try:
            player = self.players.get(guild_id)
            if player:
                try:
                    if player.voice_client and player.voice_client.is_connected():
                        await player.voice_client.disconnect()
                        self.logger.info(f"Voice client disconnected for guild {guild_id}")
                    else:
                        self.logger.warning(f"Voice client already disconnected for guild {guild_id}")
                except Exception as voice_error:
                    self.logger.error(f"Voice disconnect error for guild {guild_id}: {voice_error}")
                finally:
                    # プレイヤーは確実に削除
                    if guild_id in self.players:
                        del self.players[guild_id]

            if auto_cleanup:
                # 自動クリーンアップ: キューと履歴をリセット
                try:
                    await self._cleanup_guild_data(guild_id)
                except Exception as cleanup_error:
                    self.logger.error(f"Cleanup error for guild {guild_id}: {cleanup_error}")

            # セッション削除
            try:
                await self.database.delete_session(guild_id)
                self.logger.debug(f"Session deleted for guild {guild_id}")
            except Exception as db_error:
                self.logger.error(f"Database session delete error for guild {guild_id}: {db_error}")

        except Exception as e:
            self.logger.error(f"Unexpected error in disconnect_voice for guild {guild_id}: {e}")
            raise

    async def _cleanup_guild_data(self, guild_id: int):
        """ギルドのキューと履歴をクリーンアップ"""
        try:
            # キューをクリア
            cleared_queue = await self.database.clear_queue(guild_id)

            # 楽曲履歴をクリア
            cleared_tracks = await self.database.clear_guild_tracks(guild_id)

            self.logger.info(f"Auto cleanup for guild {guild_id}: {cleared_queue} queue items, {cleared_tracks} tracks cleared")

            # EventBus通知
            await self.event_bus.emit_event("music_data_cleaned", {
                "guild_id": guild_id,
                "cleared_queue_count": cleared_queue,
                "cleared_tracks_count": cleared_tracks,
                "reason": "voice_disconnect"
            })

        except Exception as e:
            self.logger.error(f"Cleanup error for guild {guild_id}: {e}")

    async def _notify_track_failed(self, guild_id: int, track, error_message: str):
        """楽曲再生失敗の通知"""
        try:
            # YouTubeExtractorから制限タイプを判定
            restriction_type = "unknown"
            user_message = "⚠️ 再生できない動画です"

            # エラーメッセージから制限タイプを検出
            if hasattr(self, 'youtube_extractor'):
                restriction_type = self.youtube_extractor._detect_restriction_type(error_message)
                user_message = self.youtube_extractor.get_restriction_message(restriction_type)

            # EventBus通知（ログ記録用）
            await self.event_bus.emit_event("track_failed", {
                "guild_id": guild_id,
                "track_id": track.id,
                "track_title": track.title,
                "track_url": track.url,
                "error_message": error_message,
                "restriction_type": restriction_type,
                "user_message": user_message
            })

            self.logger.warning(f"Track failed in guild {guild_id}: {track.title} - {restriction_type}")

        except Exception as e:
            self.logger.error(f"Error notifying track failure: {e}")

    async def skip_to_next(self, guild_id: int) -> bool:
        """次楽曲にスキップ（UI更新用 - 完了まで待機）"""
        player = self.players.get(guild_id)
        if not player:
            return False

        try:
            # 現在再生中でない場合は何もしない
            if not (player.voice_client.is_playing() or player.voice_client.is_paused()):
                return False

            # スキップ実行
            await player.skip()

            # 次楽曲の再生開始まで最大3秒待機
            for _ in range(30):  # 0.1秒 × 30回 = 3秒
                await asyncio.sleep(0.1)
                if player.voice_client.is_playing():
                    return True

            # タイムアウト
            self.logger.warning(f"Skip timeout for guild {guild_id}")
            return False

        except Exception as e:
            self.logger.error(f"Skip error: {e}")
            return False

    async def _handle_spotify_url(self, url_info: URLInfo) -> Optional[TrackInfo]:
        """Spotify URL処理"""
        if not self.spotify_extractor:
            self.logger.warning("Spotify extractor not available")
            return None

        try:
            if url_info.url_type == "track":
                # 単一楽曲
                spotify_track = await self.spotify_extractor.get_track(url_info.id)
                if spotify_track:
                    # Spotify楽曲情報をYouTube検索クエリに変換
                    return await self.spotify_extractor.spotify_to_youtube(spotify_track)

            elif url_info.url_type == "playlist":
                # プレイリスト（最初の楽曲のみ返す）
                tracks = await self.spotify_extractor.get_playlist_tracks(url_info.id, limit=1)
                if tracks:
                    return tracks[0]

            elif url_info.url_type == "album":
                # アルバム（最初の楽曲のみ返す）
                tracks = await self.spotify_extractor.get_album_tracks(url_info.id, limit=1)
                if tracks:
                    return tracks[0]

            return None

        except Exception as e:
            self.logger.error(f"Spotify URL handling error: {e}")
            return None