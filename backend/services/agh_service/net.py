from __future__ import annotations

import re
from typing import List, Optional, Tuple

from .common import logger, _execute


def resolve_ipv6s_for_mac(mac_address: str) -> Tuple[List[str], Optional[str]]:
    """Resolve ALL IPv6 addresses for a given MAC from the neighbor table.

    Returns (list_of_ipv6s, error_or_none).
    Prioritizes: REACHABLE global/ULA > REACHABLE link-local > ACTIVE global/ULA > ACTIVE link-local > STALE global/ULA > STALE link-local
    """
    try:
        if not isinstance(mac_address, str) or not mac_address.strip():
            return [], "Invalid MAC address"
        mac = mac_address.strip().lower()
        out, err = _execute("ip -6 neigh | cat")
        if err and not out:
            return [], err

        # Collect all IPv6 addresses for this MAC
        ipv6_addresses = []

        for line in (out or '').splitlines():
            l = line.strip().lower()
            if not l or f"lladdr {mac}" not in l:
                continue
            tokens = l.split()
            if not tokens or len(tokens) < 5:
                continue
            ipv6 = tokens[0].strip()
            # Find state: usually last token, e.g. "REACHABLE", "STALE", "FAILED", "DELAY", "PROBE"
            state = tokens[-1]
            if not re.match(r"^[0-9a-f:]+$", ipv6):
                continue
            
            # Skip FAILED states, but include all others (REACHABLE, STALE, DELAY, PROBE, PERMANENT)
            if state != "failed":
                ipv6_addresses.append(ipv6)

        # Return all found IPv6 addresses
        if ipv6_addresses:
            logger.info(f"resolve_ipv6s_for_mac: found {len(ipv6_addresses)} IPv6 addresses for {mac_address}: {ipv6_addresses}")
            print(f"resolve_ipv6s_for_mac: found {len(ipv6_addresses)} IPv6 addresses for {mac_address}: {ipv6_addresses}")
            return ipv6_addresses, None
        
        return [], "No IPv6 addresses found for MAC"
    except Exception as e:
        logger.error(f"resolve_ipv6s_for_mac failed for {mac_address}: {e}", exc_info=True)
        return [], str(e)


