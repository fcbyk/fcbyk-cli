import socket
import psutil

IFACE_RULES = [
    (['vmware', 'vmnet'],         'vmware',     True,  30),
    (['vbox', 'virtualbox'],      'virtualbox', True,  30),
    (['docker', 'wsl'],           'container',  True,  40),
    (['bluetooth'],               'bluetooth',  True,  60),
    (['ethernet', '以太网'],       'ethernet',   False, 10),
    (['wlan', 'wi-fi', '无线'],   'wifi',       False, 10),
    (['loopback'],                'loopback',   True,  100),
]


def detect_iface_type(iface: str) -> tuple[str, bool, int]:
    lname = iface.lower()
    for keywords, t, virtual, prio in IFACE_RULES:
        if any(k in lname for k in keywords):
            return t, virtual, prio
    return 'unknown', False, 50


def get_private_networks() -> list[dict]:
    results = []
    interfaces = psutil.net_if_addrs()

    for iface, addrs in interfaces.items():
        ips = []
        iface_type, is_virtual, priority = detect_iface_type(iface)

        for addr in addrs:
            if addr.family != socket.AF_INET:
                continue

            ip = addr.address

            if ip.startswith('127.'):
                continue
            if ip.startswith('169.254.'):
                continue
            if ip.startswith(('10.', '192.168.', '172.')):
                ips.append(ip)

        if ips:
            results.append({
                "iface": iface,
                "ips": ips,
                "type": iface_type,
                "virtual": is_virtual,
                "priority": priority
            })

    results.sort(key=lambda x: x['priority'])
    
    if not results:
        results.append({
            "iface": "localhost",
            "ips": ["127.0.0.1"],
            "type": "loopback",
            "virtual": True,
            "priority": 100
        })
    
    return results


def ensure_port_available(port: int, host: str = "0.0.0.0") -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((host, int(port)))