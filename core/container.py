from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from .settings import Settings
from database.manager import DatabaseManager
from .observer import EventBus, LoggingObserver, MetricsObserver
from .factory import LunaCogFactory, ComponentFactory
from music.youtube_extractor import YouTubeExtractor
from music.spotify_extractor import SpotifyExtractor
from music.music_service import MusicService
from translation.deepl_extractor import DeepLExtractor
from translation.translation_service import TranslationService


def _setup_event_bus(event_bus: EventBus, logging_observer: LoggingObserver,
                     metrics_observer: MetricsObserver) -> EventBus:
    """イベントバスにオブザーバーを自動アタッチ"""
    event_bus.attach(logging_observer)
    event_bus.attach(metrics_observer)
    return event_bus


async def _initialize_database(database_manager: DatabaseManager) -> DatabaseManager:
    """データベースの非同期初期化"""
    await database_manager.initialize()
    return database_manager


class Container(containers.DeclarativeContainer):
    """DIコンテナ - 全ての依存関係を管理"""

    # 設定プロバイダー
    config = providers.Singleton(Settings)

    # データベースプロバイダー（非同期初期化付き）
    database_manager_raw = providers.Singleton(
        DatabaseManager,
        database_path=config.provided.database_path
    )

    database_manager = providers.Resource(
        _initialize_database,
        database_manager=database_manager_raw
    )

    # イベントバスプロバイダー
    event_bus = providers.Singleton(
        EventBus,
        max_history_size=config.provided.eventbus_max_history_size
    )

    # オブザーバープロバイダー
    logging_observer = providers.Singleton(LoggingObserver)
    metrics_observer = providers.Singleton(MetricsObserver)

    # ファクトリープロバイダー
    cog_factory = providers.Singleton(LunaCogFactory)
    component_factory = providers.Singleton(ComponentFactory)

    # 依存関係の設定
    wired_event_bus = providers.Resource(
        _setup_event_bus,
        event_bus=event_bus,
        logging_observer=logging_observer,
        metrics_observer=metrics_observer
    )

    # 音楽システムプロバイダー
    youtube_extractor = providers.Singleton(YouTubeExtractor)

    spotify_extractor = providers.Singleton(
        SpotifyExtractor,
        client_id=config.provided.spotify_client_id,
        client_secret=config.provided.spotify_client_secret
    )

    music_service = providers.Singleton(
        MusicService,
        database_manager=database_manager_raw,
        event_bus=event_bus,
        youtube_extractor=youtube_extractor,
        spotify_extractor=spotify_extractor
    )

    # 翻訳システムプロバイダー
    deepl_extractor = providers.Singleton(
        DeepLExtractor,
        api_key=config.provided.deepl_api_key,
        is_pro=config.provided.deepl_is_pro
    )

    translation_service = providers.Singleton(
        TranslationService,
        deepl_extractor=deepl_extractor,
        event_bus=event_bus
    )


# DIコンテナのインスタンス
container = Container()


# 依存性注入用のデコレーター
def inject_dependencies(func):
    """関数に依存関係を注入するデコレーター"""
    return inject(func)


# よく使う依存関係のエイリアス
ConfigDep = Provide[Container.config]
DatabaseDep = Provide[Container.database_manager]
EventBusDep = Provide[Container.wired_event_bus]
CogFactoryDep = Provide[Container.cog_factory]
TranslationServiceDep = Provide[Container.translation_service]