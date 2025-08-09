## AdGuard Home Categorized Filtering (Per‑Client Categories via Tags)

This guide explains how to implement per‑client category blocking in AdGuard Home (AGH) by:
- Keeping domain‑only raw lists per category
- Auto‑generating derived lists that add a category tag ($ctag=<category>)
- Subscribing those derived lists in AGH
- Assigning category tags to clients so only tagged clients match those lists

Result: Each client can be assigned to any combination of categories; only those clients are blocked for the category’s domains. Others remain unaffected.

### Requirements (one‑time)
- AGH installed and running with API on `127.0.0.1:3000`, DNS on `:53`.
- HTTP server serving local files (OpenWrt `uhttpd`): `/www` must be accessible on `http://127.0.0.1/`.
- SSH access to run local curl calls (or tunnel if remote). All API paths below use `/control/...`.

Verify:
```sh
curl -s http://127.0.0.1:3000/control/status
```

### Directory layout (categories storage)
```sh
mkdir -p /www/agh-cats/raw /www/agh-cats/derived
/etc/init.d/uhttpd start 2>/dev/null || true
```

### Concept
- Raw lists: simple domain‑only lines (e.g., `netflix.com`).
- Derived lists: convert each domain to ABP host rule (`||domain^`) and append `$ctag=<category>` so only clients with that tag match.
- Client assignment: tag clients with category names; a client with tag `streaming` will match all rules ending `$ctag=streaming`.

---

## Setup Steps

### 1) Create raw lists (one file per category)
```sh
printf '%s\n' netflix.com hulu.com > /www/agh-cats/raw/streaming.txt
printf '%s\n' adult-example.com > /www/agh-cats/raw/adult.txt
```

### 2) Build derived lists (adds $ctag=<category>)
BusyBox‑compatible builder function:
```sh
build_cat() {
  cat_name="$1"
  src="/www/agh-cats/raw/${cat_name}.txt"
  dst="/www/agh-cats/derived/${cat_name}.txt"
  awk -v C="$cat_name" '
    /^[[:space:]]*#/ {next}
    /^[[:space:]]*$/ {next}
    {
      g=$0; sub(/^[[:space:]]+/,"",g); sub(/[[:space:]]+$/,"",g);
      if (g ~ /^\|\|/)      print g "$ctag=" C;    # already ABP host rule
      else                    print "||" g "^$ctag=" C;
    }
  ' "$src" > "$dst"
}

build_cat streaming
build_cat adult

# Sanity check
curl -sSf http://127.0.0.1/agh-cats/derived/streaming.txt >/dev/null
curl -sSf http://127.0.0.1/agh-cats/derived/adult.txt >/dev/null
```

### 3) Subscribe categories in AGH and refresh
```sh
curl -s -X POST http://127.0.0.1:3000/control/filtering/add_url \
  -H 'Content-Type: application/json' \
  -d '{"name":"cat_streaming","url":"http://127.0.0.1/agh-cats/derived/streaming.txt"}'

curl -s -X POST http://127.0.0.1:3000/control/filtering/add_url \
  -H 'Content-Type: application/json' \
  -d '{"name":"cat_adult","url":"http://127.0.0.1/agh-cats/derived/adult.txt"}'

# Refresh is POST; some versions require an empty JSON body
curl -s -X POST http://127.0.0.1:3000/control/filtering/refresh -H 'Content-Type: application/json' -d '{}'

# Inspect status
curl -s http://127.0.0.1:3000/control/filtering/status | sed -n '1,200p'
```

### 4) Tag clients to apply categories
Identify your client(s) (IPv4/IPv6) from recent queries:
```sh
curl -s 'http://127.0.0.1:3000/control/querylog?offset=0&limit=100' \
 | grep -o '"client":"[^"]*"' | cut -d'"' -f4 | sort -u
```

Optionally add a configured client combining IPv4/IPv6 IDs:
```sh
PC_V4="192.168.1.122"; PC_V6="fdxx::your:pc:v6"  # set your values
curl -s -X POST http://127.0.0.1:3000/control/clients/add \
  -H 'Content-Type: application/json' \
  -d '{"ids":["'"$PC_V4"'","'"$PC_V6"'"],"name":"PC"}'
``;

Assign categories (tags) to the client (one call can set many):
```sh
curl -s -X PATCH http://127.0.0.1:3000/control/clients/'$PC_V4' \
  -H 'Content-Type: application/json' \
  -d '{"tags":["streaming"]}'

curl -s -X POST http://127.0.0.1:3000/control/filtering/refresh -H 'Content-Type: application/json' -d '{}'
```

Verification:
```sh
# From the tagged device: should be blocked
nslookup netflix.com 127.0.0.1 || true

# From an untagged device: should resolve normally
```

---

## Daily Operations (repeatable)

### Add/remove domains in a category
```sh
echo 'disneyplus.com' >> /www/agh-cats/raw/streaming.txt
build_cat streaming
curl -s -X POST http://127.0.0.1:3000/control/filtering/refresh -H 'Content-Type: application/json' -d '{}'
```

### Assign/remove categories for a client
```sh
# Add adult category too
curl -s -X PATCH http://127.0.0.1:3000/control/clients/'$PC_V4' \
  -H 'Content-Type: application/json' \
  -d '{"tags":["streaming","adult"]}'

# Clear all categories
curl -s -X PATCH http://127.0.0.1:3000/control/clients/'$PC_V4' \
  -H 'Content-Type: application/json' \
  -d '{"tags":[]}'
```

### Disable or remove a category
```sh
# Remove a subscribed category list
curl -s -X POST http://127.0.0.1:3000/control/filtering/remove_url \
  -H 'Content-Type: application/json' \
  -d '{"url":"http://127.0.0.1/agh-cats/derived/streaming.txt"}'
curl -s http://127.0.0.1:3000/control/filtering/refresh
```

---

## Creating a New Category
1) Add a raw file:
```sh
echo 'tiktok.com' > /www/agh-cats/raw/social.txt
```
2) Build derived and verify fetch:
```sh
build_cat social
curl -sSf http://127.0.0.1/agh-cats/derived/social.txt >/dev/null
```
3) Subscribe and refresh:
```sh
curl -s -X POST http://127.0.0.1:3000/control/filtering/add_url \
  -H 'Content-Type: application/json' \
  -d '{"name":"cat_social","url":"http://127.0.0.1/agh-cats/derived/social.txt"}'
curl -s http://127.0.0.1:3000/control/filtering/refresh
```
4) Tag clients that should be affected:
```sh
curl -s -X PATCH http://127.0.0.1:3000/control/clients/'$PC_V4' \
  -H 'Content-Type: application/json' \
  -d '{"tags":["social"]}'
```

---

## Notes & Troubleshooting
- Refresh is POST: `/control/filtering/refresh`. On some builds, an empty body is required: `-H 'Content-Type: application/json' -d '{}'`.
- If API returns 404, ensure you use `/control/...` endpoints, not `/api/v1/...`.
- If clients don’t appear, use query log to discover runtime clients, or add configured clients via `/control/clients/add`.
- If AGH can’t bind :53, ensure `dnsmasq` DNS is disabled (`uci set dhcp.@dnsmasq[0].port='0'`).
- For devices with both IPv4/IPv6, include both in client `ids` so tags apply consistently.
- Security: keep AGH HTTP on loopback and use SSH tunnels when needed.


