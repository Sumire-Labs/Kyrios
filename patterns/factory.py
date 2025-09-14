from abc import ABC, abstractmethod
from typing import Dict, Type, Any, Optional
import logging


class CogFactory(ABC):
    @abstractmethod
    def create_cog(self, cog_type: str, **kwargs) -> Any:
        pass


class KyriosCogFactory(CogFactory):
    def __init__(self):
        self._cog_registry: Dict[str, Type] = {}
        self.logger = logging.getLogger(__name__)

    def register_cog(self, cog_type: str, cog_class: Type) -> None:
        self._cog_registry[cog_type] = cog_class
        self.logger.info(f"Registered cog type: {cog_type}")

    def create_cog(self, cog_type: str, **kwargs) -> Any:
        if cog_type not in self._cog_registry:
            raise ValueError(f"Unknown cog type: {cog_type}")

        cog_class = self._cog_registry[cog_type]
        try:
            return cog_class(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to create cog {cog_type}: {e}")
            raise

    def get_available_cogs(self) -> list:
        return list(self._cog_registry.keys())

    def is_cog_registered(self, cog_type: str) -> bool:
        return cog_type in self._cog_registry


class ComponentFactory:
    def __init__(self):
        self._component_registry: Dict[str, Type] = {}
        self.logger = logging.getLogger(__name__)

    def register_component(self, component_type: str, component_class: Type) -> None:
        self._component_registry[component_type] = component_class
        self.logger.info(f"Registered component type: {component_type}")

    def create_component(self, component_type: str, **kwargs) -> Any:
        if component_type not in self._component_registry:
            raise ValueError(f"Unknown component type: {component_type}")

        component_class = self._component_registry[component_type]
        try:
            return component_class(**kwargs)
        except Exception as e:
            self.logger.error(f"Failed to create component {component_type}: {e}")
            raise

    def get_available_components(self) -> list:
        return list(self._component_registry.keys())