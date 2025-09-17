import asyncio
import logging
import yt_dlp  # type: ignore
from typing import Dict, Optional, List
from dataclasses import dataclass


@dataclass
class TrackInfo:
    """楽曲情報を格納するデータクラス"""
    title: str
    artist: str
    url: str
    duration: int
    thumbnail_url: Optional[str] = None
    source: str = "youtube"


class YouTubeExtractor:
    """YouTube音楽抽出器 - Kyriosパターン準拠"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # yt-dlp設定 - 高品質音声用（修正版）
        self.ytdl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            # postprocessorsを削除（Discord.pyで直接ストリームを使用するため不要）
        }

        # FFmpeg設定 - シンプル版（ノイズ対策）
        self.ffmpeg_opts = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
            'options': '-vn -ar 48000 -ac 2 -b:a 128k'
        }

    async def search_track(self, query: str) -> Optional[TrackInfo]:
        """楽曲検索 (非同期) - 単一結果"""
        try:
            # asyncio.to_thread でノンブロッキング実行
            track_info = await asyncio.to_thread(self._search_sync, query)
            return track_info
        except Exception as e:
            self.logger.error(f"YouTube search error: {e}")
            return None

    async def search_multiple(self, query: str, limit: int = 5) -> List[TrackInfo]:
        """楽曲複数検索 (検索結果選択用)"""
        try:
            tracks = await asyncio.to_thread(self._search_multiple_sync, query, limit)
            return tracks
        except Exception as e:
            self.logger.error(f"YouTube multiple search error: {e}")
            return []

    def _search_sync(self, query: str) -> Optional[TrackInfo]:
        """同期検索処理 (内部使用)"""
        ytdl = yt_dlp.YoutubeDL(params=self.ytdl_opts)  # type: ignore

        try:
            # YouTube検索
            info = ytdl.extract_info(f"ytsearch:{query}", download=False)

            if not info or 'entries' not in info or not info['entries']:
                return None

            entry = info['entries'][0]

            # TrackInfo作成
            track_info = TrackInfo(
                title=entry.get('title', 'Unknown Title'),
                artist=entry.get('uploader', 'Unknown Artist'),
                url=entry.get('webpage_url', ''),
                duration=entry.get('duration', 0) or 0,
                thumbnail_url=entry.get('thumbnail'),
                source="youtube"
            )

            self.logger.info(f"Found track: {track_info.title} by {track_info.artist}")
            return track_info

        except Exception as e:
            self.logger.error(f"YouTube extraction error: {e}")
            return None

    def _search_multiple_sync(self, query: str, limit: int) -> List[TrackInfo]:
        """複数検索の同期処理"""
        ytdl = yt_dlp.YoutubeDL(params=self.ytdl_opts)  # type: ignore
        tracks = []

        try:
            # 複数検索
            info = ytdl.extract_info(f"ytsearch{limit}:{query}", download=False)

            if not info or 'entries' not in info:
                return tracks

            for entry in info['entries']:
                if entry:
                    track_info = TrackInfo(
                        title=entry.get('title', 'Unknown Title'),
                        artist=entry.get('uploader', 'Unknown Artist'),
                        url=entry.get('webpage_url', ''),
                        duration=entry.get('duration', 0) or 0,
                        thumbnail_url=entry.get('thumbnail'),
                        source="youtube"
                    )
                    tracks.append(track_info)

        except Exception as e:
            self.logger.error(f"YouTube multiple search error: {e}")

        return tracks

    async def get_audio_source(self, url: str) -> Optional[str]:
        """音声ソースURL取得 (discord.py用)"""
        try:
            audio_url = await asyncio.to_thread(self._get_audio_source_sync, url)
            return audio_url
        except Exception as e:
            self.logger.error(f"Audio source extraction error: {e}")
            return None

    def _get_audio_source_sync(self, url: str) -> Optional[str]:
        """音声ソース取得の同期処理"""
        ytdl = yt_dlp.YoutubeDL(params=self.ytdl_opts)  # type: ignore

        try:
            info = ytdl.extract_info(url, download=False)
            if info and 'url' in info:
                return info['url']
        except Exception as e:
            self.logger.error(f"Audio URL extraction error: {e}")

        return None

    def is_url(self, query: str) -> bool:
        """URLかどうかを判定"""
        return query.startswith(('http://', 'https://'))

    def get_ffmpeg_options(self) -> Dict[str, str]:
        """FFmpegオプション取得"""
        return self.ffmpeg_opts.copy()