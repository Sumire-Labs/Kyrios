import discord
from discord import app_commands
from discord.ext import commands
import logging
from typing import Optional, Literal
from dependency_injector.wiring import inject, Provide

from core.container import container
from translation import TranslationService, LanguageCodes, TranslationUI, TranslationConstants
from common import EmbedBuilder, UIColors, UIEmojis, UserFormatter


class TranslationView(discord.ui.View):
    """翻訳結果表示用のインタラクティブUI"""

    def __init__(self, translation_service: TranslationService, original_text: str,
                 current_result: dict, user: discord.User):
        super().__init__(timeout=300)
        self.translation_service = translation_service
        self.original_text = original_text
        self.current_result = current_result
        self.user = user


    @discord.ui.button(label="使用量確認", style=discord.ButtonStyle.secondary, emoji="📊")
    async def check_usage(self, interaction: discord.Interaction, button: discord.ui.Button):
        """API使用量を確認"""
        if interaction.user != self.user:
            await interaction.response.send_message("❌ この操作は翻訳を実行したユーザーのみ可能です。", ephemeral=True)
            return

        await interaction.response.defer(ephemeral=True)

        try:
            usage_info = await self.translation_service.get_usage_info()

            if usage_info:
                embed = EmbedBuilder.create_info_embed("📊 DeepL API使用量")

                usage_percentage = usage_info.get("usage_percentage", 0)
                remaining = usage_info.get("character_remaining")

                embed.add_field(
                    name="使用状況",
                    value=f"使用文字数: {usage_info.get('character_count', 0):,}\n"
                          f"制限: {usage_info.get('character_limit', 'unlimited'):,}\n"
                          f"使用率: {usage_percentage:.1f}%",
                    inline=True
                )

                if remaining is not None:
                    embed.add_field(
                        name="残り文字数",
                        value=f"{remaining:,} 文字",
                        inline=True
                    )

                # 使用率に応じて色を変更
                if usage_percentage > 90:
                    embed.color = TranslationUI.COLORS["ERROR"]
                elif usage_percentage > 75:
                    embed.color = discord.Color.orange()
                else:
                    embed.color = TranslationUI.COLORS["SUCCESS"]

                await interaction.followup.send(embed=embed, ephemeral=True)
            else:
                await interaction.followup.send("❌ 使用量情報を取得できませんでした。", ephemeral=True)

        except Exception as e:
            logging.error(f"Usage check failed: {e}")
            await interaction.followup.send("❌ 使用量確認中にエラーが発生しました。", ephemeral=True)


class TranslationCog(commands.Cog):
    """翻訳機能を提供するCog"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.logger = logging.getLogger(__name__)

        # DIコンテナから直接取得
        self.translation_service = container.translation_service()

    @app_commands.command(name="translate", description="テキストを翻訳します")
    @app_commands.describe(
        text="翻訳するテキスト",
        target_lang="翻訳先言語（省略時は日本語）",
        source_lang="翻訳元言語（省略時は自動検出）"
    )
    async def translate(
        self,
        interaction: discord.Interaction,
        text: str,
        target_lang: Optional[Literal[
            "ja", "en-us", "en-gb", "ko", "zh", "fr", "de", "es",
            "it", "pt-br", "ru", "nl", "pl", "sv", "da", "no"
        ]] = "ja",
        source_lang: Optional[Literal[
            "auto", "en", "ja", "ko", "zh", "fr", "de", "es",
            "it", "pt", "ru", "nl", "pl", "sv", "da", "no"
        ]] = "auto"
    ):
        """メイン翻訳コマンド"""
        await interaction.response.defer()

        try:
            # 翻訳サービスが利用可能かチェック
            if not self.translation_service.is_available():
                error_embed = EmbedBuilder.create_error_embed(
                    "翻訳サービス利用不可",
                    "DeepL APIキーが設定されていないか、サービスに接続できません。"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # 入力バリデーション
            if len(text) > TranslationConstants.MAX_TEXT_LENGTH:
                error_embed = EmbedBuilder.create_error_embed(
                    "テキストが長すぎます",
                    f"翻訳できるテキストは{TranslationConstants.MAX_TEXT_LENGTH}文字以内です。"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)
                return

            # 翻訳実行
            result = await self.translation_service.translate(
                text=text,
                target_lang=target_lang,
                source_lang=source_lang,
                user_id=interaction.user.id,
                guild_id=interaction.guild.id if interaction.guild else None
            )

            if result:
                # 翻訳成功
                formatted_result = self.translation_service.format_translation_for_discord(result)

                embed = EmbedBuilder.create_base_embed(
                    title=f"{TranslationUI.EMOJIS['TRANSLATE']} 翻訳結果",
                    color=TranslationUI.COLORS["SUCCESS"]
                )

                # 元テキスト
                embed.add_field(
                    name=f"{TranslationUI.EMOJIS['SOURCE_LANG']} 元テキスト",
                    value=UserFormatter.format_code_block(text[:1000]),
                    inline=False
                )

                # 翻訳結果
                embed.add_field(
                    name=f"{TranslationUI.EMOJIS['TARGET_LANG']} 翻訳結果",
                    value=UserFormatter.format_code_block(formatted_result["translated_text"][:1000]),
                    inline=False
                )

                # 言語情報
                detected_info = ""
                if formatted_result["detected_language"] and source_lang == "auto":
                    detected_info = f"\n検出言語: {formatted_result['detected_language']}"

                embed.add_field(
                    name="📊 翻訳情報",
                    value=f"言語: {formatted_result['source_language']} → {formatted_result['target_language']}{detected_info}\n"
                          f"文字数: {formatted_result['character_count']}",
                    inline=False
                )

                # フッター設定
                EmbedBuilder.set_footer_with_user(embed, interaction.user, "Luna Translation")

                # インタラクティブUIを追加
                view = TranslationView(
                    self.translation_service,
                    text,
                    formatted_result,
                    interaction.user
                )

                await interaction.followup.send(embed=embed, view=view)

            else:
                # 翻訳失敗
                error_embed = EmbedBuilder.create_error_embed(
                    "翻訳に失敗しました",
                    "APIエラーまたはネットワーク接続に問題があります。しばらく時間をおいて再度お試しください。"
                )
                await interaction.followup.send(embed=error_embed, ephemeral=True)

        except Exception as e:
            self.logger.error(f"Translation command error: {e}")
            error_embed = EmbedBuilder.create_error_embed(
                "エラー",
                "翻訳中に予期しないエラーが発生しました。"
            )
            await interaction.followup.send(embed=error_embed, ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(TranslationCog(bot))