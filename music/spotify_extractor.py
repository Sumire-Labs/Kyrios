import asyncio
import logging
from typing import Dict, Optional, List, Any
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from .youtube_extractor import YouTubeExtractor, TrackInfo


class SpotifyExtractor:
    """Spotify API統合 - 楽曲情報取得とYouTube変換"""

    def __init__(self, client_id: str, client_secret: str):
        self.logger = logging.getLogger(__name__)
        self.youtube_extractor = YouTubeExtractor()

        try:
            # Spotify API認証
            credentials = SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
            self.spotify = spotipy.Spotify(client_credentials_manager=credentials)
            self.logger.info("Spotify API initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Spotify API: {e}")
            raise

    async def search_track(self, query: str) -> Optional[Dict[str, Any]]:
        """Spotify楽曲検索"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self.spotify.search(q=query, type='track', limit=1)
            )

            if result['tracks']['items']:
                return result['tracks']['items'][0]
            return None
        except Exception as e:
            self.logger.error(f"Spotify search failed: {e}")
            return None

    async def get_track(self, track_id: str) -> Optional[Dict[str, Any]]:
        """Spotify楽曲情報取得"""
        try:
            loop = asyncio.get_event_loop()
            track = await loop.run_in_executor(
                None,
                lambda: self.spotify.track(track_id)
            )
            return track
        except Exception as e:
            self.logger.error(f"Failed to get Spotify track {track_id}: {e}")
            return None

    async def get_playlist(self, playlist_id: str) -> Optional[Dict[str, Any]]:
        """Spotifyプレイリスト取得"""
        try:
            loop = asyncio.get_event_loop()
            playlist = await loop.run_in_executor(
                None,
                lambda: self.spotify.playlist(playlist_id)
            )
            return playlist
        except Exception as e:
            self.logger.error(f"Failed to get Spotify playlist {playlist_id}: {e}")
            return None

    async def get_album(self, album_id: str) -> Optional[Dict[str, Any]]:
        """Spotifyアルバム取得"""
        try:
            loop = asyncio.get_event_loop()
            album = await loop.run_in_executor(
                None,
                lambda: self.spotify.album(album_id)
            )
            return album
        except Exception as e:
            self.logger.error(f"Failed to get Spotify album {album_id}: {e}")
            return None

    async def spotify_to_youtube(self, spotify_track: Dict[str, Any]) -> Optional[TrackInfo]:
        """Spotify楽曲情報からYouTube検索して変換"""
        try:
            # Spotify情報からYouTube検索クエリ作成
            artist = spotify_track['artists'][0]['name']
            title = spotify_track['name']
            search_query = f"{artist} {title}"

            self.logger.info(f"Converting Spotify track to YouTube: {search_query}")

            # YouTube検索
            youtube_tracks = await self.youtube_extractor.search_tracks(search_query, limit=1)
            if youtube_tracks:
                track_info = youtube_tracks[0]

                # Spotify情報を追加
                track_info.artist = artist  # Spotify側の正確な情報を使用
                track_info.title = title

                # 追加のSpotify情報を格納（TrackInfoを拡張する必要があるが、とりあえずコメントで残す）
                # track_info.spotify_id = spotify_track['id']
                # track_info.spotify_url = spotify_track['external_urls']['spotify']
                # track_info.album_name = spotify_track['album']['name']

                self.logger.info(f"Successfully converted: {track_info.title} - {track_info.artist}")
                return track_info

            self.logger.warning(f"No YouTube match found for: {search_query}")
            return None

        except Exception as e:
            self.logger.error(f"Failed to convert Spotify track to YouTube: {e}")
            return None

    async def get_playlist_tracks(self, playlist_id: str) -> List[Dict[str, Any]]:
        """プレイリストの全楽曲を取得"""
        try:
            playlist = await self.get_playlist(playlist_id)
            if not playlist:
                return []

            tracks = []
            items = playlist['tracks']['items']

            for item in items:
                if item['track'] and not item['track']['is_local']:  # ローカルファイルを除外
                    tracks.append(item['track'])

            self.logger.info(f"Retrieved {len(tracks)} tracks from playlist")
            return tracks

        except Exception as e:
            self.logger.error(f"Failed to get playlist tracks: {e}")
            return []

    async def get_album_tracks(self, album_id: str) -> List[Dict[str, Any]]:
        """アルバムの全楽曲を取得"""
        try:
            album = await self.get_album(album_id)
            if not album:
                return []

            tracks = []
            items = album['tracks']['items']

            for item in items:
                # アルバム情報を楽曲に追加
                item['album'] = {
                    'id': album['id'],
                    'name': album['name'],
                    'images': album['images']
                }
                tracks.append(item)

            self.logger.info(f"Retrieved {len(tracks)} tracks from album")
            return tracks

        except Exception as e:
            self.logger.error(f"Failed to get album tracks: {e}")
            return []