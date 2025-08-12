### NetPilot nft-qos Bandwidth Control Plan (backend only)

This document specifies the new bandwidth-control features using nft-qos and the migration plan to replace the current whitelist/blacklist + tc/iptables flow in `backend/` only. The upper layers (DB/UI) will own device selection and state; the backend will safely execute idempotent commands on the router.

### Design goals
- **Use nft-qos only**: stop using manual tc + iptables marking.
- **Naive per-device control**: backend receives IP lists and limits; no group persistence in backend.
- **Safe/idempotent**: replacing or removing rules must not break traffic.
- **Units**: inputs for global mode are always kbytes. For per-device/group operations, inputs may be Mbps but are applied as kbytes (1 Mbps → 125 kbytes/s).

### New endpoints (backend/ only)

- Group/device rate limits (naive per-device rules)
  - `POST /api/bandwidth/limits/group`
    - Body: `{ "ips": ["192.168.1.10", ...], "download_mbps": 12, "upload_mbps": 3 }`
    - Behavior: For each IP, set static per-IP download/upload rates via nft-qos. If the IP already has a rule, replace it.
  - `DELETE /api/bandwidth/limits/group`
    - Body: `{ "ips": ["192.168.1.10", ...] }`
    - Behavior: Remove per-IP limits for all given IPs. If a device has no rule, do nothing.
  - `POST /api/bandwidth/limits/device`
    - Body: `{ "ip": "192.168.1.10", "download_mbps": 12, "upload_mbps": 3 }`
  - `DELETE /api/bandwidth/limits/device`
    - Body: `{ "ip": "192.168.1.10" }`

 - Global limiting with exceptions ("whitelist-like" mode via nft-qos per-host entries)
  - `POST /api/bandwidth/global/activate`
    - Body: `{ "download_kbytes": 4000, "upload_kbytes": 1000, "lan_cidr": "192.168.1.0/24" }` (CIDR optional; defaults to 192.168.1.0/24)
    - Behavior: Activate global limiting by creating nft-qos per-IP download/upload entries for every host in the LAN CIDR except protected/whitelisted IPs. No nftables manual chains are used.
  - `DELETE /api/bandwidth/global/deactivate`
    - Behavior: Remove all NetPilot-managed nft-qos entries that belong to the global mode scope only.
  - `POST /api/bandwidth/global/whitelist/devices`
    - Body: `{ "ips": ["192.168.1.10", ...] }`
    - Behavior: Exempt these devices from global limits by deleting their NetPilot-global nft-qos entries (they become unlimited). If different limits are desired, use the per-device endpoints to add specific limits.
  - `DELETE /api/bandwidth/global/whitelist/devices`
    - Body: `{ "ips": ["192.168.1.10", ...] }`
    - Behavior: Re-apply the global limits to these devices by (re)creating the per-IP nft-qos entries at the stored global rates.
  - `POST /api/bandwidth/global/whitelist/device`
    - Body: `{ "ip": "192.168.1.10" }`
  - `DELETE /api/bandwidth/global/whitelist/device`
    - Body: `{ "ip": "192.168.1.10" }`

Notes
- For per-device endpoints, if the UI prefers kbytes everywhere, accept `download_kbytes`/`upload_kbytes` instead of Mbps. If `download_mbps`/`upload_mbps` are supplied, convert with: `kbytes = floor(mbps * 125)`.
- Unlimited override is represented by very high per-device rates (e.g., 999999 kbytes) if nft-qos lacks a dedicated "unlimited" flag.

### Backend module changes

- Add `backend/services/nft_qos_service.py` to encapsulate router actions.
- Add `backend/endpoints/bandwidth.py` blueprint to expose the endpoints.
- Register blueprint in `backend/server.py` under `/api/bandwidth`.
- Deprecate and remove use of:
  - `backend/utils/traffic_control_helpers.py` (tc + iptables)
  - `backend/services/mode_activation_service.py` whitelist/blacklist flows
  - `backend/services/device_rule_service.py` iptables marking helpers
  - `backend/endpoints/whitelist.py` and `backend/endpoints/blacklist.py` (replace with 410 Gone or remove once UI migrates)

### Router operations using nft-qos

Primary approach uses UCI + init script so changes are persistent and survivable across reboots.

- Ensure package and service are present
  - `opkg update && opkg install -y nft-qos` (only if missing; log and continue if already installed)
  - Service: `/etc/init.d/nft-qos restart` after any config change

