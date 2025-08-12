# Minimal Setup: AdGuard Home VM + OpenWrt Router Integration

This guide explains how to set up a single AdGuard Home instance on a cloud VM and configure any OpenWrt router to forward all DNS requests to it.

---

## 1. Infrastructure Setup on Cloud VM

1. **Install AdGuard Home**
curl -s -S -L https://static.adguard.com/adguardhome/release/AdGuardHome_linux_amd64.tar.gz | tar -xz
cd AdGuardHome
./AdGuardHome -s install


2. **Open Ports**
- Ensure the VM firewall and your cloud provider allow inbound TCP/UDP port **53** (DNS), and **3000** (web UI/API, for management).

3. **Configure AdGuard Home**
- Access the web setup at `http://<VM_PUBLIC_IP>:3000`
- Set the DNS listen address to `0.0.0.0:53` (to accept requests from your routers).
- Complete any required basic configuration.

---

## 2. Router-side Configuration on OpenWrt

1. **Point Router DNS to the AdGuard Home Server**
SSH into the router and run:
uci set dhcp.lan.dhcp_option='6,<VM_PUBLIC_IP>'
uci commit dhcp
/etc/init.d/dnsmasq restart


- Replace `<VM_PUBLIC_IP>` with the AdGuard Home VM's public IP.

2. **(Optional) Block Bypass Attempts**  
To ensure all LAN DNS uses this server, add firewall rules to redirect all DNS to the VM:
iptables -t nat -A PREROUTING -i br-lan -p udp --dport 53 -j DNAT --to-destination <VM_PUBLIC_IP>:53
iptables -t nat -A PREROUTING -i br-lan -p tcp --dport 53 -j DNAT --to-destination <VM_PUBLIC_IP>:53



---

## 3. Test

- On the router, run:  
`nslookup example.com <VM_PUBLIC_IP>`  
You should see a response from the AdGuard Home server.
- From a LAN client, ensure DNS requests are processed (and filtered) as expected.

---

**Result:** All DNS requests from the OpenWrt LAN are now routed through your cloud’s AdGuard Home instance for filtering and logging.
