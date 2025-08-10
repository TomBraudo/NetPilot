### NFT-QOS Migration Plan (backend only)

This plan replaces legacy tc/iptables bandwidth control with nft-qos using UCI only. No backward compatibility – all bandwidth control must use nft-qos.

Conventions
- Use `RouterConnectionManager.execute()` to run all `uci` and service commands on the router.
- Tag all NetPilot-created nft-qos sections with `option netpilot '1'` and, where applicable, `option netpilot_scope 'global'`.
- Use RESTful routes and HTTP methods.
- Follow existing code patterns for services and endpoints.

### Phase 1 – Service foundation [services/nft_qos_service.py]
- [x] Create file `backend/services/nft_qos_service.py`
- [x] Add `convert_mbps_to_kbytes(value_mbps: int) -> int`
- [x] Add `ensure_nft_qos_installed(rcm) -> None` (best-effort `opkg install nft-qos`)
- [x] Add `list_existing_sections(rcm) -> dict` (parse `uci show nft-qos` to map sections and fields)
- [x] Add `delete_sections(rcm, section_refs: list[str]) -> None` (batch delete)
- [x] Add `commit_and_restart(rcm) -> None` (`uci commit nft-qos && /etc/init.d/nft-qos restart`)

Per-device operations
- [x] `set_device_limit(ip: str, dl_kbytes: int, ul_kbytes: int) -> bool`
  - Delete NetPilot sections for this IP (`@download/@upload` with `netpilot='1'`), then add new ones with `ipaddr`, `rate`, `unit='kbytes'`, `netpilot='1'`.
  - Do not touch non-NetPilot sections.
- [x] `remove_device_limit(ip: str) -> bool`
  - Delete NetPilot sections for this IP (ignore if none).

Group operations
- [x] `set_group_limits(ips: list[str], dl_kbytes: int, ul_kbytes: int) -> dict`
  - Upsert all given IPs; single commit+restart.
- [x] `remove_group_limits(ips: list[str]) -> dict`
  - Delete for all IPs; single commit+restart.

- Global (whitelist-like) mode via per-host entries
- [x] `get_lan_cidr(rcm) -> str` (default `192.168.1.0/24` if unknown)
- [x] `_enumerate_hosts(cidr: str) -> list[str]` (exclude network/broadcast)
- [x] `_get_protected_ips(rcm, cidr: str) -> set[str]` (router LAN IP(s), network/broadcast, any non-NetPilot nft-qos entries)
- [x] `activate_global_limits(dl_kbytes: int, ul_kbytes: int, lan_cidr: str|None) -> dict`
  - Store rates in `nft-qos.netpilot_global` with `scope='global'`.
  - For each usable host IP not in protected set: create NetPilot `@download/@upload` entries with global rates; tag `netpilot_scope='global'`.
  - Commit+restart once. Return counts of applied/skipped.
- [x] `deactivate_global_limits() -> bool`
  - Delete sections with `netpilot='1'` and `netpilot_scope='global'`; delete `nft-qos.netpilot_global`; commit+restart.
- [x] `add_whitelist(ips: list[str]) -> dict`
  - Delete NetPilot-global entries for these IPs; commit+restart.
- [x] `remove_whitelist(ips: list[str]) -> dict`
  - Recreate NetPilot-global entries for these IPs using saved global rates; commit+restart.

Validation and safety
- [ ] Validate IPv4 format; deduplicate inputs; enforce kbytes >= 1.
- [ ] Use a simple per-router lock (threading.Lock) around commit+restart inside service.
- [ ] All functions return structured results `{ success, details }` with logs of commands run.

### Phase 2 – Endpoints [endpoints/bandwidth.py]
- [x] Create file `backend/endpoints/bandwidth.py` with blueprint `bandwidth_bp`.
- [x] Register in `backend/server.py`: `app.register_blueprint(bandwidth_bp, url_prefix='/api/bandwidth')`.

Routes (RESTful)
- [ ] `POST   /api/bandwidth/limits/group`          → set_group_limits
- [ ] `DELETE /api/bandwidth/limits/group`          → remove_group_limits
- [ ] `POST   /api/bandwidth/limits/device`         → set_device_limit
- [ ] `DELETE /api/bandwidth/limits/device`         → remove_device_limit
- [ ] `POST   /api/bandwidth/global/activate`       → activate_global_limits
- [ ] `DELETE /api/bandwidth/global/deactivate`     → deactivate_global_limits
- [ ] `POST   /api/bandwidth/global/whitelist`      → add_whitelist (group)
- [ ] `DELETE /api/bandwidth/global/whitelist`      → remove_whitelist (group)
- [ ] `POST   /api/bandwidth/global/whitelist/device`  → add_whitelist (single)
- [ ] `DELETE /api/bandwidth/global/whitelist/device`  → remove_whitelist (single)

Endpoint behaviors
- [ ] Parse/validate JSON; convert Mbps → kbytes if provided.
- [ ] Call service functions; return `{ success: true, details: {...} }` or `{ success: false, error }`.
- [ ] Use existing middleware (`verify_session_and_router`) to ensure router context.

### Phase 3 – Deprecate legacy code
- [x] Remove `backend/utils/traffic_control_helpers.py` (tc/iptables)
- [x] Remove `backend/services/mode_activation_service.py` whitelist/blacklist flows
- [x] Remove iptables-specific parts of `backend/services/device_rule_service.py`
- [x] Remove `backend/endpoints/whitelist.py` and `backend/endpoints/blacklist.py`
- [x] Purge any references in docs to legacy whitelist/blacklist bandwidth control

State file usage
- [x] Remove request-scoped `StateFileManager` from `backend/server.py`
- [x] Update session start to headless (no infra setup, only reachability)

### Phase 4 – Tests and docs
- [ ] Add integration tests (mock SSH via `RouterConnectionManager`) for all routes
- [ ] Verify idempotency: repeated apply/remove cycles yield consistent UCI state
- [ ] Verify protected IPs are skipped (router IP, network/broadcast, non-NetPilot entries)
- [ ] Update `backend/NFT_QOS_BANDWIDTH_IMPLEMENTATION.md` if adjustments are made
- [ ] Add operator notes for typical LAN /24 and large lists performance (single commit/restart)

### Phase 5 – Cleanup and verification
- [ ] Manual validation on a router with /24 LAN
- [ ] Confirm reboot persistence of UCI rules and service
- [ ] Audit logs contain exact `uci` commands
- [ ] Sign-off: legacy code removed; only nft-qos path remains


