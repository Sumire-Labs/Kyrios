import re
from typing import Literal, Optional
from dataclasses import dataclass

@dataclass
class URLInfo:
    """URL情報クラス"""
    source: Literal["youtube", "spotify_track", "spotify_playlist", "spotify_album", "search"]
    url: str
    id: Optional[str] = None
    type: Optional[str] = None

class URLDetector:
    """URL検出・分類器"""

    # Spotify URL パターン
    SPOTIFY_PATTERNS = {
        'track': re.compile(r'https://open\.spotify\.com/track/([a-zA-Z0-9]+)'),
        'playlist': re.compile(r'https://open\.spotify\.com/playlist/([a-zA-Z0-9]+)'),
        'album': re.compile(r'https://open\.spotify\.com/album/([a-zA-Z0-9]+)')
    }

    # YouTube URL パターン
    YOUTUBE_PATTERNS = {
        'video': re.compile(r'https://(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)'),
        'short': re.compile(r'https://youtu\.be/([a-zA-Z0-9_-]+)')
    }

    @classmethod
    def detect_url_type(cls, query: str) -> URLInfo:
        """クエリからURL種別を検出"""
        query = query.strip()

        # 1. Spotify URL チェック
        for spotify_type, pattern in cls.SPOTIFY_PATTERNS.items():
            match = pattern.match(query)
            if match:
                return URLInfo(
                    source=f"spotify_{spotify_type}",
                    url=query,
                    id=match.group(1),
                    type=spotify_type
                )

        # 2. YouTube URL チェック
        for youtube_type, pattern in cls.YOUTUBE_PATTERNS.items():
            match = pattern.match(query)
            if match:
                return URLInfo(
                    source="youtube",
                    url=query,
                    id=match.group(1),
                    type=youtube_type
                )

        # 3. 検索クエリとして扱う
        return URLInfo(
            source="search",
            url=query
        )