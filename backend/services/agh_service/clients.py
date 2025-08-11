from __future__ import annotations

import json
import os
import tempfile
from typing import Dict, List, Optional, Tuple

from .common import (
    logger,
    router_connection_manager,
    _execute,
    CLIENT_STAGING_REMOTE,
    RESP_STAGING_REMOTE,
)
from .net import resolve_ipv6_for_mac


def _fetch_clients() -> Tuple[Optional[Dict], Optional[str]]:
    out, err = _execute("curl -s http://127.0.0.1:3000/control/clients | cat", timeout=30)
    if err and not out:
        return None, err
    try:
        data = json.loads(out or '{}')
        return data, None
    except Exception as e:
        return None, f"Invalid JSON from AGH clients: {e}"


def _find_client_in_list(data: Dict, mac: Optional[str], ipv4: Optional[str]) -> Optional[Dict]:
    items = data.get('clients') if isinstance(data, dict) else None
    if not isinstance(items, list):
        return None
    mac_l = (mac or '').strip().lower()
    ipv4_s = (ipv4 or '').strip()
    for c in items:
        ids = c.get('ids') or []
        ids_l = [str(x).strip().lower() for x in ids]
        if mac_l and mac_l in ids_l:
            return c
        if ipv4_s and ipv4_s in ids_l:
            return c
    return None


