from athome.definitions.config import load_config
from athome.definitions.managers import BaseManager
from athome.definitions.registry import ManagersRegistry
from athome.exceptions import EntryNotFoundError
from athome.exceptions import ManagerNotFoundError


class ManagerResolver[M: BaseManager]:
    """A resolver."""

    cfg = load_config()

    def __init__(self, manager_cls: type[M]):
        # Extraction automatique des métadonnées de la classe
        self.domain_label: str = manager_cls.DOMAIN_LABEL
        self.config_attr: str = manager_cls.CONFIG_ATTR
        self.registry = ManagersRegistry(manager_type=manager_cls)

    def resolve(self, name: str) -> M:
        cfg = load_config()
        domain_dict = getattr(cfg, self.config_attr, {})

        if entry := domain_dict.get(name):
            raise EntryNotFoundError(self.domain_label, name, list(domain_dict.keys()))

        manager_name = getattr(entry, 'manager', None) or entry

        try:
            return self.registry.get(manager_name)
        except KeyError as err:
            raise ManagerNotFoundError(self.domain_label, manager_name) from err
