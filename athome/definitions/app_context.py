from functools import cache
from typing import TYPE_CHECKING
from typing import TypeVar

from athome.definitions.config import load_config
from athome.definitions.managers.base import BaseManager

from .registry import ManagersRegistry

if TYPE_CHECKING:
    from athome.definitions.config import AthomeConfig

M = TypeVar('M', bound=BaseManager)
R = TypeVar('R', bound=ManagersRegistry)


@cache
class AppContext:

    _registries: dict[str, ManagersRegistry]
    _config: AthomeConfig

    def __init__(self):
        self._registries = {}
        self._load_registries()

        self.config = load_config()
        self._check_integrity()

    def _load_registries(self) -> None:

        for manager_cls in BaseManager.__subclasses__():
            self._registries[manager_cls.NAMESPACE] = ManagersRegistry(manager_cls)

    def _check_integrity(self) -> None:
        """Fusionne la config et les entry points pour chaque domaine."""
        # BaseManager.__subclasses__() retourne [ToolManager, ProfileManager, etc.]
        for namespace, manager_registry in self._registries.items()

            # Récupération de la section TOML associée (ex: config.tools)
            domain_config = getattr(self.config, manager_registry.CONFIG_ATTR, {})

            # Liaison et validation de chaque entrée utilisateur
            for entry_name, entry_value in domain_config.items():
                # Gère le format dict complet ou la string shorthand
                manager_name = getattr(entry_value, 'manager', None) or entry_value

                if manager_name not in available_eps:
                    raise ManagerNotFoundError(manager_cls.DOMAIN_LABEL, manager_name)

                # Chargement dynamique et instanciation immédiate du plugin
                plugin_cls = available_eps[manager_name].load()

                self._registry[manager_cls.NAMESPACE][entry_name] = plugin_cls()

    def get_manager(self, manager_cls: Type[M], entry_name: str) -> M:
        """Récupère l'instance déjà prête depuis le registre."""
        domain_map = self._registry.get(manager_cls, {})

        if entry_name not in domain_map:
            raise EntryNotFoundError(manager_cls.DOMAIN_LABEL, entry_name, list(domain_map.keys()))

        return domain_map[entry_name]
