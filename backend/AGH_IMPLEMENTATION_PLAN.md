### AdGuard Home Domain Blocking – Implementation Plan (Per‑Device via Tags)

Assumes AdGuard Home (AGH) is installed and running on the router with its control API at `http://127.0.0.1:3000`. We will only use it, not install it. Rules are generated from plain `.txt` files and applied as Custom filtering rules using `$client=<tag>` as in the working guide.

Key idea: Maintain domain lists per category, generate ABP host rules with client‑tag constraints (`||domain^$client=<categoryTag>`), and apply them with a single `set_rules` call that replaces the current custom rules. Devices are “marked” by ensuring AGH clients exist with identifiers (IPv4, IPv6, MAC) and that their `tags` include the category names to enforce.

---

### Architecture alignment with backend server
- Services are implemented first; endpoints call services.
- Services return `(result, error)` tuples and execute router‑side commands via `RouterConnectionManager.execute(...)` or `copy_file(...)`.
- Router executes `curl` against AGH on loopback and reads/writes domain lists.

---

### Phase 1 — Service layer (build first)
Create `backend/services/agh_service/` package and implement these units first.

- [x] Category file operations
  - [x] `get_category_domains(category) -> (List[str], error)`
  - [x] `set_category_domains(category, domains_or_text, mode="replace") -> (ok, error)`
  - [x] `list_categories() -> (List[str], error)`

- [x] Rules build/apply
  - [x] `build_rules_union() -> List[str]` emits `||domain^$client=<category>` for all categories
  - [x] `apply_rules(rules) -> (ok, error)` posts once to `/control/filtering/set_rules`
  - [x] `get_current_rules() -> (List[str], error)` reads `/control/filtering/rules` for diagnostics

- [x] IPv6 resolution (input does NOT include IPv6)
  - [x] `resolve_ipv6_for_mac(mac) -> (ipv6_or_none, error)` using `ip -6 neigh` and matching `lladdr <MAC>`
    - Minimal reference: `ip -6 neigh | awk -v M="aa:bb:cc:dd:ee:ff" '$0 ~ ("lladdr " tolower(M)) {print $1; exit}'`

- [x] Client management
  - [x] `ensure_client_with_ids(name, mac, ipv4_optional) -> (client, error)`
    - Build `ids`: `[ipv4_optional_if_any, resolved_ipv6_if_any, mac]`
    - Upsert via `/control/clients/add` or `/control/clients/update` (post full object, including current tags)
  - [x] `find_client_by_any_id({mac, ipv4}) -> (client, error)`
  - [x] `set_client_tags(client, tags) -> (ok, error)` (send full updated object)

- [x] Device/category operations
  - [x] `mark_devices_for_categories(devices, categories) -> (summary, error)`
  - [x] `unmark_devices_for_categories(devices, categories) -> (summary, error)`
  - [x] `mark_device(device, categories) -> (summary, error)`
  - [x] `unmark_device(device, categories) -> (summary, error)`

- [x] Effective rules per client
  - [x] `get_client_effective_rules({mac, ipv4}) -> (summary, error)` combining client tags + category files; include sample rules

Notes
- Always rebuild and apply the full union of custom rules when category files change (see Set-Rules semantics below).

---

### Phase 2 — Backend API (endpoints) — after services
All routes require active `sessionId`/`routerId` context, except as noted by server middleware.

- [ ] GET `/api/agh/categories/<category>/domains`
  - Response: `{ category, domains: ["example.com", ...], count }`

- [ ] POST `/api/agh/categories/<category>/domains` (replace)
  - Body: `{ "domains": ["example.com", ...] }` or text/plain list
  - Behavior: write raw file, rebuild union across all categories, apply via `set_rules`.

- [ ] POST `/api/agh/groups/mark`
  - Body: `{ "devices": [{"name":"KidPhone","mac":"...","ipv4":"..."?}, ...], "categories": ["social","gaming"] }`
  - Behavior: ensure client per device (`ids=[ipv4_if_given, resolved_ipv6_from_mac, mac]`), merge categories into tags.

- [ ] POST `/api/agh/groups/unmark`
  - Body: `{ "devices": [...], "categories": ["social","gaming"] }`
  - Behavior: remove only specified categories from tags; keep others.

- [ ] POST `/api/agh/devices/mark`
  - Body: `{ "device": {"name":"Laptop","mac":"...","ipv4":"..."?}, "categories": ["social"] }`

