import asyncio
import logging
import discord
from typing import Dict, Optional, List, Any
from datetime import datetime
from discord import VoiceClient

from database.models import Track, Queue, MusicSession, MusicSource, LoopMode
from .youtube_extractor import YouTubeExtractor, TrackInfo


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

            # 音量調整は削除済み (UIから音量ボタンを削除したため)

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
        if self.voice_client.is_playing() or self.voice_client.is_paused():
            self.voice_client.stop()
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

        # 次の楽曲を非同期で処理
        try:
            asyncio.create_task(self._handle_track_end())
        except Exception as e:
            self.logger.error(f"Failed to create task for track end: {e}")

    async def _handle_track_end(self):
        """楽曲終了処理"""
        try:
            if self.loop_mode == LoopMode.TRACK and self.current_track:
                # 同じ楽曲をリピート
                await self.play_track(self.current_track)
            else:
                # 次の楽曲へ
                await self.music_service.play_next(self.guild_id)
        except Exception as e:
            self.logger.error(f"Track end handling error: {e}")


class MusicService:
    """音楽システムメインサービス - Kyriosパターン準拠"""

    def __init__(self, database_manager, event_bus, youtube_extractor: YouTubeExtractor):
        self.database = database_manager
        self.event_bus = event_bus
        self.youtube_extractor = youtube_extractor
        self.logger = logging.getLogger(__name__)

        # アクティブプレイヤー管理
        self.players: Dict[int, MusicPlayer] = {}

    async def search_and_add(
        self,
        guild_id: int,
        query: str,
        requested_by: int,
        voice_channel: discord.VoiceChannel
    ) -> TrackInfo:
        """楽曲検索・キュー追加"""
        # YouTube検索
        track_info = await self.youtube_extractor.search_track(query)
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
            source=MusicSource.YOUTUBE
        )

        # キューに追加
        await self.database.add_to_queue(guild_id, track.id, requested_by)

        # EventBus通知
        await self.event_bus.emit_event("track_added", {
            "guild_id": guild_id,
            "track_id": track.id,
            "title": track_info.title,
            "requested_by": requested_by
        })

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

    async def play_next(self, guild_id: int):
        """次の楽曲を再生"""
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
            # 楽曲が見つからない場合、次へ
            await self.database.remove_from_queue(guild_id, queue_item.id)
            await self.play_next(guild_id)
            return

        # 再生開始
        await player.play_track(track)

        # キューから削除
        await self.database.remove_from_queue(guild_id, queue_item.id)

        # セッション更新
        await self.database.update_session_current_track(guild_id, track.id)

        # EventBus通知
        await self.event_bus.emit_event("track_started", {
            "guild_id": guild_id,
            "track_id": track.id,
            "title": track.title
        })

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
            await self.database.create_session(
                guild_id=voice_channel.guild.id,
                voice_channel_id=voice_channel.id,
                text_channel_id=text_channel_id
            )

            return True
        except Exception as e:
            self.logger.error(f"Voice connect error: {e}")
            return False

    async def disconnect_voice(self, guild_id: int):
        """ボイスチャンネル切断"""
        player = self.players.get(guild_id)
        if player:
            await player.voice_client.disconnect()
            del self.players[guild_id]

        # セッション削除
        await self.database.delete_session(guild_id)