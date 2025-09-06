from typing import Dict, List, Optional, Set, Tuple
import ipaddress
import re
import threading

from utils.logging_config import get_logger
from managers.router_connection_manager import RouterConnectionManager


logger = get_logger('services.nft_qos_service')
router_connection_manager = RouterConnectionManager()

_commit_lock = threading.RLock()


def convert_mbps_to_kbytes(value_mbps: int) -> int:
    """Convert Mbps to kbytes/second. Enforces minimum of 1 kB/s."""
    try:
        value = int(value_mbps)
    except Exception:
        return 1
    return max(1, int(value * 114))


def ensure_nft_qos_installed() -> None:
    """Best-effort installation of nft-qos. Logs errors but does not raise."""
    command = "opkg status nft-qos >/dev/null 2>&1 || (opkg update && opkg install -y nft-qos)"
    out, err = router_connection_manager.execute(command)
    if err:
        logger.warning(f"nft-qos install check/install reported: {err}")


def _execute(command: str) -> Tuple[Optional[str], Optional[str]]:
    return router_connection_manager.execute(command)


def _run_commands(commands: List[str]) -> List[Tuple[str, Optional[str]]]:
    results: List[Tuple[str, Optional[str]]] = []
    for cmd in commands:
        out, err = _execute(cmd)
        if err:
            logger.error(f"Command failed: {cmd} | err={err}")
            results.append((cmd, err))
        else:
            if out:
                logger.debug(f"Command output: {cmd} => {out}")
            results.append((cmd, None))
    return results


def commit_and_restart() -> Dict:
    """Commit nft-qos config and restart service. Serialized to avoid interleaving."""
    with _commit_lock:
        commands = [
            "uci commit nft-qos",
            "/etc/init.d/nft-qos restart | cat",
        ]
        failures = [res for res in _run_commands(commands) if res[1]]
        return {"success": len(failures) == 0, "failures": failures}


def list_existing_sections() -> Dict[str, Dict[str, Dict[str, str]]]:
    """Return a structured map of nft-qos sections and their options.

    Output format:
    {
      "download": { "@download[0]": {"ipaddr":"192.168.1.10", ...}, ... },
      "upload":   { "@upload[1]":   {"ipaddr":"192.168.1.20", ...}, ... },
      "other":    { "sectionName":  {"option":"value", ...}, ... }
    }
    """
    out, err = _execute("uci show nft-qos | cat")
    if err:
        logger.warning(f"uci show nft-qos error: {err}")
        return {"download": {}, "upload": {}, "other": {}}

    sections: Dict[str, Dict[str, Dict[str, str]]] = {
        "download": {},
        "upload": {},
        "other": {},
    }

    type_by_ref: Dict[str, str] = {}
    line_re = re.compile(r"^nft-qos\.(?P<ref>[^.=]+)(?:\.(?P<option>[^=]+))?=(?P<value>.*)$")

    for raw in out.splitlines():
        m = line_re.match(raw.strip())
        if not m:
            continue
        ref = m.group("ref")
        option = m.group("option")
        value = m.group("value").strip()
        if value.startswith("'") and value.endswith("'"):
            value = value[1:-1]

        if option is None:
            # Type line, e.g., nft-qos.@download[0]=download
            typ = value
            type_by_ref[ref] = typ
            target = sections[typ] if typ in ("download", "upload") else sections["other"]
            target.setdefault(ref, {})
        else:
            typ = type_by_ref.get(ref)
            if typ in ("download", "upload"):
                sections[typ].setdefault(ref, {})[option] = value
            else:
                sections["other"].setdefault(ref, {})[option] = value

    return sections


