---
title: "Element Calls"
---

# Installation for Element X

## Install LiveKit

```bash

docker pull livekit/generate
docker run --rm -it -v$PWD:/output livekit/generate
```
-> LiveKit Server Only
Then:
- edit compose file - remove build-on caddy
- configure to use external STUN & TURN servers (as per [config example](https://github.com/livekit/livekit/blob/master/config-sample.yaml#L76)) 
### Setup Caddy

-1. Configure DNS to point to the server

```bash
livekit.example.com {
  reverse_proxy localhost:7880
}
```


## Install JWT

*2025-04-28*

```yaml
services:

    jwt-service:
      image: ghcr.io/element-hq/lk-jwt-service:latest
      container_name: jwt
      restart: unless-stopped
      environment:
        - LIVEKIT_URL=wss://livekit.example.com # goes from livekit generate output
        - LIVEKIT_SECRET=<your-livekit-secret>  # Put in the livekit secret defined within the livekit.yaml
        - LIVEKIT_KEY=<your-livekit-key> # Put in the livekit key defined within the livekit.yaml
        - LIVEKIT_LOCAL_HOMESERVERS=example.com # Set this to your homeserver name
```


```txt
jwt.example.com {
  log
  tls /etc/ssl/example_com.crt /etc/ssl/example_com.key

  reverse_proxy jwt:8080
}
```


## Change server

*2025-04-29*

-0. Add settings to Synapse server: https://github.com/element-hq/element-call/blob/livekit/docs/self-hosting.md#a-matrix-homeserver

Add the following to homeserver.yaml
```yaml
experimental_features:
  # MSC3266: Room summary API. Used for knocking over federation
  msc3266_enabled: true
  # MSC4222 needed for syncv2 state_after. This allow clients to
  # correctly track the state of the room.
  msc4222_enabled: true

# The maximum allowed duration by which sent events can be delayed, as
# per MSC4140.
max_event_delay_duration: 24h

rc_message:
  # This needs to match at least e2ee key sharing frequency plus a bit of headroom
  # Note key sharing events are bursty
  per_second: 0.5
  burst_count: 30

rc_delayed_event_mgmt:
  # This needs to match at least the heart-beat frequency plus a bit of headroom
  # Currently the heart-beat is every 5 seconds which translates into a rate of 0.2s
  per_second: 1
  burst_count: 20
```

-1. Add `.well-known/matrix/client` to Caddy: https://github.com/element-hq/element-call/blob/livekit/docs/self-hosting.md#matrixrtc-backend-announcement
```txt
  @well_known_client {
    path /.well-known/matrix/client
  }
  handle @well_known_client {
    respond `{
                "m.homeserver": {"base_url":"https://matrix.example.com:443"},
                "org.matrix.msc2965.authentication": {
                        "issuer": "https://auth.example.com/",
                        "account": "https://auth.example.com/account"},
                "im.vector.riot.jitsi":
                        {"preferredDomain":"jitsi.example.com"},
                "org.matrix.msc4143.rtc_foci": [
                        {"type": "livekit",
                        "livekit_service_url": "https://jwt.example.com/"},
                        {"type": "livekit",
                        "livekit_service_url": "https://livekit.example.com/"},
                        {"type": "nextgen_new_foci_type",
                        "props_for_nextgen_foci": "val"} ]
            }`
  }
```

# Pre-ready-to-use setup

As of 2024-12-05 updated Readme.md presents a much better docker-compose.yml ([commit](https://github.com/element-hq/element-call/pull/2719/files))
Also - [there is a description](https://github.com/element-hq/element-meta/issues/2371#issuecomment-2468034644) on how to build and use on FreeBSD.

And there is an issue with discussion on it: https://github.com/element-hq/element-meta/issues/2371


Refs:
- [nodejs](https://github.com/nodesource/distributions?tab=readme-ov-file#ubuntu-versions)
- [yarn](https://yarnpkg.com/getting-started/install)
- *2024-02-21*
- *2024-02-22*
- *2024-02-23*
- Lago (billing)


A very useful [issue](https://github.com/element-hq/element-meta/issues/2371#issuecomment-2308785571) with hints and optimizations.
# SW install
```bash

# adding swap (to avoid build time issues with memory)
sudo swapon --show
free --giga -h
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo swapon --show
echo "/swapfile    none    swap    sw    0   0" >> /etc/fstab

# installing docker
wget -O - https://raw.githubusercontent.com/alexander-potemkin/quickies/main/docker_ubuntu.sh | sudo bash
apt-get install docker-compose-plugin

# caddy
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy

# Synapse server
mkdir synapse-server && cd synapse-server
wget https://raw.githubusercontent.com/element-hq/synapse/develop/contrib/docker/docker-compose.yml
vi docker-compose.yml # remove postgresql & traefik labels
docker compose run --rm -e SYNAPSE_SERVER_NAME=synapse.example.com -e SYNAPSE_REPORT_STATS=no synapse generate
# docker compose down --remove-orphans # if missed removing external db earlier
cat >> files/homeserver.yaml << EOT
enable_registration: true
registration_requires_token: false
enable_registration_without_verification: true
allow_guest_access: true
experimental_features:
  msc3266_enabled: true
EOT

# nodejs & yarn
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - &&\
sudo apt-get install -y nodejs
corepack enable
yarn

# matrix-js-sdk
git clone https://github.com/matrix-org/matrix-js-sdk.git
cd matrix-js-sdk
yarn
yarn link

# element call
git clone https://github.com/element-hq/element-call.git
cd element-call
yarn
yarn link matrix-js-sdk
```
# Config

- setup DNS names for web front-end
- setup caddy

`vi /etc/caddy/Caddyfile`:
```txt

# static 
call.example.com {
    file_server
    root * /var/www/
    try_files {path} /{path} /index.html
}

jwt.example.com {
	reverse_proxy localhost:8881
}

synapse.example.com {
	reverse_proxy localhost:8008
}

synapse.example.com:8448 {
        reverse_proxy localhost:8008
}

livekit.example.com {
	reverse_proxy localhost:7880
}
```

`vi /var/www/config.json` ([ConfigOptions.ts](https://github.com/element-hq/element-call/blob/livekit/src/config/ConfigOptions.ts) is considered to be a documentation):
```json
{
  "default_server_config": {
    "m.homeserver": {
      "base_url": "https://synapse.example.com",
      "server_name": "synapse.example.com"
    }
  },
  "livekit": {
	  "livekit_service_url": "https://jwt.example.com"
  },
  "eula": "https://example.com/404"
}
```

Build and place web app:
```bash
mkdir /var/www
cd element-call
yarn build
cp -R dist/* /var/www/
cp -R dist/.* /var/www/
cd /var/www/
cp config.sample.json config.json
vi config.json # take file content from above
service caddy restart
vi backend-docker-compose.yml # adjust LIVEKIT_URL=ws://livekit.example.com:7880
docker compose -f backend-docker-compose.yml up -d
```
# Securing

## Synapse server

Matrix level outside access can be prohibited using the following directives at `homeserver.yaml`:
```yaml
enable_registration: false
registration_requires_token: true
enable_registration_without_verification: true
allow_guest_access: false
experimental_features:
  msc3266_enabled: true
```

Users shall be added with the following command then:
```bash
docker exec -it synapse-server-synapse-1 register_new_matrix_user http://localhost:8008 -c /data/homeserver.yaml --no-admin -u guest -p <guest-password>
```


## LiveKit 
Change (to `pwgen 89`\'s output):
- `LIVEKIT_KEY` & `LIVEKIT_SECRET` at `backend-docker-compose.yaml`
- match them with `keys` at `backend/livekit.yaml` (`LIVEKIT_KEY`:`LIVEKIT_SECRET` format)
- `docker ... down` && `docker up -d` - `restart` doesn't work for some reason.

## Redis

Adjust `ports` section in `backend-docker-compose.yaml` to look like `127.0.0.1:6379:6379` ([ref](https://stackoverflow.com/questions/45109398/how-can-i-make-docker-compose-bind-the-containers-only-on-defined-network-instea))
# ToDo
- process information from [that ticket](https://github.com/element-hq/element-call/issues/2235) and [that ticket](https://github.com/element-hq/element-call/issues/2220) and place on Troubleshooting
- Place as a todo item - domains to direct to the server
Assembling my config variables:
- Synapse server: <server-ip> -> 'synapse.example.com'
- Element call server: <server-ip> -> 'call.example.com'
- LiveKit server: <server-ip> -> 'livekit.example.com'
- JWT server: <server-ip> -> 'jwt.example.com'

# Troubleshooting
- try federation tester against Synapse server
- collect logs from web app as described on [that issue](https://github.com/element-hq/element-call/issues/2235)


# Known limitations
- call.mydomain.com integration in messengers missing - [here is an issue](https://github.com/element-hq/element-desktop/issues/1566).
# Basura (remove after redone)

Synapse server config:
- enable_notifs => false
- registration_shared_secret: "<registration-secret>"
- allow_guest_access: false
- experimental_features:
    msc3266_enabled: true


Installed Synapse server with registration enabled and - before starting to use the server - changed the server name to a full DNS name.
