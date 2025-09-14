from __future__ import annotations

import json
import os
import tempfile
from typing import Dict, List, Optional, Tuple

from .common import logger, router_connection_manager, _execute, RULES_STAGING_REMOTE, RESP_STAGING_REMOTE
from .categories import list_categories, get_category_domains


def build_rules_union() -> Tuple[Optional[List[str]], Optional[str]]:
    try:
        categories, err = list_categories()
        if err:
            return None, err
        categories = categories or []
        rules: List[str] = []
        for cat in categories:
            domains, derr = get_category_domains(cat)
            if derr:
                logger.warning(f"Skipping category {cat}: {derr}")
                continue
            for d in domains or []:
                rules.append(f"||{d}^$client={cat}")
        seen = set()
        uniq: List[str] = []
        for r in rules:
            if r not in seen:
                seen.add(r)
                uniq.append(r)
        return uniq, None
    except Exception as e:
        logger.error(f"build_rules_union failed: {e}", exc_info=True)
        return None, str(e)


def apply_rules(rules: List[str]) -> Tuple[Optional[dict], Optional[str]]:
    try:
        if not isinstance(rules, list):
            return None, "rules must be a list"
        payload = json.dumps({"rules": rules}, ensure_ascii=False)

        with tempfile.NamedTemporaryFile('w', delete=False, encoding='utf-8', newline='\n') as tf:
            tf.write(payload)
            tf.flush()
            local_json = tf.name
        try:
            success, copy_err = router_connection_manager.copy_file(
                local_path=local_json,
                remote_path=RULES_STAGING_REMOTE,
                make_executable=False,
                normalize_crlf=True,
            )
        finally:
            try:
                os.unlink(local_json)
            except Exception:
                pass
        if not success:
            return None, copy_err or "Failed to stage rules payload on router"

        curl_cmd = (
            "sh -c '"
            f"resp_code=$(curl -s -o {RESP_STAGING_REMOTE} -w \"%{{http_code}}\" "
            "-X POST http://127.0.0.1:3000/control/filtering/set_rules "
            "-H \"Content-Type: application/json\" --data @/tmp/netpilot_agh_rules.json); "
            "echo $resp_code'"
        )
        out, err = _execute(curl_cmd, timeout=60)
        http_code = (out or '').strip()
        if err:
            logger.error(f"apply_rules curl stderr: {err}")
        body_out, _ = _execute(f"cat {RESP_STAGING_REMOTE} 2>/dev/null | cat")
        try:
            body = json.loads(body_out or '{}')
        except Exception:
            body = {"raw": (body_out or '').strip()}
        if http_code and http_code.isdigit() and int(http_code) // 100 != 2:
            return None, f"AGH set_rules HTTP {http_code}: {body}"
        return {"http_code": http_code or None, "count": len(rules), "response": body}, None
    except Exception as e:
        logger.error(f"apply_rules failed: {e}", exc_info=True)
        return None, str(e)


def _safe_parse_json(text: str) -> Tuple[Optional[dict], Optional[str]]:
    try:
        return json.loads(text), None
    except Exception as e1:
        # Try to extract the first JSON object or array substring
        s = text
        start = s.find('{')
        end = s.rfind('}')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end+1]), None
            except Exception as e2:
                pass
        start = s.find('[')
        end = s.rfind(']')
        if start != -1 and end != -1 and end > start:
            try:
                return json.loads(s[start:end+1]), None
            except Exception as e3:
                pass
        # Truncate output for error readability
        snippet = (text[:200] + '...') if len(text) > 200 else text
        return None, f"Invalid JSON from AGH: {e1}. Raw: {snippet}"


def get_current_rules() -> Tuple[Optional[List[str]], Optional[str]]:
    try:
        # Read rules from AGH YAML config file instead of API
        out, err = _execute("cat /opt/AdGuardHome/AdGuardHome.yaml 2>/dev/null | grep -A 1000 'user_rules:' | grep -E '^  - ' | sed 's/^  - //' | sed \"s/^'//\" | sed \"s/'$//\"", timeout=30)
        if err and not out:
            return None, err
        
        # Parse the rules from YAML format
        rules = []
        for line in (out or '').strip().split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                rules.append(line)
        
        logger.info(f"get_current_rules: Found {len(rules)} existing rules in YAML")
        return rules, None
    except Exception as e:
        logger.error(f"get_current_rules failed: {e}", exc_info=True)
        return None, str(e)


# ---------------------------------------------------------------------------
# Per-client rule application with preservation of other clients' rules
# ---------------------------------------------------------------------------