def delete_sections(section_refs: List[str]) -> Dict:
    if not section_refs:
        return {"success": True, "deleted": 0}
    # Delete indexed refs in descending order to avoid shifting indices, but preserve named refs as-is
    indexed: List[str] = []
    named: List[str] = []
    for ref in set(section_refs):
        m = re.match(r"^@(download|upload)\[(\d+)\]$", ref)
        if m:
            indexed.append(ref)
        else:
            named.append(ref)
    # Sort indexed like @type[3], @type[2], ...
    def idx_key(r: str) -> int:
        mm = re.match(r"^@(?:download|upload)\[(\d+)\]$", r)
        return int(mm.group(1)) if mm else -1
    indexed_sorted_desc = sorted(indexed, key=idx_key, reverse=True)
    commands = [f"uci delete nft-qos.{ref}" for ref in indexed_sorted_desc] + [f"uci delete nft-qos.{ref}" for ref in named]
    failures = [res for res in _run_commands(commands) if res[1]]
    return {"success": len(failures) == 0, "deleted": len(commands), "failures": failures}


def _is_valid_ipv4(ip: str) -> bool:
    try:
        ipaddress.IPv4Address(ip)
        return True
    except Exception:
        return False


def _build_add_device_commands(ip: str, dl_kbytes: int, ul_kbytes: int, scope: str) -> List[str]:
    commands: List[str] = []
    # download
    commands.append("uci add nft-qos download")
    commands.append(f"uci set nft-qos.@download[-1].ipaddr='{ip}'")
    commands.append(f"uci set nft-qos.@download[-1].rate='{int(dl_kbytes)}'")
    commands.append("uci set nft-qos.@download[-1].unit='kbytes'")
    commands.append("uci set nft-qos.@download[-1].netpilot='1'")
    commands.append(f"uci set nft-qos.@download[-1].netpilot_scope='{scope}'")
    # upload
    commands.append("uci add nft-qos upload")
    commands.append(f"uci set nft-qos.@upload[-1].ipaddr='{ip}'")
    commands.append(f"uci set nft-qos.@upload[-1].rate='{int(ul_kbytes)}'")
    commands.append("uci set nft-qos.@upload[-1].unit='kbytes'")
    commands.append("uci set nft-qos.@upload[-1].netpilot='1'")
    commands.append(f"uci set nft-qos.@upload[-1].netpilot_scope='{scope}'")
    return commands


def _collect_netpilot_refs_for_ip(sections: Dict[str, Dict[str, Dict[str, str]]], ip: str,
                                   scope: Optional[str] = None) -> List[str]:
    refs: List[str] = []
    for typ in ("download", "upload"):
        for ref, opts in sections.get(typ, {}).items():
            if opts.get("ipaddr") == ip and opts.get("netpilot") == '1':
                if scope is None or opts.get("netpilot_scope") == scope:
                    refs.append(ref)
    return refs


def set_device_limit(ip: str, dl_kbytes: int, ul_kbytes: int):
    if not _is_valid_ipv4(ip):
        return None, f"Invalid IPv4: {ip}"
    ensure_nft_qos_installed()
    sections = list_existing_sections()
    to_delete = _collect_netpilot_refs_for_ip(sections, ip)
    commands: List[str] = []
    if to_delete:
        commands.extend([f"uci delete nft-qos.{ref}" for ref in to_delete])
    commands.extend(_build_add_device_commands(ip, dl_kbytes, ul_kbytes, scope="device"))
    failures = [res for res in _run_commands(commands) if res[1]]
    commit_res = commit_and_restart()
    success = len(failures) == 0 and commit_res.get("success", False)
    if not success:
        err_msg = failures[0][1] if failures else "Commit/restart failed"
        return None, err_msg
    return {"deleted": len(to_delete), "ip": ip, "dl_kbytes": dl_kbytes, "ul_kbytes": ul_kbytes}, None


def remove_device_limit(ip: str):
    if not _is_valid_ipv4(ip):
        return None, f"Invalid IPv4: {ip}"
    sections = list_existing_sections()
    to_delete = _collect_netpilot_refs_for_ip(sections, ip)
    if not to_delete:
        return {"deleted": 0, "ip": ip}, None
    del_res = delete_sections(to_delete)
    commit_res = commit_and_restart()
    success = del_res.get("success", False) and commit_res.get("success", False)
    if not success:
        return None, "Delete or commit failed"
    return {"deleted": len(to_delete), "ip": ip}, None


