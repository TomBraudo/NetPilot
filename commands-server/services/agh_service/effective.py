from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from .common import logger
from .clients import find_client_by_any_id, ensure_client_for_device
from .categories import list_categories, get_category_domains
from .rules import get_current_rules


def _build_domain_to_categories_index() -> Tuple[Optional[Dict[str, List[str]]], Optional[str]]:
    cats, err = list_categories()
    if err:
        return None, err
    index: Dict[str, List[str]] = {}
    for c in cats or []:
        doms, derr = get_category_domains(c)
        if derr:
            continue
        for d in doms or []:
            bucket = index.setdefault(d, [])
            if c not in bucket:
                bucket.append(c)
    return index, None


def get_client_effective_rules(identifier: Dict) -> Tuple[Optional[Dict], Optional[str]]:
    """Return an easy-to-read summary of categories affecting a client by parsing custom rules.

    identifier: {"mac": ".."} or {"ipv4": ".."}
    """
    try:
        mac = (identifier or {}).get('mac')
        ipv4 = (identifier or {}).get('ipv4')
        # Try to find an existing client; if not present, try to ensure to obtain IPv6 name
        client, err = find_client_by_any_id(mac=mac, ipv4=ipv4)
        if not client:
            ensured, e2 = ensure_client_for_device(mac=mac, ipv4_optional=ipv4)
            if e2 or not ensured:
                # No client; return empty categories
                return {"client": None, "categories": [], "sampleRules": [], "estimatedTotalRules": 0}, None
            client = ensured.get('client')

        client_name = client.get('name')
        if not client_name:
            return {"client": None, "categories": [], "sampleRules": [], "estimatedTotalRules": 0}, None

        rules, rerr = get_current_rules()
        if rerr:
            return None, rerr
        rules = rules or []

        # Filter rules for this client
        def _parse_client(rule: str) -> Optional[str]:
            if not isinstance(rule, str):
                return None
            i = rule.find('$client=')
            if i == -1:
                return None
            tail = rule[i + len('$client=') :]
            for sep in [',', ' ']:
                cut = tail.find(sep)
                if cut != -1:
                    tail = tail[:cut]
                    break
            return tail.strip()

        def _parse_domain(rule: str) -> Optional[str]:
            r = rule.strip().lower()
            if not r.startswith('||'):
                return None
            caret = r.find('^', 2)
            if caret == -1:
                return None
            dom = r[2:caret]
            return dom

        device_domains = [(_parse_domain(r) or '') for r in rules if _parse_client(r) == client_name]
        device_domains = [d for d in device_domains if d]

        # Build domain→categories index and compute active categories
        index, ierr = _build_domain_to_categories_index()
        if ierr:
            return None, ierr
        active_cats: Dict[str, int] = {}
        for d in device_domains:
            for c in (index or {}).get(d, []):
                active_cats[c] = active_cats.get(c, 0) + 1

        # Sample the first few rules for UX
        sample_rules = [r for r in rules if _parse_client(r) == client_name][:10]

        return {
            "client": {"name": client_name, "ids": client.get('ids')},
            "categories": sorted(list(active_cats.keys())),
            "sampleRules": sample_rules,
            "estimatedTotalRules": len(device_domains),
        }, None
    except Exception as e:
        logger.error(f"get_client_effective_rules failed: {e}", exc_info=True)
        return None, str(e)


def get_clients_effective_rules(identifiers: List[Dict]) -> Tuple[Optional[List[Dict]], Optional[str]]:
    try:
        results: List[Dict] = []
        for ident in identifiers or []:
            summary, err = get_client_effective_rules(ident)
            if err:
                results.append({"input": ident, "error": err})
            else:
                results.append({"input": ident, "result": summary})
        return results, None
    except Exception as e:
        logger.error(f"get_clients_effective_rules failed: {e}", exc_info=True)
        return None, str(e)


