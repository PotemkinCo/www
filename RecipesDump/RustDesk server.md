Installation of RustDesk server (as [per](https://rustdesk.com/docs/en/self-host/rustdesk-server-oss/docker/)):

- Network Ports required: TCP 21115-21117, UDP 21116
- A server with 1 CPU, 1 GB and 10 GB disk is plenty to run RustDesk.


## Scripted install

```bash
wget https://raw.githubusercontent.com/dinger1986/rustdeskinstall/master/install.sh
chmod +x install.sh
./install.sh
service gohttpserver restart # as otherwise web server auth won't work
```
Web server only provide download option for two shell scripts (for Linux & Windows) available at `/opt/gohttp/public/`. [MacOS script work in progress](https://github.com/rustdesk/rustdesk-server-pro/issues/32).

## Scripted update
```bash
wget https://raw.githubusercontent.com/techahold/rustdeskinstall/master/update.sh
chmod +x update.sh
./update.sh
crontab -e
```

```crontab
5 1 * * SUN /root/update.sh >> /root/rust_desk_update.log 2>&1

```

## Docker

Not in use.
```bash
wget -O - https://raw.githubusercontent.com/alexander-potemkin/quickies/main/docker_ubuntu.sh | bash
sudo usermod -aG docker `whoami`

```

`vi compose.yml`:
```yaml
services:
  hbbs:
    container_name: hbbs
    ports:
      - 21115:21115
      - 21116:21116
      - 21116:21116/udp
      - 21118:21118
    image: rustdesk/rustdesk-server:latest
    command: hbbs -r rustdesk.example.com:21117
    volumes:
      - ./data:/root
    depends_on:
      - hbbr
    restart: unless-stopped
    labels:
      - "com.centurylinklabs.watchtower.enable=true"

  hbbr:
    container_name: hbbr
    ports:
      - 21117:21117
      - 21119:21119
    image: rustdesk/rustdesk-server:latest
    command: hbbr
    volumes:
      - ./data:/root
    restart: unless-stopped
    labels:
      - "com.centurylinklabs.watchtower.enable=true"

```

Followed by:
```bash
docker compose up -d # without '-d' to debug
```

Here is the key to be used in RustDesk configuration:
```bash
cat ./data/id_ed25519.pub

```

ToDo: not tested; web access is not there.