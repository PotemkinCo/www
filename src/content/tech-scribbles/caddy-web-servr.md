---
title: "caddy web servr"
---

# Pass IP address when running on a rootless Docker
```bash
mkdir -p ~/.config/systemd/user/docker.service.d/
cat > ~/.config/systemd/user/docker.service.d/override.conf << EOF
[Service]
Environment=DOCKERD_ROOTLESS_ROOTLESSKIT_PORT_DRIVER="slirp4netns"
EOF
systemctl --user daemon-reload
systemctl --user restart docker
```


# Rate limits

```json
(rate_limit) {
	rate_limit {
		zone per_ip {
			key    {remote_ip}
			events 100
			window 10s
		}
		zone global {
			key    static
			events 1000
			window 1s
		}
	}
}
```

followed by: `import rate_limit` under every domain

Before restarting:
```bash
caddy validate --config /etc/caddy/Caddyfile
```

# Logs (Apache / Common log)
- [transform-encoder extension](https://github.com/caddyserver/transform-encoder)
```bash
$ caddy add-package github.com/caddyserver/transform-encoder
```
and
` format transform "{common_log}"`

## to preserve on reboot (remote build server on Ubuntu way)

That creates a service that install extension required before the caddy start.

```bash
#!/usr/bin/env bash
set -euo pipefail

sudo tee /etc/systemd/system/caddy-packages.service > /dev/null <<'EOF'
[Unit]
Description=Ensure Caddy custom packages
Before=caddy.service

[Service]
Type=oneshot
ExecStart=/usr/bin/caddy add-package github.com/caddyserver/transform-encoder github.com/mholt/caddy-ratelimit
SuccessExitStatus=1

[Install]
WantedBy=caddy.service
EOF

sudo systemctl daemon-reload

sudo systemctl start caddy-packages.service
sudo systemctl status caddy-packages.service --no-pager # VERIFY IT DIDN'T FAIL!

sudo systemctl enable caddy-packages.service
sudo systemctl restart caddy
```

force to rebuild, if necessary:

```bash
sudo /usr/bin/caddy remove-package github.com/caddyserver/transform-encoder github.com/mholt/caddy-ratelimit
sudo systemctl start caddy-packages.service
```

## to preserve on reboot (xcaddy Ubuntu way)

That creates a service that install extension required before the caddy start.

```bash
#!/usr/bin/env bash
set -euo pipefail

sudo snap install go --classic

# Install xcaddy if needed
if ! command -v xcaddy &>/dev/null; then
  sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/xcaddy/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-xcaddy-archive-keyring.gpg
  curl -1sLf 'https://dl.cloudsmith.io/public/caddy/xcaddy/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-xcaddy.list
  sudo apt update && sudo apt install xcaddy
fi

sudo tee /etc/systemd/system/caddy-packages.service > /dev/null <<'EOF'
[Unit]
Description=Ensure Caddy custom packages
Before=caddy.service

[Service]
Type=oneshot
User=root
Environment=HOME=/root
Environment=GOPATH=/tmp/go
Environment=PATH=/snap/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ExecStart=xcaddy build --with github.com/caddyserver/transform-encoder --with github.com/mholt/caddy-ratelimit --output /usr/bin/caddy

[Install]
WantedBy=caddy.service
EOF

sudo systemctl daemon-reload
sudo systemctl start caddy-packages.service
sudo systemctl status caddy-packages.service --no-pager # VERIFY IT DIDN'T FAIL!
sudo systemctl enable caddy-packages.service
sudo systemctl restart caddy
```

# UDP buffer (for QUIC)

https://github.com/quic-go/quic-go/wiki/UDP-Buffer-Sizes

# Build for custom extensions - using Docker
[Ref](https://github.com/caddyserver/caddy/issues/5999#issuecomment-2843518285)

https://caddyserver.com/docs/build#docker


## Custom SSL certificate

add  `tls /etc/ssl/xyz.crt /etc/ssl/xyz.key` just below domain's name line.

crt & key files: [seems](https://serverfault.com/a/224127) like 'crt and key files represent both parts of a certificate, key being the private key to the certificate and crt being the signed certificate.' [Or](https://serverfault.com/a/224125), 'These are the public (.crt) and private (.key) parts of an SSL certificate.'

So, just upload those files, restart caddy and you are done!

# Debug (including L4 level proxy)

As [per](https://github.com/mholt/caddy-l4/issues/246#issuecomment-2455883759):
> Put the word `debug` in your global options: [https://caddyserver.com/docs/caddyfile/options#debug](https://caddyserver.com/docs/caddyfile/options#debug)
## nginx like log

https://github.com/caddyserver/transform-encoder/issues/38#issuecomment-1971081260

# install caddy

### Docker

`wget -O - https://get.docker.com | sudo bash`
```yaml
services:
  caddy:
    image: caddy:2-alpine
    container_name: caddy
    restart: unless-stopped
    volumes:
       - ./Caddyfile:/etc/caddy/Caddyfile
       - ./caddy_data:/data
       - ./caddy_config:/config
    ports:
       - 80:80
       - 443:443
```

## apt
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

`vi /etc/caddy/Caddyfile`:
# /etc/caddy/Caddyfile
```bash
{
auto_https disable_redirects
}

pre-billy.devneya.com {
	reverse_proxy localhost:80
}

api.pre-billy.devneya.com {
	reverse_proxy localhost:3000
}
```

followed by `service caddy restart`.


In Docker compose:

```bash
mkdir caddy_data caddy_config
```


## Native

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
vi /etc/caddy/Caddyfile
sudo service caddy start
journalctl -f -u caddy
```


# XCaddy (custom modules)

```bash
sudo snap install go --classic
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/xcaddy/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-xcaddy-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/xcaddy/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-xcaddy.list
sudo apt update
sudo apt install xcaddy
```



# L4 level proxy

Don't know how to log - asked [here](https://github.com/mholt/caddy-l4/issues/246#issuecomment-2453014513).
Interesting configs collection: https://github.com/mholt/caddy-l4/issues/209

Have www.example.com for now.
