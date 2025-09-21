"""
画像解析ユーティリティモジュール

Discord画像（アバター、バナー、絵文字等）の解析機能を提供
asyncio.to_thread を使用してイベントループをブロックしない設計
"""

import aiohttp
import asyncio
from PIL import Image
from io import BytesIO
from typing import Dict, Any, Optional, List, Tuple
import logging


class ImageAnalyzer:
    """画像解析のための汎用クラス"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    async def analyze_image(self, image_url: str) -> Dict[str, Any]:
        """
        画像URLから詳細情報を解析

        Args:
            image_url: 解析対象の画像URL

        Returns:
            画像の詳細情報辞書
            - format: 画像形式 (png, jpg, gif, webp)
            - size: ファイルサイズ（バイト）
            - dimensions: (width, height) タプル
            - mode: カラーモード (RGB, RGBA, P, etc.)
            - animated: アニメーション有無
            - dominant_color: 主要色（16進）
        """
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as response:
                    if response.status != 200:
                        self.logger.warning(f"Failed to fetch image: HTTP {response.status}")
                        return {}

                    image_data = await response.read()
                    return await self._analyze_image_data(image_data)

        except Exception as e:
            self.logger.error(f"Image analysis failed for {image_url}: {e}")
            return {}

    def _analyze_image_data_sync(self, image_data: bytes) -> Dict[str, Any]:
        """画像データから詳細情報を抽出（同期版 - スレッドプールで実行）"""
        image = Image.open(BytesIO(image_data))

        info = {
            'format': image.format.lower() if image.format else 'unknown',
            'size': len(image_data),
            'dimensions': image.size,
            'mode': image.mode,
            'animated': getattr(image, 'is_animated', False)
        }

        # 主要色抽出（同期版）
        info['dominant_color'] = self._extract_dominant_color_sync(image)

        return info

    async def _analyze_image_data(self, image_data: bytes) -> Dict[str, Any]:
        """画像データから詳細情報を抽出（非同期版 - イベントループをブロックしない）"""
        try:
            # 同期処理をスレッドプールで実行してイベントループをブロックしない
            return await asyncio.to_thread(self._analyze_image_data_sync, image_data)
        except Exception as e:
            self.logger.error(f"Image data analysis failed: {e}")
            return {}

    def _extract_dominant_color_sync(self, image: Image.Image) -> str:
        """画像から主要色を抽出（同期版 - スレッドプールで実行）"""
        try:
            # パフォーマンス最適化: アスペクト比を保持しつつ最適サイズにリサイズ
            # 高品質リサンプリングアルゴリズムを使用
            original_width, original_height = image.size

            # 最大サイズを32x32に削減（50x50から大幅改善）
            max_size = 32
            if original_width > max_size or original_height > max_size:
                # アスペクト比を保持してリサイズ
                ratio = min(max_size / original_width, max_size / original_height)
                new_width = int(original_width * ratio)
                new_height = int(original_height * ratio)
                small_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            else:
                small_image = image

            # RGBA や P モードを RGB に変換（最適化）
            if small_image.mode in ('RGBA', 'LA', 'P'):
                # 透明度がある場合は白背景にする
                rgb_image = Image.new('RGB', small_image.size, (255, 255, 255))
                if small_image.mode == 'P':
                    small_image = small_image.convert('RGBA')
                rgb_image.paste(small_image, mask=small_image.split()[-1] if small_image.mode in ('RGBA', 'LA') else None)
                small_image = rgb_image
            elif small_image.mode != 'RGB':
                small_image = small_image.convert('RGB')

            # 色を取得（色数を128に削減してパフォーマンス向上）
            colors_raw = small_image.getcolors(maxcolors=128)
            if colors_raw:
                # 最も多く使われている色
                dominant_color = max(colors_raw, key=lambda x: x[0])
                # 型安全性のための明示的チェック
                if len(dominant_color) >= 2 and isinstance(dominant_color[1], (tuple, list)) and len(dominant_color[1]) >= 3:
                    rgb = dominant_color[1]  # Tuple[int, int, int]
                    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                else:
                    return "#808080"  # 予期しない形式の場合
            else:
                return "#808080"  # グレー（デフォルト）

        except Exception as e:
            self.logger.error(f"Color extraction failed: {e}")
            return "#808080"

    async def _extract_dominant_color(self, image: Image.Image) -> str:
        """画像から主要色を抽出（非同期版 - イベントループをブロックしない）"""
        try:
            # 同期処理をスレッドプールで実行してイベントループをブロックしない
            return await asyncio.to_thread(self._extract_dominant_color_sync, image)
        except Exception as e:
            self.logger.error(f"Color extraction failed: {e}")
            return "#808080"

    async def get_image_info_summary(self, image_url: str) -> str:
        """画像情報の要約テキストを生成"""
        info = await self.analyze_image(image_url)

        if not info:
            return "画像情報の取得に失敗しました"

        summary_parts = []

        if info.get('format'):
            summary_parts.append(f"形式: {info['format'].upper()}")

        if info.get('dimensions'):
            w, h = info['dimensions']
            summary_parts.append(f"解像度: {w}×{h}px")

        if info.get('size'):
            size_mb = info['size'] / 1024 / 1024
            if size_mb >= 1:
                summary_parts.append(f"サイズ: {size_mb:.1f}MB")
            else:
                size_kb = info['size'] / 1024
                summary_parts.append(f"サイズ: {size_kb:.1f}KB")

        if info.get('animated'):
            summary_parts.append("アニメーション: あり")

        if info.get('dominant_color'):
            summary_parts.append(f"主要色: {info['dominant_color']}")

        return " | ".join(summary_parts) if summary_parts else "画像情報なし"


# 後方互換性のためのエイリアス
AvatarAnalyzer = ImageAnalyzer