- UCI model (representative; adjust to the router's schema if it differs)
  - Per-device limits (two sections, one for download and one for upload)
    - `uci add nft-qos download; uci set nft-qos.@download[-1].ipaddr='<IP>'; uci set nft-qos.@download[-1].rate='<KBYTES>'; uci set nft-qos.@download[-1].unit='kbytes'`
    - `uci add nft-qos upload;   uci set nft-qos.@upload[-1].ipaddr='<IP>';   uci set nft-qos.@upload[-1].rate='<KBYTES>'; uci set nft-qos.@upload[-1].unit='kbytes'`
    - Add `option netpilot '1'` to each created section so we can safely find/update/remove our own entries without touching user-managed ones.
  - Apply
    - `uci commit nft-qos && /etc/init.d/nft-qos restart`

- Finding and deleting existing entries by IP
  - List candidate sections tagged by NetPilot:
    - `uci show nft-qos | grep "netpilot='1'" -n | cat`
  - Find download/upload entries for a specific IP and delete them:
    - `for S in $(uci show nft-qos | grep "@download\[.*\]\.ipaddr='<IP>'" | sed -E "s/^(nft-qos\.)(@download\[[0-9]+\])\.ipaddr=.*/\2/"); do uci delete nft-qos.$S; done`
    - `for S in $(uci show nft-qos | grep "@upload\[.*\]\.ipaddr='<IP>'"   | sed -E "s/^(nft-qos\.)(@upload\[[0-9]+\])\.ipaddr=.*/\2/");   do uci delete nft-qos.$S; done`
  - Prefer deleting only sections that either match `ipaddr=<IP>` and/or include `option netpilot '1'` to avoid removing user-defined rules.

- Batch update pattern (group operations)
  - For all IPs in the request, pre-delete matches (as above) without committing yet.
  - Add new `@download` and `@upload` sections for each IP with computed `rate` and `unit='kbytes'`, plus `option netpilot '1'`.
  - Single `uci commit nft-qos` and a single `/etc/init.d/nft-qos restart` at the end.

Whitelist mode using nft-qos per-host enumeration (no nftables manual rules)
- Approach: enumerate all usable host IPs in the LAN CIDR and create nft-qos `download`/`upload` sections for each, excluding protected IPs and the whitelist. Whitelisted devices simply have no nft-qos entries, hence are unlimited.
- Scope tagging:
  - Every NetPilot-created section has `option netpilot '1'` and `option netpilot_scope 'global'` so we can safely manage/deactivate without touching user rules or device-scoped entries.
- Global rates storage:
  - Store current global rates in a NetPilot-only UCI section:
    - `uci set nft-qos.netpilot_global=netpilot`
    - `uci set nft-qos.netpilot_global.scope='global'`
    - `uci set nft-qos.netpilot_global.dl_kbytes='<KBYTES>'`
    - `uci set nft-qos.netpilot_global.ul_kbytes='<KBYTES>'`
  - Commit once per batch.
- Protected (do-not-touch) IPs detection:
  - Always exclude: network address and broadcast of the CIDR; default `192.168.1.0` and `192.168.1.255` for /24.
  - Exclude router LAN IP(s): `uci get network.lan.ipaddr` (and any additional IPv4s returned by `ip -4 addr show br-lan`). Default excludes `192.168.1.1`.
  - Exclude any existing nft-qos download/upload entries that are NOT tagged with `netpilot='1'` to avoid modifying user-managed rules.
  - Exclude the explicitly provided whitelist IPs.
- Batch creation/removal flow:
  - To activate: pre-delete any NetPilot-global sections for IPs to be (re)applied, then add new `@download` and `@upload` sections for each candidate IP with `rate=<KBYTES>`, `unit='kbytes'`, plus `netpilot` and `netpilot_scope='global'`; commit once and restart once.
  - To add to whitelist: delete the matching NetPilot-global sections for those IPs; commit/restart once.
  - To remove from whitelist: re-add the NetPilot-global sections for those IPs using the stored global rates; commit/restart once.
  - To deactivate: delete all sections with `netpilot='1'` and `netpilot_scope='global'`; delete `nft-qos.netpilot_global`; commit/restart once.

### Service-level implementation details

Add `backend/services/nft_qos_service.py` with functions (pseudocode level):

```python
def mbps_to_kbytes(value_mbps: int) -> int:
    return max(1, int(value_mbps * 125))

def ensure_nft_qos_installed(rcm) -> None: ...

def set_device_limit(ip: str, dl_kbytes: int, ul_kbytes: int) -> bool:
    # Remove any existing NetPilot-managed sections for this IP, then add new upload/download entries with netpilot=1
    # uci commands + commit + service restart (batched at call sites when updating groups)
    ...

def remove_device_limit(ip: str) -> bool:
    # Delete any @download/@upload sections where ipaddr == ip and netpilot == 1
    ...

def set_group_limits(ips: list[str], dl_mbps: int, ul_mbps: int) -> dict:
    # Convert to kbytes, upsert all entries, commit once, restart once
    ...

def remove_group_limits(ips: list[str]) -> dict:
    # Delete matching entries, commit once, restart once
    ...

def _get_protected_ips(lan_cidr: str) -> set[str]:
    # Compute network/broadcast; query router LAN ip(s) and existing non-NetPilot nft-qos entries; return a set of IPs to exclude
    ...

def activate_global_limits(dl_kbytes: int, ul_kbytes: int, lan_cidr: str = "192.168.1.0/24") -> dict:
    # Store global rates in nft-qos.netpilot_global; enumerate host IPs in CIDR; exclude protected IPs; create per-IP entries with scope=global
    # Return counts of applied/skipped
    ...

def deactivate_global_limits() -> bool:
    # Delete all nft-qos sections with netpilot=1 and netpilot_scope=global; delete netpilot_global
    ...

def add_whitelist(ips: list[str]) -> dict:
    # For each IP, delete NetPilot-global @download/@upload entries (ignore missing)
    ...

def remove_whitelist(ips: list[str]) -> dict:
    # For each IP, add NetPilot-global @download/@upload entries using saved global rates
    ...
```

Command execution
- Reuse `RouterConnectionManager` (already exposed on `app.router_connection_manager`) to run SSH commands.
- Batch UCI edits where possible to minimize restarts:
  - Perform multiple `uci add/set` commands, then a single `uci commit nft-qos` and single `/etc/init.d/nft-qos restart`.
- Idempotency:
  - On upsert, first delete any NetPilot-managed entries for the target IP(s) before adding new ones.
  - Deletion should tolerate missing entries.
- Validation:
  - Validate IPv4 format; ignore duplicates; enforce kbytes >= 1.
- Concurrency:
  - Use a simple per-router lock around `uci commit` + restart to avoid interleaving.

### Endpoint-layer mapping (`backend/endpoints/bandwidth.py`)

- Each route parses JSON, validates input, calls the corresponding `nft_qos_service` function, and returns `{ success: true, details: ... }` or `{ success: false, error: ... }`.
- Minimal response schemas to match current style in `backend/endpoints/*`.

### Migration plan (backend only)

1) Introduce new files
   - `services/nft_qos_service.py`
   - `endpoints/bandwidth.py` (Flask blueprint `bandwidth_bp`)
   - Register in `backend/server.py`: `app.register_blueprint(bandwidth_bp, url_prefix='/api/bandwidth')`

