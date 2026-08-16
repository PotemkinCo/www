# auto delayed geo routing


```bash
cat > /etc/systemd/system/setup_geo_routing.service << EOF
[Unit]
Description=GEO routing setup script

[Service]
Type=oneshot
ExecStart=/root/setup_geo_routing.sh
EOF

cat > /etc/systemd/system/setup_geo_routing.timer << EOF
[Unit]
Description=Run GEO routing in 5 minutes after the boot

[Timer]
OnBootSec=5min

[Install]
WantedBy=timers.target
EOF

# convinience links
ln -s /etc/systemd/system/setup_geo_routing.service ./
ln -s /etc/systemd/system/setup_geo_routing.timer ./

sudo systemctl daemon-reload
sudo systemctl enable --now setup_geo_routing.timer # not the service!

sudo systemctl status setup_geo_routing.timer
```


# Провайдеры
- Турция: https://inferno.name/en/ (из канала vless)
- Беларуссия: https://hoster.by/ (от Романа)


# Outline Performance monitoring
- https://stackoverflow.com/questions/76869983/monitoring-outline-vpn-how-to-access-performance-metrics-of-an-outline-server

## Отключить прямые звонки в Telegram & WhatsApp
- WhatsApp: Настройки (в правом нижнем углу) -> Расширенные (предпоследний пункт снизу) -> Защитить IP-адрес во время звонка
- Telegram:
	- Настройки (в правом нижнем углу) -> Конфиденциальность -> Звонки (четвёртая строка снизу во втором блоке) -> "Peer-to-peer" поставить в "Никогда"
	- "Данные и память" -> "Сократить трафик звонков" - включить (это уменьшит объём трафика)
	- перезагрузить после этого устройство - иначе настройки могут не примениться.

# Outline server binary only

```bash
wget https://github.com/Jigsaw-Code/outline-ss-server/releases/download/v1.9.2/outline-ss-server_1.9.2_linux_x86_64.tar.gz
tar zaf outline-ss-server*.tar.gz
./outline-ss-server --config config.yaml --replay_history 10000
 cat > /lib/systemd/system/outline.service << EOF
[Unit]
Description=Outline server
After=network.target

[Service]
ExecStart=/root/outline-ss-server --config /root/outline-config.yml --replay_history 10000
Restart=always

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable outline
systemctl start outline
systemctl status outline
journalctl -u outline

```
Setting up SSHFS:
```bash
ssh-keygen -t rsa -b 4096 -C "sshfs"
cat id_rsa.pub # and => to `authorized_keys` on another server 
```

## Outline containerized via systemd

as created [[2026-02-02]]

```bash
sudo apt install systemd-container
sudo mkdir -p /var/lib/machines/outline/etc/  /var/lib/machines/outline/usr/lib /var/lib/machines/outline/etc 
sudo touch /var/lib/machines/outline/etc/os-release /var/lib/machines/outline/usr/lib/os-release
cp /home/alex/outline-ss-server /var/lib/machines/outline/outline-server
cp /root/config.yaml /var/lib/machines/outline/config.yaml
touch /var/lib/machines/outline/resolv.conf
sudo tee /etc/systemd/system/outline-wss.service >> /dev/null << 'EOF'
[Unit]
Description=Outline (WebSocket)
After=network.target

[Service]
Type=simple

ExecStart=/usr/bin/systemd-nspawn --quiet \
    -D /var/lib/machines/outline \
    --as-pid2 \
    --network-host \
    /outline-server \
    --config /config.yaml \
    --replay_history 10000

# Restart behavior
Restart=on-failure

[Install]
WantedBy=multi-user.target

EOF
sudo systemctl daemon-reload
sudo systemctl restart outline-wss.service
sudo systemctl status outline.service
```

