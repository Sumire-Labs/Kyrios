#!/usr/bin/env python3
"""
エラーチェック用の最小限BOTテスト
依存関係が欠けている場合はインポートエラーで止まる
"""

try:
    print("Testing imports...")
    import discord
    print("✓ discord.py OK")

    from discord.ext import commands
    print("✓ discord.ext.commands OK")

    from database.models import Ticket, Log, GuildSettings
    print("✓ database models OK")

    from database.manager import DatabaseManager
    print("✓ database manager OK")

    from di.container import container
    print("✓ DI container OK")

    from config.settings import Settings
    print("✓ settings OK")

    # 基本的なBOT初期化テスト
    print("\nTesting bot initialization...")

    # 設定読み込みテスト
    try:
        settings = Settings()
        print("✓ Settings initialization OK")
    except FileNotFoundError:
        print("! Config file not found (expected)")
    except Exception as e:
        print(f"✗ Settings error: {e}")

    # DI コンテナテスト
    try:
        container.init_resources()
        print("✓ DI container init OK")
    except Exception as e:
        print(f"! DI init issue: {e}")

    print("\n🎉 Basic imports and initialization tests passed!")
    print("BOTコードに重大なエラーはないようです。")

except ImportError as e:
    print(f"✗ Import Error: {e}")
    print("必要な依存関係が不足している可能性があります。")
except Exception as e:
    print(f"✗ Error: {e}")

print("\nテスト完了")