import asyncio
import logging
import yt_dlp  # type: ignore
from typing import Dict, Optional, List, Any
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
        """改善された同期検索処理 (内部使用)"""
        ytdl = yt_dlp.YoutubeDL(params=self.ytdl_opts)  # type: ignore

        try:
            # 検索クエリの強化
            enhanced_query = self._enhance_music_query(query)
            self.logger.debug(f"Enhanced query: '{query}' -> '{enhanced_query}'")

            # 上位10件を取得して最適な結果を選択
            info = ytdl.extract_info(f"ytsearch10:{enhanced_query}", download=False)

            if not info or 'entries' not in info or not info['entries']:
                # 元のクエリでリトライ
                self.logger.warning(f"No results for enhanced query, trying original: {query}")
                info = ytdl.extract_info(f"ytsearch5:{query}", download=False)

                if not info or 'entries' not in info or not info['entries']:
                    return None

            # 音楽コンテンツをフィルタリング
            filtered_entries = self._filter_music_results(info['entries'])

            if not filtered_entries:
                # フィルタ後に何もない場合は、元の結果から最初の1件を使用
                self.logger.warning("No results after filtering, using first original result")
                filtered_entries = [info['entries'][0]] if info['entries'] else []

            if not filtered_entries:
                return None

            # 最適な楽曲を選択
            best_entry = self._select_best_match(filtered_entries, query)

            if not best_entry:
                return None

            # TrackInfo作成
            track_info = TrackInfo(
                title=best_entry.get('title', 'Unknown Title'),
                artist=best_entry.get('uploader', 'Unknown Artist'),
                url=best_entry.get('webpage_url', ''),
                duration=best_entry.get('duration', 0) or 0,
                thumbnail_url=best_entry.get('thumbnail'),
                source="youtube"
            )

            self.logger.info(f"Found track: {track_info.title} by {track_info.artist}")
            return track_info

        except Exception as e:
            self.logger.error(f"YouTube extraction error: {e}")
            return None

    def _enhance_music_query(self, query: str) -> str:
        """音楽検索に特化したクエリ強化"""
        # 既にアーティスト名や楽曲情報が含まれている場合はそのまま
        if any(separator in query for separator in [' - ', ' by ', ' feat.', ' ft.']):
            return query

        # URL形式の場合はそのまま
        if self.is_url(query):
            return query

        # 音楽関連キーワードがすでに含まれている場合はそのまま
        music_indicators = ['music', 'song', 'audio', 'official', 'mv', 'lyric']
        if any(indicator in query.lower() for indicator in music_indicators):
            return query

        # 短いクエリの場合は音楽キーワードを追加
        if len(query.split()) <= 3:
            return f"{query} music OR song"

        return query

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

    def _filter_music_results(self, entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """音楽コンテンツのフィルタリング"""
        filtered = []

        for entry in entries:
            if not entry:
                continue

            title = entry.get('title', '').lower()
            duration = entry.get('duration', 0) or 0

            # Shorts動画を除外
            if '#shorts' in title or 'shorts' in title:
                self.logger.debug(f"Filtered out shorts: {entry.get('title', 'Unknown')}")
                continue

            # 極端に短い動画を除外 (30秒未満)
            if duration < 30:
                self.logger.debug(f"Filtered out too short ({duration}s): {entry.get('title', 'Unknown')}")
                continue

            # 極端に長い動画を除外 (30分以上)
            if duration > 1800:
                self.logger.debug(f"Filtered out too long ({duration}s): {entry.get('title', 'Unknown')}")
                continue

            # 明らかに音楽以外のコンテンツを除外
            exclude_keywords = ['reaction', 'review', 'tutorial', 'gameplay', 'vlog', 'interview']
            if any(keyword in title for keyword in exclude_keywords):
                self.logger.debug(f"Filtered out non-music content: {entry.get('title', 'Unknown')}")
                continue

            filtered.append(entry)

        return filtered

    def _calculate_music_score(self, entry: Dict[str, Any], original_query: str) -> int:
        """楽曲らしさのスコア計算"""
        score = 0
        title = entry.get('title', '').lower()
        uploader = entry.get('uploader', '').lower()
        duration = entry.get('duration', 0) or 0

        # 音楽関連キーワードでスコア加算
        music_keywords = ['music', 'song', 'audio', 'official', 'mv', 'lyric', 'album']
        score += sum(5 for keyword in music_keywords if keyword in title)

        # 公式チャンネル系でスコア加算
        official_keywords = ['official', 'records', 'music', 'entertainment', 'vevo']
        score += sum(3 for keyword in official_keywords if keyword in uploader)

        # 長さによるスコア (1-15分が最適、2-6分が理想)
        if 60 <= duration <= 900:  # 1-15分
            score += 10
            if 120 <= duration <= 360:  # 2-6分 (理想的な楽曲長)
                score += 5

        # 検索クエリとの一致度
        query_words = original_query.lower().split()
        title_words = title.split()

        # 完全一致する単語の数
        matches = sum(1 for word in query_words if word in title)
        score += matches * 3

        # タイトルの長さでスコア調整 (短すぎず長すぎないものを優遇)
        title_length = len(title)
        if 10 <= title_length <= 100:
            score += 2

        self.logger.debug(f"Score {score} for: {entry.get('title', 'Unknown')}")
        return score

    def _select_best_match(self, entries: List[Dict[str, Any]], original_query: str) -> Optional[Dict[str, Any]]:
        """最適な楽曲を選択"""
        if not entries:
            return None

        # 各エントリにスコアを付けて最高スコアを選択
        scored_entries = []
        for entry in entries:
            score = self._calculate_music_score(entry, original_query)
            scored_entries.append((score, entry))

        # スコア順でソート
        scored_entries.sort(key=lambda x: x[0], reverse=True)

        best_score, best_entry = scored_entries[0]
        self.logger.info(f"Selected best match (score: {best_score}): {best_entry.get('title', 'Unknown')}")

        return best_entry

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