# Core system components
from .settings import Settings
from .container import Container, container
from .command import Command, CommandInvoker
from .factory import LunaCogFactory, ComponentFactory
from .observer import EventBus, Observer, LoggingObserver, MetricsObserver

# DI aliases
from dependency_injector.wiring import Provide, inject

# よく使う依存関係のエイリアス
ConfigDep = Provide[Container.config]
DatabaseDep = Provide[Container.database_manager]
EventBusDep = Provide[Container.wired_event_bus]
CogFactoryDep = Provide[Container.cog_factory]

# 依存性注入用のデコレーター
def inject_dependencies(func):
    """関数に依存関係を注入するデコレーター"""
    return inject(func)

__all__ = [
    'Settings',
    'Container', 'container',
    'Command', 'CommandInvoker',
    'LunaCogFactory', 'ComponentFactory',
    'EventBus', 'Observer', 'LoggingObserver', 'MetricsObserver',
    'ConfigDep', 'DatabaseDep', 'EventBusDep', 'CogFactoryDep',
    'inject_dependencies'
]