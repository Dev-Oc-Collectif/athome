"""Tests for ManagersRegistry — entry-point-based plugin discovery."""

from __future__ import annotations

from unittest.mock import MagicMock
from unittest.mock import patch

import pytest

from athome.definitions.registry import ManagersRegistry


class TestManagersRegistry:
    def test_get_returns_registered_manager(self) -> None:
        mock_cls = MagicMock(return_value=MagicMock())
        mock_ep = MagicMock()
        mock_ep.name = 'myplugin'
        mock_ep.load.return_value = mock_cls

        with patch('athome.registry.importlib.metadata.entry_points', return_value=[mock_ep]):
            registry: ManagersRegistry[MagicMock] = ManagersRegistry('athome.test_managers')
            manager = registry.get('myplugin')

        assert manager is mock_cls.return_value

    def test_get_raises_key_error_for_unknown_name(self) -> None:
        with patch('athome.registry.importlib.metadata.entry_points', return_value=[]):
            registry: ManagersRegistry[MagicMock] = ManagersRegistry('athome.test_managers')
            with pytest.raises(KeyError, match='unknown'):
                registry.get('unknown')

    def test_all_returns_all_registered_managers(self) -> None:
        mock_cls_a = MagicMock(return_value=MagicMock())
        mock_cls_b = MagicMock(return_value=MagicMock())
        ep_a = MagicMock(name='ep_a')
        ep_a.name = 'alpha'
        ep_a.load.return_value = mock_cls_a
        ep_b = MagicMock(name='ep_b')
        ep_b.name = 'beta'
        ep_b.load.return_value = mock_cls_b

        with patch('athome.registry.importlib.metadata.entry_points', return_value=[ep_a, ep_b]):
            registry: ManagersRegistry[MagicMock] = ManagersRegistry('athome.test_managers')
            managers = registry.all()

        assert set(managers) == {'alpha', 'beta'}

    def test_instances_are_cached(self) -> None:
        mock_cls = MagicMock(return_value=MagicMock())
        mock_ep = MagicMock()
        mock_ep.name = 'cached'
        mock_ep.load.return_value = mock_cls

        with patch('athome.registry.importlib.metadata.entry_points', return_value=[mock_ep]):
            registry: ManagersRegistry[MagicMock] = ManagersRegistry('athome.test_managers')
            first = registry.get('cached')
            second = registry.get('cached')

        assert first is second
        assert mock_cls.call_count == 1

    def test_error_message_lists_available_managers(self) -> None:
        mock_cls = MagicMock(return_value=MagicMock())
        mock_ep = MagicMock()
        mock_ep.name = 'existing'
        mock_ep.load.return_value = mock_cls

        with patch('athome.registry.importlib.metadata.entry_points', return_value=[mock_ep]):
            registry: ManagersRegistry[MagicMock] = ManagersRegistry('athome.test_managers')
            with pytest.raises(KeyError, match='existing'):
                registry.get('missing')
