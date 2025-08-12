### AdGuard Home: Per‑Device Rules (Working Approach)

This document shows a simple, working flow to apply domain blocking rules to a single device in AdGuard Home using client tags and a plain text list of domains.

### 1) Identify and configure the client

- Configure the client in AdGuard Home with all identifiers:
  - **IPv4 address**
  - **IPv6 address**
  - **MAC address**
  - (Optional but recommended) **Tag** to target this client with rules (e.g., `family1`)

- In the UI: `Settings → Clients → Known clients → Add client` and fill the fields above.

- The identifier that usually shows up on DNS requests is the **IPv6** address. To find the client’s IPv6, run on the router and match with the MAC:

```bash
ip -6 neigh
```

Match the entry by `lladdr <MAC>` to get the correct IPv6 address for the client record.

### 2) Create or update the client via REST API

Use the control API to create a client with IPv4, IPv6, MAC, and the tag you plan to target with rules.

Example payload:

```json
{
  "name": "MyDevice",
  "ids": [
    "192.168.1.170",
    "fd1f:c83e:bacb:0:498c:72d1:865:fcc",
    "06:f6:bc:dd:ef:a2"
  ],
  "filtering_enabled": true,
  "use_global_settings": false,
  "tags": ["<tag>"]
}
```

Add the client:

```bash
curl -sS -X POST "http://127.0.0.1:3000/control/clients/add" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyDevice",
    "ids": [
      "192.168.1.170",
      "fd1f:c83e:bacb:0:498c:72d1:865:fcc",
      "06:f6:bc:dd:ef:a2"
    ],
    "filtering_enabled": true,
    "use_global_settings": false,
    "tags": ["<tag>"]
  }'
```

Update an existing client (if needed) by posting the full, updated object to the update endpoint:

```bash
curl -sS -X POST "http://127.0.0.1:3000/control/clients/update" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MyDevice",
    "ids": [
      "192.168.1.170",
      "fd1f:c83e:bacb:0:498c:72d1:865:fcc",
      "06:f6:bc:dd:ef:a2"
    ],
    "filtering_enabled": true,
    "use_global_settings": false,
    "tags": ["<tag>"]
  }'
```

If authentication is enabled, include credentials (e.g., `-u admin:password`).

### 3) Apply rules to that client from a domain list

Prepare a text file with one domain per line. Lines starting with `#` are treated as comments and ignored by the command below.

Use a client tag you’ve assigned in the client’s configuration, then transform the file into AdGuard Home rules and set them via the control API:

```bash
TAG=<tag>
FILE=/opt/AdGuardHome/categories/social-media.txt

RULES_JSON=$(jq -R --slurp --arg tag "$TAG" \
    'split("\n") | map(select(length > 0 and startswith("#") | not)) | map("||" + . + "^$client=" + $tag)' $FILE)

curl -X POST -H "Content-Type: application/json" \
    -d "{\"rules\": $RULES_JSON}" \
    "http://127.0.0.1:3000/control/filtering/set_rules"
```

Notes:
- **TAG** must match a tag set on the client in AdGuard Home.
- **FILE** points to your domain list. Adjust the path/name as needed.
- This uses `set_rules`, which replaces the current custom filtering rules with the generated ones.

### 4) Preset and custom lists

- You can keep preset lists (e.g., social media, gaming) as plain `.txt` files and point `FILE` at the one you need.
- You can also create your own custom `.txt` files with one domain per line (comments allowed with `#`).

Example preset locations you might use: `/opt/AdGuardHome/categories/*.txt`.

### 5) Verify

- UI: `Filters → Custom filtering rules` should show rules like `||example.com^$client=<tag>`.
- API: `GET http://127.0.0.1:3000/control/filtering/rules` to view the current rules.
- Test from the client by resolving a blocked domain to confirm it’s filtered for that device.

### 6) Caveats

- This is not the “smartest” approach, but it works reliably with client tagging.
- Because DNS queries often identify clients by IPv6, ensuring the client has the correct IPv6 in its AdGuard record is critical.
- Since `set_rules` replaces the whole custom ruleset, re-run the command any time you want to switch lists or update the rules for a given tag.