def _parse_client_from_rule(rule: str) -> Optional[str]:
    """Extract $client value from an ABP rule like '||d^$client=Name[,...]'.
    Returns client name if present and not a negation (~), else None.
    """
    if not isinstance(rule, str):
        return None
    idx = rule.find('$client=')
    if idx == -1:
        return None
    tail = rule[idx + len('$client='):]
    # stop at comma or end
    for sep in [',', ' ']:
        cut = tail.find(sep)
        if cut != -1:
            tail = tail[:cut]
            break
    val = tail.strip()
    if not val or val.startswith('~'):
        return None
    return val


def _sanitize_domain_token(token: str) -> Optional[str]:
    if not isinstance(token, str):
        return None
    s = token.strip().lower()
    if not s:
        return None
    # remove abp markers if provided
    if s.startswith('||'):
        s = s[2:]
    if s.endswith('^'):
        s = s[:-1]
    # basic domain filter
    import re
    if not re.match(r'^[a-z0-9.-]+$', s):
        return None
    if re.match(r'^\d+\.\d+\.\d+\.\d+$', s):
        return None
    return s


def _parse_domain_from_rule(rule: str) -> Optional[str]:
    """Extract domain from an ABP rule of form '||domain^...'."""
    if not isinstance(rule, str):
        return None
    rule = rule.strip().lower()
    if not rule.startswith('||'):
        return None
    caret = rule.find('^', 2)
    if caret == -1:
        return None
    dom = rule[2:caret]
    return _sanitize_domain_token(dom)


def apply_rules_for_clients(client_to_domains: Dict[str, List[str]]) -> Tuple[Optional[dict], Optional[str]]:
    """Apply per-client rules while preserving existing rules for other clients.

    Steps:
    1) Fetch current rules; preserve rules for non-target devices; drop all rules for target devices.
    2) Generate new rules for target devices from input categories/domains.
    3) Combine preserved + generated, dedupe, and POST via set_rules.
    """
    try:
        existing_rules, err = get_current_rules()
        if err:
            # If we can't fetch, treat as empty to avoid destructive behavior
            logger.warning(f"apply_rules_for_clients: get_current_rules error: {err}; proceeding with empty base")
            existing_rules = []
        existing_rules = existing_rules or []

        # Determine clients to update
        target_clients = {str(k).strip() for k in (client_to_domains or {}).keys() if str(k).strip()}

        # Preserve rules: keep non-target clients; for target clients keep rules whose domain is not in provided domain list
        preserved: List[str] = []
        # Precompute domain sets per target client
        target_domains_by_client: Dict[str, set] = {
            str(k).strip(): {d for d in (v or []) if _sanitize_domain_token(d)}
            for k, v in (client_to_domains or {}).items()
            if str(k).strip()
        }
        for r in existing_rules:
            cli = _parse_client_from_rule(r)
            if not cli or cli not in target_clients:
                preserved.append(r)
                continue
            # Within target client: preserve only if domain not managed
            dom = _parse_domain_from_rule(r)
            if dom and dom not in target_domains_by_client.get(cli, set()):
                preserved.append(r)

        # Generate new rules for targets
        generated: List[str] = []
        for client_name, domains in (client_to_domains or {}).items():
            cname = str(client_name).strip()
            if not cname:
                continue
            for d in domains or []:
                sd = _sanitize_domain_token(d)
                if not sd:
                    continue
                generated.append(f"||{sd}^$client={cname}")

        # Combine and deduplicate
        combined: List[str] = []
        seen = set()
        for r in preserved + generated:
            if r not in seen:
                seen.add(r)
                combined.append(r)

        return apply_rules(combined)
    except Exception as e:
        logger.error(f"apply_rules_for_clients failed: {e}", exc_info=True)
        return None, str(e)


def clear_rules_for_clients(client_names: List[str]) -> Tuple[Optional[dict], Optional[str]]:
    """Remove all rules for the given clients and preserve others, then apply.

    - Fetch current rules
    - Preserve only rules whose $client is not in client_names (or have no $client)
    - Apply preserved set
    """
    try:
        existing_rules, err = get_current_rules()
        if err:
            logger.warning(f"clear_rules_for_clients: get_current_rules error: {err}; proceeding with empty base")
            existing_rules = []
        existing_rules = existing_rules or []
        targets = {str(n).strip() for n in (client_names or []) if str(n).strip()}
        preserved: List[str] = []
        for r in existing_rules:
            cli = _parse_client_from_rule(r)
            if not cli or cli not in targets:
                preserved.append(r)
        return apply_rules(preserved)
    except Exception as e:
        logger.error(f"clear_rules_for_clients failed: {e}", exc_info=True)
        return None, str(e)

