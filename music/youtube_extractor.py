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

    def is_spotify_url(self, query: str) -> bool:
        """SpotifyURLかどうかを判定"""
        return ('spotify.com' in query or
                query.startswith('spotify:') or
                'open.spotify.com' in query)

    def get_ffmpeg_options(self) -> Dict[str, str]:
        """FFmpegオプション取得"""
        return self.ffmpeg_opts.copy()

    async def check_video_availability(self, url: str) -> Dict[str, Any]:
        """動画の利用可能性をチェック"""
        try:
            result = await asyncio.to_thread(self._check_availability_sync, url)
            return result
        except Exception as e:
            self.logger.error(f"Availability check error: {e}")
            return {
                "available": False,
                "error": str(e),
                "restriction_type": "unknown"
            }

    def _check_availability_sync(self, url: str) -> Dict[str, Any]:
        """動画利用可能性の同期チェック"""
        ytdl = yt_dlp.YoutubeDL(params=self.ytdl_opts)  # type: ignore

        try:
            # メタデータのみ取得（軽量）
            info = ytdl.extract_info(url, download=False)

            if not info:
                return {
                    "available": False,
                    "error": "No video information found",
                    "restriction_type": "not_found"
                }

            # 制限情報をチェック
            availability_info = {
                "available": True,
                "age_limit": info.get('age_limit', 0),
                "is_live": info.get('is_live', False),
                "availability": info.get('availability', 'public'),
                "duration": info.get('duration', 0),
                "title": info.get('title', 'Unknown'),
                "uploader": info.get('uploader', 'Unknown')
            }

            # 年齢制限チェック
            if info.get('age_limit', 0) > 0:
                availability_info.update({
                    "available": False,
                    "restriction_type": "age_restricted",
                    "age_limit": info.get('age_limit')
                })

            # ライブストリームチェック
            elif info.get('is_live', False):
                availability_info.update({
                    "available": False,
                    "restriction_type": "live_stream"
                })

            # 可用性チェック
            availability = info.get('availability', 'public')
            if availability not in ['public', 'unlisted']:
                availability_info.update({
                    "available": False,
                    "restriction_type": "private_or_restricted",
                    "availability": availability
                })

            return availability_info

        except yt_dlp.DownloadError as e:
            error_str = str(e).lower()
            restriction_type = self._detect_restriction_type(error_str)

            return {
                "available": False,
                "error": str(e),
                "restriction_type": restriction_type
            }

    def _detect_restriction_type(self, error_message: str) -> str:
        """エラーメッセージから制限タイプを検出"""
        error_lower = error_message.lower()

        if any(keyword in error_lower for keyword in ['age', 'sign in', 'login']):
            return "age_restricted"
        elif any(keyword in error_lower for keyword in ['region', 'country', 'location']):
            return "region_blocked"
        elif any(keyword in error_lower for keyword in ['private', 'unavailable']):
            return "private"
        elif any(keyword in error_lower for keyword in ['deleted', 'removed', 'not found']):
            return "deleted"
        elif any(keyword in error_lower for keyword in ['live', 'stream']):
            return "live_stream"
        elif any(keyword in error_lower for keyword in ['embed', 'disabled']):
            return "embed_disabled"
        else:
            return "unknown"

    def get_restriction_message(self, restriction_type: str) -> str:
        """制限タイプに対応するユーザーフレンドリーなメッセージ"""
        messages = {
            "age_restricted": "🔞 年齢制限のため再生できません",
            "region_blocked": "🌍 地域制限のため再生できません",
            "private": "🔒 プライベート動画のため再生できません",
            "deleted": "❌ 動画が削除されています",
            "live_stream": "📺 ライブストリームは対応していません",
            "embed_disabled": "🚫 埋め込み無効のため再生できません",
            "not_found": "❓ 動画が見つかりません",
            "unknown": "⚠️ 再生できない動画です"
        }
        return messages.get(restriction_type, messages["unknown"])

    async def extract_spotify_track(self, spotify_url: str) -> Optional[TrackInfo]:
        """Spotify URLからYouTube音源を取得"""
        try:
            track_info = await asyncio.to_thread(self._extract_spotify_sync, spotify_url)
            return track_info
        except Exception as e:
            self.logger.error(f"Spotify extraction error: {e}")
            return None

    def _extract_spotify_sync(self, spotify_url: str) -> Optional[TrackInfo]:
        """Spotify抽出の同期処理"""
        ytdl = yt_dlp.YoutubeDL(params=self.ytdl_opts)  # type: ignore

        try:
            self.logger.info(f"Extracting Spotify track: {spotify_url}")

            # yt-dlpがSpotifyメタデータを取得してYouTube音源を検索
            info = ytdl.extract_info(spotify_url, download=False)

            if not info:
                return None

            # TrackInfo作成
            track_info = TrackInfo(
                title=info.get('title', 'Unknown Title'),
                artist=info.get('uploader', info.get('artist', 'Unknown Artist')),
                url=info.get('webpage_url', ''),
                duration=info.get('duration', 0) or 0,
                thumbnail_url=info.get('thumbnail'),
                source="spotify"
            )

            self.logger.info(f"Spotify extraction successful: {track_info.title} by {track_info.artist}")
            return track_info

        except Exception as e:
            self.logger.error(f"Spotify sync extraction error: {e}")
            return None

    async def smart_search_with_fallback(self, query: str) -> Optional[TrackInfo]:
        """スマート検索（YouTube→Spotify フォールバック）"""
        try:
            # 1. 通常のYouTube検索
            youtube_result = await self.search_track(query)

            if youtube_result and self._is_high_quality_result(youtube_result):
                self.logger.info(f"High quality YouTube result found for: {query}")
                return youtube_result

            # 2. Spotify フォールバック検索
            self.logger.info(f"Trying Spotify fallback for: {query}")
            spotify_search_query = f"ytsearch:site:youtube.com {query} music OR song"

            # Spotifyで楽曲情報を検索
            enhanced_result = await self.search_track(spotify_search_query)

            if enhanced_result and self._calculate_music_score(enhanced_result.__dict__, query) > 5:
                enhanced_result.source = "spotify_via_youtube"
                self.logger.info(f"Spotify fallback successful for: {query}")
                return enhanced_result

            # 3. 元のYouTube結果を返す（低品質でも）
            self.logger.warning(f"Fallback to original YouTube result for: {query}")
            return youtube_result

        except Exception as e:
            self.logger.error(f"Smart search error: {e}")
            # フォールバック: 通常の検索
            return await self.search_track(query)

    def _is_high_quality_result(self, track_info: TrackInfo) -> bool:
        """楽曲結果が高品質かどうか判定"""
        if not track_info:
            return False

        # 仮のTrackInfoオブジェクトからdict形式に変換
        track_dict = {
            'title': track_info.title,
            'uploader': track_info.artist,
            'duration': track_info.duration
        }

        # 既存のスコアリング機能を活用
        score = self._calculate_music_score(track_dict, track_info.title)

        # スコア5以上を高品質と判定
        return score >= 5