"""
画像解析ユーティリティモジュール

Discord画像（アバター、バナー、絵文字等）の解析機能を提供
"""

import aiohttp
from PIL import Image
from io import BytesIO
from typing import Dict, Any, Optional
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

    async def _analyze_image_data(self, image_data: bytes) -> Dict[str, Any]:
        """画像データから詳細情報を抽出"""
        try:
            image = Image.open(BytesIO(image_data))

            info = {
                'format': image.format.lower() if image.format else 'unknown',
                'size': len(image_data),
                'dimensions': image.size,
                'mode': image.mode,
                'animated': getattr(image, 'is_animated', False)
            }

            # 主要色抽出
            info['dominant_color'] = await self._extract_dominant_color(image)

            return info

        except Exception as e:
            self.logger.error(f"Image data analysis failed: {e}")
            return {}

    async def _extract_dominant_color(self, image: Image.Image) -> str:
        """画像から主要色を抽出"""
        try:
            # パフォーマンスのため小さくリサイズ
            small_image = image.resize((50, 50))

            # RGBA や P モードを RGB に変換
            if small_image.mode in ('RGBA', 'LA', 'P'):
                # 透明度がある場合は白背景にする
                rgb_image = Image.new('RGB', small_image.size, (255, 255, 255))
                if small_image.mode == 'P':
                    small_image = small_image.convert('RGBA')
                rgb_image.paste(small_image, mask=small_image.split()[-1] if small_image.mode in ('RGBA', 'LA') else None)
                small_image = rgb_image
            elif small_image.mode != 'RGB':
                small_image = small_image.convert('RGB')

            # 色を取得
            colors = small_image.getcolors(maxcolors=256)
            if colors:
                # 最も多く使われている色
                dominant_color = max(colors, key=lambda x: x[0])
                rgb = dominant_color[1]
                return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
            else:
                return "#808080"  # グレー（デフォルト）

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