2) Wire up router exec
   - Use `RouterConnectionManager` to run the UCI/nft-qos commands over SSH.

3) Deprecate legacy flows
   - Stop calling `utils/traffic_control_helpers.py` and `services/mode_activation_service.py` from any endpoint.
   - Replace `endpoints/whitelist.py` and `endpoints/blacklist.py` with 410 Gone or remove once UI migrates.
   - Remove iptables/tc-specific helpers from `services/device_rule_service.py`.

4) Tests
   - Add integration tests stubbing SSH to assert correct UCI command sequences for:
     - Group set/remove
     - Device set/remove
     - Global activate/deactivate
     - Whitelist add/remove (group and single)

5) Router safety
   - Ensure a best-effort check/install of `nft-qos` (log-only if offline).
   - One restart per batch change. Retry once on failure; on persistent failure, return an error without leaving partial UCI state (delete the partial NetPilot sections created in the batch).

6) Rollout
   - Ship new endpoints behind feature flag; keep legacy endpoints returning 410 with migration hint.
   - When UI uses new endpoints exclusively, delete legacy modules and docs.

### Request/response examples

Set group limits
```http
POST /api/bandwidth/limits/group
{
  "ips": ["192.168.1.10", "192.168.1.11"],
  "download_mbps": 20,
  "upload_mbps": 5
}
```
Response:
```json
{ "success": true, "applied": ["192.168.1.10","192.168.1.11"], "dl_kbytes": 2500, "ul_kbytes": 625 }
```

Activate global and whitelist two devices (unlimited)
```http
POST /api/bandwidth/global/activate
{ "download_kbytes": 4000, "upload_kbytes": 1000, "lan_cidr": "192.168.1.0/24" }

POST /api/bandwidth/global/whitelist/devices
{ "ips": ["192.168.1.50", "192.168.1.60"] }
```

### Operational notes
- Units: use kbytes everywhere at the router; convert Mbps→kbytes only at the boundary.
- Logs: emit the exact UCI commands executed for auditability. Avoid touching non-NetPilot nft-qos entries.
- Cleanup: `DELETE /api/bandwidth/global/deactivate` removes only NetPilot-global nft-qos entries and the `netpilot_global` section.