def set_group_limits(ips: List[str], dl_kbytes: int, ul_kbytes: int):
    ensure_nft_qos_installed()
    cleaned_ips = sorted({ip for ip in ips if _is_valid_ipv4(ip)})
    sections = list_existing_sections()
    commands: List[str] = []
    total_deleted = 0
    for ip in cleaned_ips:
        to_delete = _collect_netpilot_refs_for_ip(sections, ip)
        total_deleted += len(to_delete)
        commands.extend([f"uci delete nft-qos.{ref}" for ref in to_delete])
        commands.extend(_build_add_device_commands(ip, dl_kbytes, ul_kbytes, scope="group"))
    failures = [res for res in _run_commands(commands) if res[1]]
    commit_res = commit_and_restart()
    success = len(failures) == 0 and commit_res.get("success", False)
    if not success:
        err_msg = failures[0][1] if failures else "Commit/restart failed"
        return None, err_msg
    return {"applied": len(cleaned_ips), "deleted": total_deleted}, None


def remove_group_limits(ips: List[str]):
    cleaned_ips = sorted({ip for ip in ips if _is_valid_ipv4(ip)})
    sections = list_existing_sections()
    to_delete: List[str] = []
    for ip in cleaned_ips:
        to_delete.extend(_collect_netpilot_refs_for_ip(sections, ip))
    del_res = delete_sections(to_delete)
    commit_res = commit_and_restart()
    success = del_res.get("success", False) and commit_res.get("success", False)
    if not success:
        return None, "Delete or commit failed"
    return {"deleted": len(to_delete)}, None


def get_lan_cidr() -> str:
    """Best-effort detection of LAN CIDR. Defaults to 192.168.1.0/24 if unknown."""
    ip_out, ip_err = _execute("uci -q get network.lan.ipaddr | cat")
    mask_out, mask_err = _execute("uci -q get network.lan.netmask | cat")
    if not ip_err and ip_out and not mask_err and mask_out:
        try:
            net = ipaddress.IPv4Network((ip_out.strip(), mask_out.strip()), strict=False)
            return str(net)
        except Exception:
            pass
    alt_out, alt_err = _execute("ip -4 addr show br-lan | awk '/inet / {print $2}' | head -n1 | cat")
    if not alt_err and alt_out:
        try:
            net = ipaddress.IPv4Network(alt_out.strip(), strict=False)
            return str(net)
        except Exception:
            pass
    return "192.168.1.0/24"


def _enumerate_hosts(cidr: str) -> List[str]:
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
        return [str(h) for h in network.hosts()]
    except Exception:
        return []


def _get_protected_ips(cidr: str) -> Set[str]:
    protected: Set[str] = set()
    try:
        network = ipaddress.IPv4Network(cidr, strict=False)
        protected.add(str(network.network_address))
        protected.add(str(network.broadcast_address))
    except Exception:
        pass

    ip_out, ip_err = _execute("uci -q get network.lan.ipaddr | cat")
    if not ip_err and ip_out:
        for token in ip_out.split():
            if _is_valid_ipv4(token):
                protected.add(token.strip())

    addr_out, addr_err = _execute("ip -4 addr show br-lan | awk '/inet / {print $2}' | cut -d/ -f1 | cat")
    if not addr_err and addr_out:
        for token in addr_out.split():
            if _is_valid_ipv4(token):
                protected.add(token.strip())

    sections = list_existing_sections()
    for typ in ("download", "upload"):
        for _, opts in sections.get(typ, {}).items():
            ip = opts.get("ipaddr")
            if ip and opts.get("netpilot") != '1':
                protected.add(ip)

    return protected