def find_client_by_any_id(mac: Optional[str] = None, ipv4: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        data, err = _fetch_clients()
        if err:
            return None, err
        return _find_client_in_list(data or {}, mac, ipv4), None
    except Exception as e:
        logger.error(f"find_client_by_any_id failed: {e}", exc_info=True)
        return None, str(e)


def _prepare_ids_for_client(mac: str, ipv4: Optional[str]) -> List[str]:
    ids: List[str] = []
    # IPv4 optional
    if ipv4 and isinstance(ipv4, str) and ipv4.strip():
        ids.append(ipv4.strip())
    # Resolve IPv6 from neighbor table when possible
    ipv6, _ = resolve_ipv6_for_mac(mac)
    if ipv6:
        ids.append(ipv6)
    # MAC is always included
    ids.append(mac.strip().lower())
    return ids


def ensure_client_with_ids(name: str, mac: str, ipv4_optional: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        if not name or not mac:
            return None, "name and mac are required"
        existing, err = find_client_by_any_id(mac=mac, ipv4=ipv4_optional)
        ids = _prepare_ids_for_client(mac, ipv4_optional)

        # Compose object
        base_obj: Dict = {
            "name": name,
            "ids": ids,
            "filtering_enabled": True,
            "use_global_settings": False,
        }

        # If client exists, merge tags and update; else add
        if existing:
            # Merge existing tags if any
            tags = existing.get('tags') or []
            base_obj["tags"] = tags
            payload = json.dumps(base_obj, ensure_ascii=False)
            with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', newline='\n') as tf:
                tf.write(payload)
                tf.flush()
                local = tf.name
            try:
                success, copy_err = router_connection_manager.copy_file(local, CLIENT_STAGING_REMOTE, False, True)
            finally:
                try:
                    os.unlink(local)
                except Exception:
                    pass
            if not success:
                return None, copy_err or "Failed to stage client payload"
            cmd = (
                "sh -c '"
                "resp_code=$(curl -s -o " + RESP_STAGING_REMOTE + " -w \"%{http_code}\" "
                "-X POST http://127.0.0.1:3000/control/clients/update "
                "-H \"Content-Type: application/json\" --data @" + CLIENT_STAGING_REMOTE + "); "
                "echo $resp_code'"
            )
            out, err = _execute(cmd, timeout=30)
            if err:
                logger.error(f"ensure_client_with_ids update stderr: {err}")
        else:
            payload = json.dumps(base_obj, ensure_ascii=False)
            with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', newline='\n') as tf:
                tf.write(payload)
                tf.flush()
                local = tf.name
            try:
                success, copy_err = router_connection_manager.copy_file(local, CLIENT_STAGING_REMOTE, False, True)
            finally:
                try:
                    os.unlink(local)
                except Exception:
                    pass
            if not success:
                return None, copy_err or "Failed to stage client payload"
            cmd = (
                "sh -c '"
                "resp_code=$(curl -s -o " + RESP_STAGING_REMOTE + " -w \"%{http_code}\" "
                "-X POST http://127.0.0.1:3000/control/clients/add "
                "-H \"Content-Type: application/json\" --data @" + CLIENT_STAGING_REMOTE + "); "
                "echo $resp_code'"
            )
            out, err = _execute(cmd, timeout=30)
            if err:
                logger.error(f"ensure_client_with_ids add stderr: {err}")

        # Read back latest clients and return the matching one
        data, ferr = _fetch_clients()
        if ferr:
            return None, ferr
        return _find_client_in_list(data or {}, mac=mac, ipv4=ipv4_optional), None
    except Exception as e:
        logger.error(f"ensure_client_with_ids failed: {e}", exc_info=True)
        return None, str(e)


def ensure_client_for_device(mac: str, ipv4_optional: Optional[str] = None) -> Tuple[Optional[Dict], Optional[str]]:
    """Ensure a client exists and is named after its IPv6.

    Strict requirement: IPv6 must be resolvable from the neighbor table. If not,
    returns an error instead of falling back to MAC naming.

    Returns {"client": client_dict, "previous_name": str|None}.
    """
    try:
        if not mac:
            return None, "mac is required"
        ipv6, _ = resolve_ipv6_for_mac(mac)
        if not ipv6:
            return None, "IPv6 not found for device MAC; cannot ensure client name"

        existing, err = find_client_by_any_id(mac=mac, ipv4=ipv4_optional)
        prev_name = existing.get('name') if existing else None
        target_name = ipv6
        client, cerr = ensure_client_with_ids(name=target_name, mac=mac, ipv4_optional=ipv4_optional)
        if cerr:
            return None, cerr
        result = {
            "client": client,
            "previous_name": prev_name if prev_name and prev_name != target_name else None,
        }
        return result, None
    except Exception as e:
        logger.error(f"ensure_client_for_device failed: {e}", exc_info=True)
        return None, str(e)


def set_client_tags(client: Dict, tags: List[str]) -> Tuple[Optional[Dict], Optional[str]]:
    try:
        if not isinstance(client, dict):
            return None, "client must be a dict"
        # Recompose full object with updated tags; ids/name needed by AGH
        name = client.get('name') or ''
        ids = client.get('ids') or []
        obj = {
            "name": name,
            "ids": ids,
            "filtering_enabled": True,
            "use_global_settings": False,
            "tags": tags or [],
        }
        payload = json.dumps(obj, ensure_ascii=False)
        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', newline='\n') as tf:
            tf.write(payload)
            tf.flush()
            local = tf.name
        try:
            success, copy_err = router_connection_manager.copy_file(local, CLIENT_STAGING_REMOTE, False, True)
        finally:
            try:
                os.unlink(local)
            except Exception:
                pass
        if not success:
            return None, copy_err or "Failed to stage client payload"
        cmd = (
            "sh -c '"
            "resp_code=$(curl -s -o " + RESP_STAGING_REMOTE + " -w \"%{http_code}\" "
            "-X POST http://127.0.0.1:3000/control/clients/update "
            "-H \"Content-Type: application/json\" --data @" + CLIENT_STAGING_REMOTE + "); "
            "echo $resp_code'"
        )
        out, err = _execute(cmd, timeout=30)
        if err:
            logger.error(f"set_client_tags stderr: {err}")
        # Return updated client by re-fetching and matching
        mac = None
        for i in ids:
            if isinstance(i, str) and ':' in i:
                mac = i.lower()
                break
        data, ferr = _fetch_clients()
        if ferr:
            return None, ferr
        return _find_client_in_list(data or {}, mac=mac, ipv4=None), None
    except Exception as e:
        logger.error(f"set_client_tags failed: {e}", exc_info=True)
        return None, str(e)


