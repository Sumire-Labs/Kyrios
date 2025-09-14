from dependency_injector import containers, providers
from dependency_injector.wiring import Provide, inject

from config.settings import Settings
from database.manager import DatabaseManager
from patterns.observer import EventBus, LoggingObserver, MetricsObserver
from patterns.factory import KyriosCogFactory, ComponentFactory


def _setup_event_bus(event_bus: EventBus, logging_observer: LoggingObserver,
                     metrics_observer: MetricsObserver) -> EventBus:
    """イベントバスにオブザーバーを自動アタッチ"""
    event_bus.attach(logging_observer)
    event_bus.attach(metrics_observer)
    return event_bus


class Container(containers.DeclarativeContainer):
    """DIコンテナ - 全ての依存関係を管理"""

    # 設定プロバイダー
    config = providers.Singleton(Settings)

    # データベースプロバイダー
    database_manager = providers.Singleton(
        DatabaseManager,
        database_path=config.provided.database_path
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
    cog_factory = providers.Singleton(KyriosCogFactory)
    component_factory = providers.Singleton(ComponentFactory)

    # 依存関係の設定
    wired_event_bus = providers.Resource(
        _setup_event_bus,
        event_bus=event_bus,
        logging_observer=logging_observer,
        metrics_observer=metrics_observer
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