def activate_global_limits(dl_kbytes: int, ul_kbytes: int, lan_cidr: Optional[str] = None):
    ensure_nft_qos_installed()
    cidr = lan_cidr or get_lan_cidr()
    protected = _get_protected_ips(cidr)
    hosts = [ip for ip in _enumerate_hosts(cidr) if ip not in protected]

    commands: List[str] = []
    commands.append("uci set nft-qos.netpilot_global=netpilot")
    commands.append("uci set nft-qos.netpilot_global.scope='global'")
    commands.append(f"uci set nft-qos.netpilot_global.dl_kbytes='{int(dl_kbytes)}'")
    commands.append(f"uci set nft-qos.netpilot_global.ul_kbytes='{int(ul_kbytes)}'")

    sections = list_existing_sections()
    total_deleted = 0
    for ip in hosts:
        to_delete = _collect_netpilot_refs_for_ip(sections, ip, scope="global")
        total_deleted += len(to_delete)
        commands.extend([f"uci delete nft-qos.{ref}" for ref in to_delete])
        commands.extend(_build_add_device_commands(ip, dl_kbytes, ul_kbytes, scope="global"))

    failures = [res for res in _run_commands(commands) if res[1]]
    commit_res = commit_and_restart()
    success = len(failures) == 0 and commit_res.get("success", False)
    if not success:
        err_msg = failures[0][1] if failures else "Commit/restart failed"
        return None, err_msg
    return {"cidr": cidr, "applied": len(hosts), "deleted": total_deleted}, None


def deactivate_global_limits():
    sections = list_existing_sections()
    to_delete: List[str] = []
    for typ in ("download", "upload"):
        for ref, opts in sections.get(typ, {}).items():
            if opts.get("netpilot") == '1' and opts.get("netpilot_scope") == 'global':
                to_delete.append(ref)
    # Delete indexed sections safely (descending order)
    del_res = delete_sections(to_delete)
    failures: List[Tuple[str, Optional[str]]] = []
    # Remove global marker section
    failures.extend([res for res in _run_commands(["uci -q delete nft-qos.netpilot_global || true"]) if res[1]])
    commit_res = commit_and_restart()
    success = del_res.get("success", False) and len(failures) == 0 and commit_res.get("success", False)
    if not success:
        err_msg = failures[0][1] if failures else "Commit/restart failed"
        return None, err_msg
    return {"deleted": len(to_delete)}, None


def add_whitelist(ips: List[str]):
    cleaned_ips = sorted({ip for ip in ips if _is_valid_ipv4(ip)})
    sections = list_existing_sections()
    to_delete: List[str] = []
    for ip in cleaned_ips:
        to_delete.extend(_collect_netpilot_refs_for_ip(sections, ip, scope="global"))
    del_res = delete_sections(to_delete)
    commit_res = commit_and_restart()
    success = del_res.get("success", False) and commit_res.get("success", False)
    if not success:
        return None, "Delete or commit failed"
    return {"whitelisted": len(cleaned_ips), "deleted": len(to_delete)}, None


def remove_whitelist(ips: List[str]):
    cleaned_ips = sorted({ip for ip in ips if _is_valid_ipv4(ip)})
    # Read saved global rates
    dl_out, dl_err = _execute("uci -q get nft-qos.netpilot_global.dl_kbytes | cat")
    ul_out, ul_err = _execute("uci -q get nft-qos.netpilot_global.ul_kbytes | cat")
    if dl_err or ul_err or not dl_out or not ul_out:
        return None, "Global limits not active or missing saved rates"

    try:
        dl_kbytes = int(dl_out.strip())
        ul_kbytes = int(ul_out.strip())
    except Exception:
        return None, "Invalid saved global rates"

    sections = list_existing_sections()
    # Delete existing sections for these IPs using safe deletion
    to_delete_all: List[str] = []
    for ip in cleaned_ips:
        to_delete_all.extend(_collect_netpilot_refs_for_ip(sections, ip, scope="global"))
    del_res = delete_sections(to_delete_all)

    # Now add new per-IP limits
    add_cmds: List[str] = []
    for ip in cleaned_ips:
        add_cmds.extend(_build_add_device_commands(ip, dl_kbytes, ul_kbytes, scope="global"))
    failures = [res for res in _run_commands(add_cmds) if res[1]]
    commit_res = commit_and_restart()
    success = del_res.get("success", False) and len(failures) == 0 and commit_res.get("success", False)
    if not success:
        err_msg = failures[0][1] if failures else "Commit/restart failed"
        return None, err_msg
    return {"reapplied": len(cleaned_ips)}, None


