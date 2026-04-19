from __future__ import annotations

import socket
from unittest.mock import MagicMock, patch

import pytest

from bykcli.api.network import (
    detect_iface_type,
    ensure_port_available,
    get_private_networks,
)


class TestDetectIfaceType:
    def test_vmware_interface(self):
        result = detect_iface_type("vmware0")
        assert result == ("vmware", True, 30)

    def test_vmnet_interface(self):
        result = detect_iface_type("vmnet1")
        assert result == ("vmware", True, 30)

    def test_vbox_interface(self):
        result = detect_iface_type("vboxnet0")
        assert result == ("virtualbox", True, 30)

    def test_virtualbox_interface(self):
        result = detect_iface_type("virtualbox0")
        assert result == ("virtualbox", True, 30)

    def test_docker_interface(self):
        result = detect_iface_type("docker0")
        assert result == ("container", True, 40)

    def test_wsl_interface(self):
        result = detect_iface_type("wsl")
        assert result == ("container", True, 40)

    def test_bluetooth_interface(self):
        result = detect_iface_type("bluetooth0")
        assert result == ("bluetooth", True, 60)

    def test_ethernet_interface(self):
        result = detect_iface_type("ethernet0")
        assert result == ("ethernet", False, 10)

    def test_chinese_ethernet_interface(self):
        result = detect_iface_type("以太网")
        assert result == ("ethernet", False, 10)

    def test_wlan_interface(self):
        result = detect_iface_type("wlan0")
        assert result == ("wifi", False, 10)

    def test_wifi_interface(self):
        result = detect_iface_type("wi-fi")
        assert result == ("wifi", False, 10)

    def test_chinese_wifi_interface(self):
        result = detect_iface_type("无线网络")
        assert result == ("wifi", False, 10)

    def test_loopback_interface(self):
        result = detect_iface_type("loopback0")
        assert result == ("loopback", True, 100)

    def test_unknown_interface(self):
        result = detect_iface_type("unknown0")
        assert result == ("unknown", False, 50)

    def test_case_insensitive(self):
        result = detect_iface_type("DOCKER0")
        assert result == ("container", True, 40)


class TestGetPrivateNetworks:
    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_empty_interfaces(self, mock_net_if_addrs):
        mock_net_if_addrs.return_value = {}
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["iface"] == "localhost"
        assert result[0]["ips"] == ["127.0.0.1"]

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_loopback_only(self, mock_net_if_addrs):
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "127.0.0.1"
        mock_net_if_addrs.return_value = {"lo0": [mock_addr]}
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["iface"] == "localhost"

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_link_local_only(self, mock_net_if_addrs):
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "169.254.1.1"
        mock_net_if_addrs.return_value = {"eth0": [mock_addr]}
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["iface"] == "localhost"

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_private_ip_10(self, mock_net_if_addrs):
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "10.0.0.1"
        mock_net_if_addrs.return_value = {"eth0": [mock_addr]}
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["iface"] == "eth0"
        assert result[0]["ips"] == ["10.0.0.1"]
        assert result[0]["type"] == "unknown"

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_private_ip_192_168(self, mock_net_if_addrs):
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "192.168.1.1"
        mock_net_if_addrs.return_value = {"wlan0": [mock_addr]}
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["iface"] == "wlan0"
        assert result[0]["ips"] == ["192.168.1.1"]
        assert result[0]["type"] == "wifi"

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_private_ip_172(self, mock_net_if_addrs):
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "172.16.0.1"
        mock_net_if_addrs.return_value = {"eth0": [mock_addr]}
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["ips"] == ["172.16.0.1"]

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_ipv6_skipped(self, mock_net_if_addrs):
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET6
        mock_addr.address = "fe80::1"
        mock_net_if_addrs.return_value = {"eth0": [mock_addr]}
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["iface"] == "localhost"

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_multiple_ips_on_interface(self, mock_net_if_addrs):
        mock_addr1 = MagicMock()
        mock_addr1.family = socket.AF_INET
        mock_addr1.address = "192.168.1.1"
        mock_addr2 = MagicMock()
        mock_addr2.family = socket.AF_INET
        mock_addr2.address = "10.0.0.1"
        mock_net_if_addrs.return_value = {"eth0": [mock_addr1, mock_addr2]}
        result = get_private_networks()
        assert len(result) == 1
        assert result[0]["ips"] == ["192.168.1.1", "10.0.0.1"]

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_priority_sorting(self, mock_net_if_addrs):
        mock_addr1 = MagicMock()
        mock_addr1.family = socket.AF_INET
        mock_addr1.address = "192.168.1.1"
        mock_addr2 = MagicMock()
        mock_addr2.family = socket.AF_INET
        mock_addr2.address = "10.0.0.1"
        mock_net_if_addrs.return_value = {
            "docker0": [mock_addr1],
            "eth0": [mock_addr2],
        }
        result = get_private_networks()
        assert len(result) == 2
        # Results are sorted by priority, lower is higher priority
        priorities = [r["priority"] for r in result]
        assert priorities == sorted(priorities)

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_virtual_flag(self, mock_net_if_addrs):
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "192.168.1.1"
        mock_net_if_addrs.return_value = {"docker0": [mock_addr]}
        result = get_private_networks()
        assert result[0]["virtual"] is True

    @patch("bykcli.api.network.psutil.net_if_addrs")
    def test_non_virtual_flag(self, mock_net_if_addrs):
        mock_addr = MagicMock()
        mock_addr.family = socket.AF_INET
        mock_addr.address = "192.168.1.1"
        mock_net_if_addrs.return_value = {"eth0": [mock_addr]}
        result = get_private_networks()
        assert result[0]["virtual"] is False


class TestEnsurePortAvailable:
    def test_port_available(self):
        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
            mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)
            ensure_port_available(8080)
            mock_socket.bind.assert_called_once_with(("0.0.0.0", 8080))

    def test_custom_host(self):
        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
            mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)
            ensure_port_available(3000, host="127.0.0.1")
            mock_socket.bind.assert_called_once_with(("127.0.0.1", 3000))

    def test_port_as_string(self):
        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
            mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)
            ensure_port_available("8080")
            mock_socket.bind.assert_called_once_with(("0.0.0.0", 8080))

    def test_socket_options_set(self):
        with patch("socket.socket") as mock_socket_class:
            mock_socket = MagicMock()
            mock_socket_class.return_value.__enter__ = MagicMock(return_value=mock_socket)
            mock_socket_class.return_value.__exit__ = MagicMock(return_value=False)
            ensure_port_available(8080)
            mock_socket.setsockopt.assert_called_once_with(
                socket.SOL_SOCKET, socket.SO_REUSEADDR, 1
            )