# Outline WebSocket 
- create WebSocket based Outline server: [doc](https://developers.google.com/outline/docs/guides/service-providers/websockets), but as a matter of fact I need to create server side config, put caddy in front of it and then feed a config to the client - pretty much like I do now; and that service can actually run on the same server, given that I use relay servers for that.. 
      To run:
      ~~`docker run quay.io/outline/shadowbox` to run the server, I guess and the command it `docker-entrypoint.sh /cmd.sh`~~  
      Download the binary from [here](https://github.com/Jigsaw-Code/outline-ss-server/releases) and run it as `outline-ss-server -config=config.yaml` 
      The only question - is how to monitor that process then. Guess I will stick with monit ([example](https://www.claudiokuenzler.com/blog/622/supervision-supervise-daemon-process-application-monit-supervisor))  
      
```bash

sudo apt install wget

wget https://github.com/Jigsaw-Code/outline-ss-server/releases/download/v1.9.2/outline-ss-server_1.9.2_linux_x86_64.tar.gz
tar xzf outline-ss-server_*_linux_x86_64.tar.gz

sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

cat > /etc/caddy/Caddyfile << EOF
vpn.example.com:443 {
    root * /var/www
    
    @websocket path /WS_*
    reverse_proxy @websocket localhost:8080
    
    file_server
}
EOF

cat > /lib/systemd/system/outline.service << EOF
[Unit]
Description=Outline server
After=network.target

[Service]
ExecStart=/home/alex/outline-ss-server --config /root/config.yaml --replay_history 10000
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable outline outline-ss

sudo mkdir /var/www
sudo chown caddy:caddy /var/www

cat > /var/www/index.html <<'EOF'
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="0; url=https://onlysynth.fans/">
  <title>Coming soon...</title>
</head>
<body>
  Redirecting…
</body>
</html>
EOF

cat > /root/config.yaml <<'EOF'
web:
  servers:
    - id: server1
      listen:
        - "127.0.0.1:8080"

services:
  - listeners:
      - type: websocket-stream
        web_server: server1
        path: "/ws-secret-path/tcp"
      - type: websocket-packet
        web_server: server1
        path: "/ws-secret-path/udp"
    keys:
      - id: 'test'
        cipher: chacha20-ietf-poly1305
        secret: <shadowsocks-secret>
EOF

cat > ./client_config.yaml <<'EOF'
transport:
  $type: tcpudp

  tcp:
    $type: shadowsocks

    endpoint:
      $type: websocket
      url: wss://vpn.example.com/ws-secret-path/tcp
    cipher: chacha20-ietf-poly1305
    secret: <shadowsocks-secret>

  udp:
    $type: shadowsocks

    endpoint:
      $type: websocket
      url: wss://vpn.example.com/ws-secret-path/udp
    cipher: chacha20-ietf-poly1305
    secret: <shadowsocks-secret>
EOF

sudo systemctl restart caddy
sudo systemctl status caddy

sudo systemctl start outline outline-ss
sudo systemctl status outline outline-ss

cd /var/www/
mkdir $(printf '%012x' $(($(date +%s%3N))))$(openssl rand -hex 10 | tr '[:lower:]' '[:upper:]')
cd <Tab>
cp ~/client_config.yaml ch1.yaml

```

Adding users:
```bash
vi config.yaml
./ws_users_to_ss_users.py
./send_users_to_dobby_today.sh
```

> [!NOTE] URL shall be single leveled
> Don't do `/owss/sdsdsd` -> outline doesn't know how to handle that


Какая-то информация [[2025-05-06]]
Неофициальная инструкция:  https://codepoetry.ru/post/nastraivaiem/ 
Инструкция по настройке: https://developers.google.com/outline/docs/guides/service-providers/websockets

**SS-over-WS setup**

This is a feature of our core `outline-ss-server` server. It's an advanced feature not available in the out-of-the-box `outline-server` Docker implementation that the Outline Manager deploys.

You don't need to use `outline-ss-server` as a Caddy plugin. You can use SS-over-WS with just the regular `outline-ss-server` (see [instructions](https://developers.google.com/outline/docs/guides/service-providers/websockets)). However, you'll likely want to add TLS in front of the WebSocket endpoints, and that's where you could leverage the Caddy plugin to facilitate automatic HTTPS.

**Prefixing** - looks like other traffic
https://developers.google.com/outline/docs/guides/service-providers/prefixing

**Dynamic keys** - looks like it's an URL to the link, entered in client as `ssconf://`
https://developers.google.com/outline/docs/guides/service-providers/prefixing#dynamic_access_keys
To make them work on iOS - CORS has to be enabled on the server side (as [per](https://www.reddit.com/r/outlinevpn/comments/z49ou8/comment/iy5agjm/?utm_source=share&utm_medium=web3x&utm_name=web3xcss&utm_term=1&utm_content=share_button), a bit more info on [headers](https://github.com/Jigsaw-Code/outline-apps/issues/1596#issuecomment-1472114860)).
JSON example in [issues](https://github.com/Jigsaw-Code/outline-apps/issues/1808). Multi-server is currently not supported. Expiration date seems like defined by a HTTP level headers (as [per](https://github.com/Jigsaw-Code/outline-apps/issues/1591)).

As a **Caddy plugin**: https://github.com/Jigsaw-Code/outline-ss-server/tree/master/outlinecaddy

**outline-ss-server config**: https://github.com/Jigsaw-Code/outline-ss-server/blob/master/cmd/outline-ss-server/config_example.yml

# Test Outline
```bash
OUTLINE_KEY="ss://vpn.example.com/<uuid>/profiles/<user>"
go run github.com/Jigsaw-Code/outline-sdk/x/examples/test-connectivity@latest -transport "$OUTLINE_KEY" && echo success || echo failure
```
[ref](https://github.com/Jigsaw-Code/outline-sdk/tree/main/x/examples/test-connectivity)

# Wireguard Debian/Ubuntu way


# Wireguard via netplan

Ref - [[2025-02-21]], [[2025-02-22]], [[2025-02-23]]

TL;DR: create 2 pair of keys,  2 yaml files for WG, NAT on egress server

```bash
apt install wireguard-tools
wg genkey > private.key
wg pubkey < private.key > public.key
echo 'Private:'
cat private.key
echo 'Public:'
cat public.key
```

## Netplan Wireguard

### Preparation

> [!NOTE] Use cronttab entry from below to clean-up `netplan --try` files
> If missed - server could be bricked.

```bash
crontab -l | { cat; echo "*/1 * * * * find /etc/netplan -name '*.*.yaml' | grep -v '*.yaml' | xargs rm"; } | crontab -
crontab -l
```
### Egress server (primary)

Egress server in region desired (RU, AM, UAE, etc).

Create it in working directory first - `vi wg_in_traffic.yaml`

```yaml
network:
  tunnels:
    wg_in_traffic:
        mode: wireguard
        port: 53160
        key: <client-private-key> # private key
        addresses:
          - 172.17.1.1/30
        peers:
          - allowed-ips: [172.17.1.2/32]
            endpoint: <server-ip>:53160
            keys:
              public: <server-public-key> # public key from the other side
            keepalive: 2
```

Followed by `netplan --debug try --config wg_in_traffic.yaml`

If everything is alright, then:
```bash
cp wg_in_traffic.yaml /etc/netplan/99_wg_in_traffic.yaml
netplan try
netplan apply
ls /etc/netplan
shutdown -r now
```

### Routing server

> [!WARNING] Verify cleaning crontab is in place!

```bash
crontab -l | { cat; echo "*/1 * * * * find /etc/netplan -name '*.*.yaml' | grep -v '*.yaml' | xargs rm"; } | crontab -
crontab -l
```

Create netplan yaml in working directory first - `vi wg_ru_traffic.yaml`

```yaml
network:
  tunnels:
    wg_out_traffic:
      mode: wireguard
      port: 53160
      key: <client-private-key> # private key from that machine
      addresses:
        - 172.17.1.2/30
      peers:
        - allowed-ips: [172.17.1.1/32, 0.0.0.0/0]
          endpoint: <server-ip>:53160
          keys:
            public: <server-public-key> # public key from another
          keepalive: 2
```

Followed by `netplan --debug try --config wg_ru_traffic.yaml`

### NAT - on egress server

Apply the following forward rule. Be sure the IP address for returning the traffic is correct! 
```bash
sudo apt -y install ufw
sudo sed -i 's/DEFAULT_FORWARD_POLICY="DROP"/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw
sudo sed -i 's/DEFAULT_INPUT_POLICY="DROP"/DEFAULT_INPUT_POLICY="ACCEPT"/' /etc/default/ufw
grep FORWARD_POLICY /etc/default/ufw
grep INPUT_POLICY /etc/default/ufw
sudo sed -i 's|#net/ipv4/ip_forward=1|net/ipv4/ip_forward=1|' /etc/ufw/sysctl.conf
grep ip_forward /etc/ufw/sysctl.conf

echo '
# NAT table rules
*nat
:POSTROUTING ACCEPT [0:0]

# CHANGE ME: IP address of LAN and interface of WAN
-A POSTROUTING -s 172.22.2.1/30 -o eth0 -j MASQUERADE

COMMIT
' | cat - /etc/ufw/before.rules > /tmp/before_rules.full && cp /tmp/before_rules.full /etc/ufw/before.rules

sudo ufw disable && sudo ufw enable
```
### Add routing entries on the routing server

1. Disable IPv6 on that server, as otherwise all IPv6 addresses will be resolved directly
2. Do:
```bash
cd netplant_geo_route && uv run main.py
cat wg_to_ru_interface.yaml > wg_with_ru_traffic_routes.yaml && cat ./netplan_geo_route/netplan-RU.yaml >> wg_with_ru_traffic_routes.yaml
netplan try --config wg_with_ru_traffic_routes.yaml
route add <server-ip>/32 gw <gateway-ip> # for egres
route add <relay-ip>/32 gw <gateway-ip> # for every relay
```

### Adding new user
- Create user on Outline manager - note username, close Outline Manager app
- Take password from `outline-config.yml` file and save it in users.ini on vpn.example.com server
- Send the link `https://https://vpn.example.com/link?token=ssconf://vpn.example.com/<uuid>/profiles/<user>`

# TODO

- Setup reverse PTR records!!!
- проверить работу сертификата: ``curl -v --resolve www.microsoft.com:443:151.101.65.69 https://www.microsoft.com` (вместо 151.101.xx.xx должен быть IP вашего сервера)`

# Amnezia VPN front-end

https://github.com/w0rng/amnezia-wg-easy

# Найти под кого (домен) прикидываемся 

https://github.com/XTLS/RealiTLScanner
```bash
sudo apt install git build-essential
snap install go --classic
git clone https://github.com/XTLS/RealiTLScanner.git
cd RealiTLScanner
go build
./RealiTLScanner -addr 1.2.3.4
```
# Outline

Credentials file is /opt/outline/access.txt, convert them into the Outline Manager string with ([ref](https://developers.google.com/outline/docs/guides/service-providers/share-management-access)):
```bash
sed -n '2s/^apiUrl://p; 1s/^certSha256://p' /opt/outline/access.txt | paste -d'\n' -s | sed 'H;1h;$!d;x;s/\n/", \"apiUrl\": \"/g; s/^/{"certSha256": \"/; s/$/\"}/'
```

Outline config for relay:
- change IP address
- add `/?outline=1&prefix=GET%20%2F%20HTTP%2F1.1%0D%0A%0D%0A` after server name

``` bash
sudo ufw default allow incoming
sudo ufw default allow outgoing
sudo ufw enable

sudo wget -O /usr/local/bin/ufw-docker \
  https://github.com/chaifeng/ufw-docker/raw/master/ufw-docker
sudo chmod +x /usr/local/bin/ufw-docker
sudo ufw-docker install
sudo systemctl restart ufw
sudo ufw-docker check
sudo ufw default deny incoming
sudo ufw allow proto any from any port 23534 to any port 23534 # ssh access restricted to SRC port
sudo ufw allow proto tcp from <mgmt-server-ip> to any port 9687 # management port from my nocloud server only
sudo ufw allow proto tcp from any to any port 443 # ShadowSocks
sudo ufw status numbered
sudo ufw enable
```

**Ref:**
- Outline install without Docker [script](https://gist.github.com/delfer/efa0a0bcf6393df255617ed8d1f3f14b)

# Ports forwarding

## ipchains way

It's better to verify if there are any other firewall rules: `iptables -nvL`.
If things doesn't work - it might be worth to flush those rules with:
```bash
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -t nat -F
iptables -t mangle -F
iptables -F
iptables -X
```

```bash
echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
sudo sysctl -p
d_ip=<server-ip>
d_port=443
iptables -t nat -A PREROUTING -p tcp --dport 443 -j DNAT --to-destination $d_ip:$d_port
iptables -t nat -A PREROUTING -p udp --dport 443 -j DNAT --to-destination $d_ip:$d_port
iptables -t nat -A POSTROUTING -j MASQUERADE
iptables -L -n -t nat # shall display forward & masquerade
# iptables -I FORWARD -j LOG # enable logging
cat >> /etc/network/if-pre-up.d/iptablesload <<EOF 
#!/bin/sh
iptables-restore < /etc/iptables.rules
exit 0
EOF
chmod +x /etc/network/if-pre-up.d/iptablesload
iptables-save > /etc/iptables.rules
```

## socat way

### docker-compose way

`bash <(curl -s https://get.docker.com)`

as per [ref1](https://stackoverflow.com/questions/56582446/how-to-use-host-network-for-docker-compose), [ref2](https://hub.docker.com/r/alpine/socat).
```yaml
services:
  dobby_outline_mgmnt_socat:
    image: alpine/socat
    container_name: socat_dobby_outline_mgmnt
    command: "-d -d TCP-LISTEN:43180,fork TCP:dobbyvpn-testbed1:43180"
    restart: unless-stopped
    network_mode: "host"

  dobby_outline_ss_socat:
    image: alpine/socat
    container_name: dobby_outline_ss_socat
    command: "-d TCP-LISTEN:40287,fork TCP:dobbyvpn-testbed1:40287"
    restart: unless-stopped
    network_mode: "host"

        #  dobby_outline_ss_socat_udp:
        #    image: alpine/socat
        #    container_name: dobby_outline_ss_socat_udp
        #    command: "UDP-LISTEN:40287,fork UDP:dobbyvpn-testbed1:4087"
        #    ports:
        #      - 40287:40287/udp
        #    network_mode: "host"

```

### systemd service
```bash
cat >> socat.service <<EOF 
[Unit]
Description=Socat
After=multi-user.target

[Service]
Type=simple
ExecStart=/usr/bin/socat TCP4-LISTEN:443,fork TCP4:<destination-ip>:443
Restart=on-failure
RestartSec=6
StandardOutput=syslog  
StandardError=syslog  
SyslogIdentifier=socat

[Install]
WantedBy=multi-user.target
EOF

sudo cp socat.service /etc/systemd/system
sudo apt install socat
systemctl enable socat
systemctl start socat
systemctl status socat
```

### as a command, not a service

```bash
nohup socat UDP4-RECVFROM:65326,fork UDP4-SENDTO:$IP:65326 #UDP traffic forward
nohup socat TCP4-LISTEN:443,fork TCP4:<destination-ip>:443 # TCP port forward

```

# Troubleshooting

I've found `pwru` a wonderful [packet inspection tool](https://github.com/cilium/pwru) I was looking for (from [here](https://github.com/SagerNet/sing-box/issues/2655))

# Clients
- v2box might be a good client, but it comes with ad
- foxray might be a good thing - has paid feature, but config files format is different + WhatsApp calls didn't work for Agorbunov on MegaFon; also [doesn't support xray config in full](https://yiguo.dev/docs/apple/routingdns/)

Recommended:
	- NekoRay / NekoBox -> Linux & Windows
	- FoXray -> MacOS; URL schema described [here](https://yiguo.dev/docs/apple/develop/)
	- v2rayNG -> Android
	- [Streisands](https://streisand.pages.dev/) -> iOS: my note - it is not very stable while changing network
	- GUI.for.Cores - вроде адекватный, но [не умеет поднимать права](https://gui-for-cores.github.io/guide/03-how-it-works)

# Hiddify

Seems to be the best app so far.
Subscription's file is just a file with a list of config URLs, as per [[2025-02-13]] findings.

Нашёл [формат файлов подписки](https://github.com/koroshkorosh1/Hiddify_Subscription) - это просто обычные файлы с обычными строками. 
	Тут же [нашёл документацию по URL-ам](https://github.com/hiddify/hiddify-app/wiki/URL-Scheme/2611c46ace01a87eb2a1c1b3b81b97eeb85e3d37).

```bash
pwgen 88 | tail -1 # for file name generation
```

Config's structure:
```
#profile-title: H4AG
#profile-title: base64:base64string
#profile-update-interval: 1
vless://<uuid>@<server-ip>:443/?encryption=none&type=tcp&sni=example.com&fp=chrome&security=reality&alpn=h2&sid=<short-id>&flow=xtls-rprx-vision&pbk=<public-key>&packetEncoding=xudp#Vless-Reality
ss://<base64-credentials>@<server-ip>:443/?outline=1&prefix=GET%20%2F%20HTTP%2F1.1%0D%0A%0D%0A#Outline-Reality
```

# Sing-box

### From closed chat

ToDo: understand how urltest parameters actually work

>> Is it correct to understand that  "type": "urltest", - is my way to choose fastest server, based on ping?

> urltest sends HTTP requests via outbound to detect latency, so it is not ping.

>> It is also the way to ping all of the servers specified in there every "interval": "1m", (1 minute in my config), change the connection to another server or restart existing as per "tolerance": 50, value (50 ms in my config) and keep tunnel open as per "idle_timeout": "0", parameter (zero means do not ever close it; otherwise - close tunnel connection when no active packets for that time)?

> Connections on L4 proxies cannot be switched to other servers like you would think, like WireGuard. If a switch occurs, the old connection cannot be moved to another server.

> "type": "selector", is a way to let user choose the server manually in the interface + logical abstraction to reference server(s) inside my config?

> It sounds like this

[automatic installation script](https://github.com/deathline94/sing-REALITY-Box/blob/main/sing-REALITY-box.sh) - my procedure is adapted version of it, given the use of Docker
[Official docs.](https://sing-box.sagernet.org/configuration/)

Client & server configs are descendants from [Clash](https://en.clash.wiki/configuration/outbound.html)

```bash
wget https://raw.githubusercontent.com/NoCloud-today/tools/main/ubuntu_setup.sh && sudo bash ubuntu_setup.sh
```

```bash
curl https://get.docker.com/ | sh
cat << EOF >> docker-compose.yml
version: "3.8"
services:
  sing-box:
    image: ghcr.io/sagernet/sing-box
    container_name: sing-box
    restart: unless-stopped
    volumes:
      - ./sing-box:/etc/sing-box/
    command: -D /var/lib/sing-box -C /etc/sing-box/ run -c /etc/sing-box/reality.json
    network_mode: "host"
EOF
```

To generate keys & uuids:
```bash
#!/bin/bash
#set -x
set -e
sudo apt install -y jq 
config_file_name='reality.json'
read -p "Enter server name/SNI (default: myserver.com): " server_name
listen_port=443
server_ip=$(curl -s ipinfo.io/ip)
sing_box_exec='docker run -v ./sing-box:/etc/sing-box/ ghcr.io/sagernet/sing-box -D /var/lib/sing-box -C /etc/sing-box/'
key_pair=$($sing_box_exec generate reality-keypair)
uuid=$($sing_box_exec generate uuid)
short_id=$($sing_box_exec generate rand --hex 8)
private_key=$(echo "$key_pair" | awk '/PrivateKey/ {print $2}' | tr -d '"')
public_key=$(echo "$key_pair" | awk '/PublicKey/ {print $2}' | tr -d '"')
echo "Short id: $short_id"
echo "UUID (first): $uuid"
echo "Private key: $private_key"
echo "Public key: $public_key"

jq -n --arg listen_port "$listen_port" --arg server_name "$server_name" --arg private_key "$private_key" --arg short_id "$short_id" --arg uuid "$uuid" --arg server_ip "$server_ip" '{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "vless",
      "tag": "vless-in",
      "listen": "::",
      "listen_port": ($listen_port | tonumber),
      "sniff": true,
      "sniff_override_destination": true,
      "domain_strategy": "ipv4_only",
      "users": [
        {
          "name": "user1",
          "uuid": $uuid,
          "flow": "xtls-rprx-vision"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": $server_name,
          "reality": {
          "enabled": true,
          "handshake": {
            "server": $server_name,
            "server_port": 443
          },
          "private_key": $private_key,
          "short_id": [$short_id]
        }
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    },
    {
      "type": "block",
      "tag": "block"
    }
  ]
}' > "sing-box/$config_file_name"

`$sing_box_exec check -c "/etc/sing-box/$config_file_name"`

echo
echo "First key prepared: $server_link"
echo

```

## Create client's connection id
```bash
sing_box_exec='docker run -v ./sing-box:/etc/sing-box/ ghcr.io/sagernet/sing-box -D /var/lib/sing-box -C /etc/sing-box/'
uuid=$($sing_box_exec generate uuid)
echo $uuid

docker run -v ./sing-box:/etc/sing-box/ ghcr.io/sagernet/sing-box -D /var/lib/sing-box -C /etc/sing-box/ generate uuid

```

## Config

To merge few configs, the `-c configFile` or `-C configDir` option shall be used (as per [manual](https://sing-box.sagernet.org/configuration/#merge)), or, to be more precise, here is the algorithm (as per [changelog](https://sing-box.sagernet.org/changelog/#12-beta10)):
> Now you can pass the parameter `--config` or `-c` multiple times, or use the new parameter `--config-directory` or `-C` to load all configuration files in a directory.
>Loaded configuration files are sorted by name. If you want to control the merge order, add a numeric prefix to the file name.

SingBox [client's config](https://sing-box.sagernet.org/manual/proxy/client/) - I can't see the reconnect option; but I've found multiples [JSON examples](https://github.com/malikshi/sing-box-examples/tree/main) and [some more](https://vpnrouter.homes/singbox-ready/) - leaving it for now

Following up [the tutorial](https://vpnrouter.homes/singbox-config/):
```json
"log": { "disabled": false, "level": "error", "timestamp": true }

```

Random links:
- config с объяснениями: https://github.com/malikshi/sing-box-examples/blob/main/Trojan%20Websocket/README.md
- one more adequate config: https://gist.github.com/woyin/f7656f6b7ca76bb46bf6260d20700c24
- seems like adequate config: https://github.com/WhyMan1/marzban-template/blob/master/singbox/default.json
- 
- https://krasovs.ky/2024/08/05/sing-box-bypass.html
- https://wener.me/notes/service/network/proxy/sing-box/config
- https://github.com/malikshi/sing-box-examples -> looks out of date
- https://github.com/chika0801/sing-box-examples/blob/main/VLESS-Vision-REALITY/config_client.json -> looks right
- https://habr.com/ru/articles/853796/ - c базами данных IP РФ
- https://sing-box.sagernet.org/configuration/shared/v2ray-transport/#structure - docs
- https://vpnrouter.homes/singbox-config/ -> some kind of docs, not very adequate, I would say
- репа с настройкой Trojan: https://github.com/BLUEBL0B/Secret-Sing-Box

## Sing-box's server dashboard
- https://github.com/Zephyruso/zashboard -> works via clash api (experimental block)

### vless server:

`docker-compose.yml:`
```yaml
services:
  sing-box:
    image: ghcr.io/sagernet/sing-box:v1.11.4
    container_name: sing-box
    restart: unless-stopped
    volumes:
      - ./sing-box:/etc/sing-box/
    command: -D /var/lib/sing-box -C /etc/sing-box/ run -c /etc/sing-box/reality.json
    network_mode: "host"
```

`reality.json`
```json
{
  "log": {
    "level": "trace",
    "timestamp": true
  },
  "inbounds": [
  {
      "type": "vless",
      "tag": "vless-in",
      "listen": "::",
      "listen_port": 443,
      "sniff": true,
      "sniff_override_destination": true,
      "domain_strategy": "ipv4_only",
      "users": [
        {
          "name": "user1",
          "uuid": "24320746-837c-45a3-bbeb-ac919011d91c",
          "flow": "xtls-rprx-vision"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "vpn.example.com",
        "reality": {
          "enabled": true,
          "handshake": {
            "server": "vpn.example.com",
            "server_port": 443
          },
          "private_key": "<reality-private-key>",
          "short_id": [
        "<short-id>"
      ]
        }
     },
     "multiplex": {
        "enabled": true,
        "brutal": {
          "enabled": false
        }
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    },
    {
      "type": "block",
      "tag": "block"
    }
  ]
}
```
# XRay

- https://github.com/XTLS/Xray-core/discussions/3518 - good doc to read
- Дока по VLess config: https://xtls.github.io/en/config/log.html#logobject

Хорошие документы по моим вопросам:
- настройка vless + vision: https://github.com/XTLS/Xray-core/discussions/3518 И ОБЪЯСНЕНИЕ
- как сделать хорошо: По статье настроить, не маскироваться под google/yahoo/сайт за CDN, ходить на панель только под ssh -L, держать inbound на 443 порту, fingerprint - chrome. Мб ещё что-то забыл.
	Этот комбайн полностью тут расписан
	https://xtls.github.io/ru/
	А примеры настроек можно тут посмотреть
	https://github.com/XTLS/Xray-examples/tree/main/VLESS-TCP-XTLS-Vision-REALITY
- как работает шифрование и снятие слоёв:
	https://github.com/XTLS/Xray-core/blob/main/proxy/proxy.go
	
	https://github.com/XTLS/Xray-core/blob/main/proxy/vless/encoding/encoding.go
	
	Опять же повторюсь, два слоя: внутренний (юзер-сайт), внешний: прокси соединение.
	Первый вложен во второе
	Устанавливаем соединение, дальше просто буфер копируем 1:1 не нарушая структуру внутреннего
	
	Тут единственный нюанс который надо знать что на трафик tls 1.2 внутреннего слоя vision применяется только частично (padding)

Ref:
- https://habr.com/ru/articles/799751/
- https://github.com/EmptyLibra/Configure-Xray-with-VLESS-Reality-on-VPS-server/

Forums:
- https://github.com/net4people/bbs/issues
- https://ntc.party/

Pick up latest versions:
- XRay from [Releases](https://github.com/XTLS/Xray-core/releases)
- Scanner from [Releases](https://github.com/XTLS/RealiTLScanner/releases/tag/v0.2.1)
```bash
wget https://github.com/XTLS/Xray-core/releases/download/v25.1.30/Xray-linux-64.zip
apt install unzip
mkdir /opt/xray  
unzip ./Xray-linux-64.zip -d /opt/xray  
chmod +x /opt/xray/xray

cat << EOF >> /usr/lib/systemd/system/xray.service
[Unit]  
Description=XRay  
[Service]  
Type=simple  
Restart=on-failure  
RestartSec=30  
WorkingDirectory=/opt/xray  
ExecStart=/opt/xray/xray run -c /opt/xray/config.json  
[Install]  
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable xray

# Optional - to choose IP address
# wget https://github.com/XTLS/RealiTLScanner/releases/download/v0.2.1/RealiTLScanner-linux-64
# chmod +x RealiTLScanner-linux-64 
# curl ipinfo.io
# ./RealiTLScanner-linux-64 -addr $IP -showFail

openssl rand -hex 8 # for the streamSettings -> shortIds
/opt/xray/xray uuid # generates user's id -> 1 user = 1 id
/opt/xray/xray x25519 # public and private keys
systemctl restart xray
systemctl status xray
journalctl -u xray
```

Generating new clients keys:
```bash
/opt/xray/xray uuid
vi /opt/xray/config.json # add new keys there
```

Connection string shall be: `vless://ваш_UUID@IP_адрес_вашего_сервера:443/?encryption=none&type=tcp&sni=домен_сайта&fp=chrome&security=reality&alpn=h2&flow=xtls-rprx-vision&pbk=ваш_публичный_ключ&packetEncoding=xudp`

# BBR

Increase speed:
```bash
cat << EOF >> /etc/sysctl.d/10-custom-kernel-bbr.conf
net.core.default_qdisc=fq
net.ipv4.tcp_congestion_control=bbr
EOF

service procps force-reload
# sysctl -p # guess that is redundant
```

# Var

Короткая выжимка и для меня самого и если кому интересно:
- XRay - наряду с SingBox - софтверная реализация различных протоколов для обхода блокировок - про остальные можно забыть (сдулись)
- VLESS - самый адекватный протокол для обхода блокировок - но суть его в выявлении свой-чужой и отправлении цензора на другой сайт; он умеет заворачиваться в TLS 
- к нему есть extensions - которые бог весть почему называются также протоколами - XTLS-Reality - тот что нас интересует более всего - он позволяет делать TLS 1.3 (что есть хорошо - ибо там есть ChaCha20_Poly1305 - как и в Wireguard и это хорошо) и прокидывать трафик на условный vk.com
- XTLS-Vision - убирает лишний слой шифрования (вот как это происходит я до сих пор не понял) - но требует своего доменного имени; НО - XTLS-Reality является расширением поверх XTLS-Vision и снимает это требование.
Помимо ускорения работы и снижения требования на батарейку (телефона) доп. слой шифрования становится флагом для нейросеток внутри DPI - так что это надо делать по любому.
Что дальше важно / какой вопрос возникает: как сделать чтобы IP адрес реально выглядел как что-то обычное?
Ответ: RealiTLScanner - тул (https://github.com/XTLS/RealiTLScanner), который сканирует соседей по IP адресу и предлагает под кого прикидываться будем.
Итак:
VLess —extended_by—> XTLS-Vision —extended_by—> XTLS-Reality == готовый нужный пакет. 
Что делают сейчас разработчики - пишут основные слова через дефис/слеш/...:  XRay/VLESS/XTLS-Reality - видя эти слова понимаем что имеем протокол VLESS с двумя расширениями: XTLS-Reality & XTLS-Vision (последний включен в предыдущий). Ну и если совсем копать, то понимаем что пользуется XTLS.
Со стороны клиента мы ещё хотим uTLS - чтобы максимально выглядеть как браузеры. Ок - не максимально, но достаточно близко. 
Соответственно, если смотреть на этот инструментарий - то это самый рабочий вариант.
Настройка этого добра происходит через довольно изощрённый config.json в котором прописываются правила входа и выхода - как на клиенте, так и на сервере. В этом же конфиге задаются правила для роутинга - чтобы трафик внутри страны пускать внутри страны - чтобы не создавать один очень толстый канал связи с единственным сервером и таким образом не выдать VPN сервер.
Кажется, что это всё - по крайней мере, как будто со всех сторон в таком случае решается проблема.
Последний штрих: оказывается, эти протоколы изначально работали как proxy - а не как VPN - добавление проброса всего трафика по VPN - через TUN - фича, которая есть не у всех. Стало быть, если мы сюда доберёмся когда-нибудь и добавим этот набор инструментов (не вижу это приоритетом - пока изучал - ещё больше убедился в том что наш набор из outline & cloak & awg довольно полезен) - то это будет хороший плюс.

--

Из чата Project VLESS:
Reality — форк TLS 1.3.
Т.е. полноценный TLS с дополнительными инструментами.

VISION — объект VLESS, предотвращающий TLS in TLS.
Так как Reality тот же TLS, но с дополнительными инструментами, он не защищен сам по себе от TLS in TLS.
Поэтому VISION нужно применять.

# VPN (Wireguard)


```bash
sudo ln -s /usr/bin/resolvectl /usr/local/bin/resolvconf
sudo su -
wget https://raw.githubusercontent.com/alexander-potemkin/quick-wireguard/master/wireguard-install.sh && chmod +x wireguard-install.sh 
```


> [!NOTE] 'resolvconf: command not found' error
> To be sorted with `ln -s /usr/bin/resolvectl /usr/local/bin/resolvconf` command line ([ref](https://superuser.com/questions/1500691/usr-bin-wg-quick-line-31-resolvconf-command-not-found-wireguard-debian)); resolvconf package might brake some software

## server-to-server
as [per](https://www.reddit.com/r/WireGuard/comments/ru6tvh/connecting_to_wireguard_server_from_ubuntu/):
```bash
apt install wireguard
vi /etc/wireguard/wg1.conf
wg-quick up wg1
wg-quick down wg1
systemctl enable wg-quick@wg1.service

```


### Users list

```bash
#!/bin/bash

echo "Keys list:"
echo "----------"
grep -i client /etc/wireguard/wg0.conf | awk '{print $3}' | sort
echo

echo "Users list:"
echo "-----------"
grep -i client /etc/wireguard/wg0.conf | awk '{print $3}' | sort | awk -F '_' '{print $1}' | grep -v alexp | grep -v agorbunov | grep -v ii5 | uniq
echo

echo "Total:"
grep -i client /etc/wireguard/wg0.conf | awk '{print $3}' | sort | awk -F '_' '{print $1}' | grep -v alexp | grep -v agorbunov | grep -v ii5 | uniq | wc -l
echo
```
## Notes

Routing thing: [https://www.poftut.com/add-new-route-ubuntu-linux/](https://www.poftut.com/add-new-route-ubuntu-linux/)
```
sudo route add -net 10.0.0.0/8 gw 192.168.168.1 ens4
```

For the office computers with internal network AND to the intranet (192.168.168.0/24), add that:

```bash
AllowedIPs = 1.0.0.0/8, 2.0.0.0/8, 3.0.0.0/8, 4.0.0.0/6, 8.0.0.0/7, 11.0.0.0/8, 12.0.0.0/6, 16.0.0.0/4, 32.0.0.0/3, 64.0.0.0/2, 128.0.0.0/3, 160.0.0.0/5, 168.0.0.0/6, 172.0.0.0/12, 172.32.0.0/11, 172.64.0.0/10, 172.128.0.0/9, 173.0.0.0/8, 174.0.0.0/7, 176.0.0.0/4, 192.0.0.0/9, 192.128.0.0/11, 192.160.0.0/13, 192.168.168.0/24, 192.169.0.0/16, 192.170.0.0/15, 192.172.0.0/14, 192.176.0.0/12, 192.192.0.0/10, 193.0.0.0/8, 194.0.0.0/7, 196.0.0.0/6, 200.0.0.0/5, 208.0.0.0/4, 94.140.14.14/32, 94.140.15.15/32
```

All traffic's AllowedIPs is `0.0.0.0/0, ::/0`.

Just the cloud traffic AllowedIPs is  `192.168.168.0/24, IP/32, IP/32` - which is intranet network and DNS server's IPs with /32 network on it.

Working note: netmask 255.255.255.0 network is in use.

## Server side (very limited) logging:

```bash
sudo su -
echo "module wireguard +p" | tee /sys/kernel/debug/dynamic_debug/control
touch /var/log/wireguard.log
nohup dmesg -T --follow | egrep "(wireguard:|wg0)" >> /var/log/wireguard.log
```

Some usefull commands:

```bash
wg show all dump
```

Generate QR code

```bash
qrencode -t ansiutf8 -l L < ...conf #to generate QR code
```

Various:

```bash
# sudo vi /etc/sysctl.conf
# sudo sysctl -p
net.ipv4.ip_forward = 1
```


## On Windows - background service

Is created, as [per](https://github.com/WireGuard/wireguard-windows/blob/master/docs/enterprise.md).

## No-go tools & services:
- https://github.com/tailscale/tailscale - wg management thing
- https://github.com/complexorganizations/wireguard-manager - cli wrapper
- check for [https://www.procustodibus.com/](https://www.procustodibus.com/)


# Socks5 proxy for Telegram
```bash
sudo su -

apt install dante-server
mv /etc/danted.conf /etc/danted.conf.bak

useradd -r -s /bin/false daldalim
passwd daldalim

cat << EOF > /etc/danted.conf
debug: 2
logoutput: syslog
user.privileged: root
user.unprivileged: nobody

# The listening network interface or address.
internal: 0.0.0.0 port=443

# The proxying network interface or address.
external: eth0

# socks-rules determine what is proxied through the external interface.
socksmethod: username

# client-rules determine who can connect to the internal interface.
clientmethod: none

client pass {
    from: 0.0.0.0/0 to: 0.0.0.0/0
}

socks pass {
    from: 0.0.0.0/0 to: 0.0.0.0/0
}
EOF

systemctl restart danted.service
systemctl status danted.service

```

# Заметки из DobbyVPN

# Notes
- 2025-08-18
	- и да - люди хотят чтобы я сохранял информацию - которая нужна чтобы обеспечивать лучшую работу сервиса: никого не устраивает (и я сам такой же был) история про то, что логов нет - ничего нельзя поделать (как я тикет в WARP писал, я помню)
	- и ещё один момент: каждый человек хочет очень человеческого к себе отношения и глубой проработки - я готов это давать, но только за очень приличные деньги 


- сделать демо того сколько информации знает VPN: страна, куда ты ходишь, когда ты ходишь, какая у тебя операционная система



# Servers logs
- RuVDS:
	- KZ, Astana - numerous heartbeat failures to dobby-today (2025-06-03)
	- RU, MSK, M9 - моргает (2025-06-03)
	- RU, MSK, Королёв - awful as well, decommissioning (2025-06-04)
- Selectel -> [regions](https://docs.selectel.ru/control-panel-actions/infrastructure/?country=russia&ru-regions=msk)
	- ru-3b (SPB) -> numerous heartbeat failures to dobby-today (2025-06-03)
	- ru-9a (SPB) - quite bad, decomissioning (2025-06-04)
	- ru-8a (OVB / Novosibirsk) -> numerous heartbeat failures to dobby-today (2025-06-03)
	- ke-1a (Kenya (Nairoby)) -> 1.1.1.1 ping failures + numerous hearbeat failures to dobby-today (2025-06-03)
	- ru-7a (MSK) - 

Setting up RuVDS server:
```bash
vi ~/.ssh/authorized_keys # put SSH key there
apt update && apt install vi aptd bc
systemctl unmask unattended-upgrades && systemctl enable unattended-upgrades
unminimize # this might take up to 1 hour
```


My script:
```bash
sudo apt update && apt install monit
cat > /etc/monit/monitrc <<EOF 
set mmonit https://monit:hdOAmP85JvXPZU6lgvuDFqp2yIfi1AdqyXliGaL9@rdr.vpn.example.com/collector
  with timeout 5 seconds
set daemon 10

check system $HOST
  if cpu usage > 90% for 10 cycles then alert
  if memory usage > 85% then alert
  if swap usage > 70% then alert
check filesystem rootfs with path / if space usage > 90% then alert

check file root_ssh_keys with path /root/.ssh/authorized_keys if changed checksum then alert
check file etc_passwd with path /etc/passwd if changed checksum then alert

check host 1.1.1.1 with address 1.1.1.1 if failed ping count 2 then alert
check host yandex_ru with address yandex.ru if failed ping count 2 then alert

set httpd port 2812 use address 127.0.0.1 allow monicli:Thei1IquaeS
set log /var/log/monit.log
set idfile /var/lib/monit/id
set statefile /var/lib/monit/state
set eventqueue basedir /var/lib/monit/events slots 1000
EOF
monit reload all
```

And then `ipchains` port NAT-ing:

```bash
echo 'net.ipv4.ip_forward = 1' >> /etc/sysctl.conf
sudo sysctl -p
iptables -t nat -A PREROUTING -p tcp --dport 443 -j DNAT --to-destination <destination-ip>:443
iptables -t nat -A POSTROUTING -j MASQUERADE
iptables -L -n -t nat # shall display forward & masquerade
# iptables -I FORWARD -j LOG # enable logging
cat >> /etc/network/if-pre-up.d/iptablesload <<EOF 
#!/bin/sh
iptables-restore < /etc/iptables.rules
exit 0
EOF
chmod +x /etc/network/if-pre-up.d/iptablesload
iptables-save > /etc/iptables.rules
```

And automatic reboot:
```bash
crontab -l | { cat; echo "$((RANDOM % 60)) $((2 + RANDOM % 4)) * * * /bin/sh -c '[ -f /var/run/reboot-required ] && sudo shutdown -r now'"; } | crontab -
```