- [ ] POST `/api/agh/devices/unmark`
  - Body: `{ "device": {"name":"Laptop","mac":"...","ipv4":"..."?}, "categories": ["social"] }`

- [ ] GET `/api/agh/clients/effective-rules`
  - Query: `?mac=...` (preferred) or `?ipv4=...`
  - Response: `{ client, tags, categories: [{ name, domainCount }], sampleRules: [...] }`

---

### Phase 3 — Router storage and rule generation details
- [ ] Ensure directory exists on router (adjustable): `/opt/AdGuardHome/categories`
- [ ] File format: one domain per line; `#` for comments; trim and lowercase
- [ ] Rule format: `||domain^$client=<category>`
- [ ] Union/replace model: always rebuild union for all categories, then apply once via `set_rules`
- Minimal shell reference (for understanding only):
  ```sh
  TAG=social; FILE=/opt/AdGuardHome/categories/social.txt
  RULES_JSON=$(jq -R --slurp --arg tag "$TAG" 'split("\n") | map(select(length > 0 and startswith("#") | not)) | map("||" + . + "^$client=" + $tag)' $FILE)
  curl -s -X POST -H 'Content-Type: application/json' -d "{\"rules\": $RULES_JSON}" http://127.0.0.1:3000/control/filtering/set_rules
  ```

---

### Phase 4 — Behavior details and safeguards
- **IPv6 matters**: DNS requests often identify the client by IPv6. Always include IPv4, IPv6, and MAC in `ids` when creating/updating clients.
- **Single source of truth**: Treat router category files as canonical. UI edits should go through our API to avoid desync.
- **`set_rules` is global**: Any manual custom rule in AGH UI will be overwritten. Document this in UI and logs.
- **Validation**: normalize domains, drop comments/blank lines, enforce lowercase, and optionally deduplicate.
- **Performance**: If rule counts grow large, batch `set_rules` updates sensibly; ABP rules scale well, but test with your category sizes.

---

### Phase 5 — Minimal flows per requirement (trackable)
- [ ] 1) Get domains from category: read `/opt/AdGuardHome/categories/<category>.txt` and return cleaned list
- [ ] 2) Post a new domain list: replace file contents; rebuild union; call `set_rules`
- [ ] 3) Mark a group of devices: ensure client (ids via MAC→IPv6), merge categories into tags
- [ ] 4) Unblock a group from categories: remove only specified tags; keep others
- [ ] 5) Mark a single device: ensure client, add tags
- [ ] 6) Unmark a single device: ensure client, remove tags
- [ ] 7) Get rules per client: return tags, categories, counts, sample `||domain^$client=<tag>`

---

### Phase 6 — Verification steps
- After changing domains: `GET /control/filtering/rules` should include `||domain^$client=<category>` lines for all categories.
- After marking devices: `GET /control/clients` (or UI: Settings → Clients) shows each client with tags matching selected categories.
- End‑to‑end test from the device: the domain resolves as blocked; from an untagged device, it resolves normally.

---

### Phase 6 — Notes and future enhancements
- If desired later, you can migrate to subscribed per‑category lists (`add_url`) with `$ctag=<category>` as in `AGH_CATEGORIZED_FILTERING.md`. The marking/unmarking logic remains identical (operate on client `tags`), but rules will live in subscribed lists instead of AGH custom rules.
- Add optional audit endpoints: list all categories, preview resulting custom rules without applying, and diff pending vs applied.

---

### Minimal request/response examples
- Apply combined rules (service will build one JSON array):
  ```sh
  curl -s -X POST http://127.0.0.1:3000/control/filtering/set_rules \
    -H 'Content-Type: application/json' \
    -d '{"rules":["||tiktok.com^$client=social","||netflix.com^$client=streaming"]}'
  ```

- Create/update client with identifiers and tags:
  ```sh
  curl -s -X POST http://127.0.0.1:3000/control/clients/update \
    -H 'Content-Type: application/json' \
    -d '{"name":"KidPhone","ids":["192.168.1.170","fd1f::865:fcc","06:f6:bc:dd:ef:a2"],"filtering_enabled":true,"use_global_settings":false,"tags":["social","gaming"]}'
  ```

---

### Set-Rules semantics (AGH)
- `POST /control/filtering/set_rules` REPLACES the entire Custom filtering rules list with the provided `rules` array.
- It does not append. To preserve previous custom rules, always send the full desired set.
- Subscribed filter lists added via `add_url` are separate and unaffected by `set_rules`.


