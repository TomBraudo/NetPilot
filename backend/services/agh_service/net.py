from __future__ import annotations

import re
from typing import Optional, Tuple

from .common import logger, _execute


def resolve_ipv6_for_mac(mac_address: str) -> Tuple[Optional[str], Optional[str]]:
    """Resolve an IPv6 address for a given MAC from the neighbor table.

    Returns (ipv6_or_none, error_or_none).
    """
    try:
        if not isinstance(mac_address, str) or not mac_address.strip():
            return None, "Invalid MAC address"
        mac = mac_address.strip().lower()
        out, err = _execute("ip -6 neigh | cat")
        if err and not out:
            return None, err
        for line in (out or '').splitlines():
            l = line.strip().lower()
            if not l:
                continue
            if f"lladdr {mac}" in l:
                tokens = l.split()
                if tokens:
                    ipv6 = tokens[0].strip()
                    if re.match(r"^[0-9a-f:]+$", ipv6):
                        return ipv6, None
        return None, None
    except Exception as e:
        logger.error(f"resolve_ipv6_for_mac failed for {mac_address}: {e}", exc_info=True)
        return None, str(e)


