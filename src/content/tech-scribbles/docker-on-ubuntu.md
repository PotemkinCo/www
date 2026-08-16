---
title: "Docker (on Ubuntu)"
---

No Kubernetes: docker compose + haproxy - https://statusdude.com/blog/zero-downtime-docker-compose

# Watchtower replacement - dockcheck

https://github.com/mag37/dockcheck

```bash
mkdir -p ~/.local/bin
wget -O ~/.local/bin/dockcheck.sh "https://raw.githubusercontent.com/mag37/dockcheck/main/dockcheck.sh" && chmod +x ~/.local/bin/dockcheck.sh
```

## Get IPs for each Docker

```bash
docker ps -q | xargs -n1 docker inspect --format '{{.Name}} {{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' | sed 's#^/##'
```

# Lazydocker

```bash
curl https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash
echo 'PATH=$PATH:~/.local/bin' >> ~/.bashrc
```

# Move docker to another disk / path

```bash
systemctl stop docker docker.socket
rsync -avxHAX /var/lib/docker /mnt/new
mv /var/lib/docker /var/lib/docker.backup
echo '{ "data-root": "/mnt/new/docker" }' >> /etc/docker/daemon.json
vi /etc/docker/daemon.json
systemctl start docker
```


# Docker one-liner

```bash
wget -O - https://get.docker.com | sudo bash
```

# Rootless Docker

Create non-root user (if doesn't exist):
```bash
NEWUSER='ubuntu'
sudo adduser $NEWUSER
sudo usermod -aG sudo $NEWUSER #add user to sudo group, to enable passwordless sudo
echo '%sudo ALL=(ALL) NOPASSWD: ALL' | sudo tee /etc/sudoers.d/sudo_nopasswd > /dev/null
sudo vi /etc/shadow # place `*` on the password field to prevent password login
rsync --archive --chown=$NEWUSER:$NEWUSER ~/.ssh /home/$NEWUSER #copy SSH keys
```

```bash
sudo apt-get install -y dbus-user-session uidmap slirp4netns && exit
# after re-login:
sudo apt-mark hold slirp4netns

wget -O - https://get.docker.com | sudo bash

sudo systemctl disable --now docker.service docker.socket
sudo rm /var/run/docker.sock
dockerd-rootless-setuptool.sh install

sudo loginctl enable-linger `id -nu`
sudo setcap cap_net_bind_service=ep $(which rootlesskit)
systemctl --user restart docker

sudo bash -c "echo 'net.ipv4.ip_unprivileged_port_start=0' > /etc/sysctl.d/20-any_port_for_anyone.conf"
sudo sysctl --system
sudo sysctl net.ipv4.ip_unprivileged_port_start # shall be 0

sudo tee -a ~/.bashrc >> /dev/null << 'EOF'
export PATH=/usr/bin:$PATH
export DOCKER_HOST=unix:///run/user/1000/docker.sock
EOF
```

**Using pasta on rootless docker:**
```bash
sudo apt remove slirp4netns
sudo apt install passt
systemctl --user set-environment PATH=/usr/bin:/usr/local/bin:$PATH

mkdir -p ~/.config/systemd/user/docker.service.d
cat > ~/.config/systemd/user/docker.service.d/override.conf <<'EOF'
[Service]
Environment="DOCKERD_ROOTLESS_ROOTLESSKIT_NET=pasta"
Environment="DOCKERD_ROOTLESS_ROOTLESSKIT_PORT_DRIVER=implicit"
EOF

systemctl --user daemon-reload
systemctl --user restart docker
```

**root docker (with firewalls):** 
```bash
// /etc/docker/daemon.json
{
  "firewall-backend": "nftables"
}
```

### Disable localhost isolation

In rootless mode, localhost is isolated (fuck you, Docker developers).
Related links:
- https://docs.docker.com/engine/release-notes/26.0/
- https://github.com/moby/moby/pull/47352
- 
```bash
[Service]
Environment="DOCKERD_ROOTLESS_ROOTLESSKIT_DISABLE_HOST_LOOPBACK=false"
```
that goes to `vi ~/.config/systemd/user/docker.service.d/override.conf`


### Uninstall
```bash
dockerd-rootless-setuptool.sh uninstall
sudo systemctl enable --now docker.service docker.socket
sudo systemctl start --now docker.service docker.socket
```
# Docker (on Ubuntu)

```bash
wget -O - https://get.docker.com | sudo bash
```


**Installation one liner**

```bash
wget -O - https://raw.githubusercontent.com/alexander-potemkin/quickies/main/docker_ubuntu.sh | bash
sudo apt-get install docker-compose-plugin
sudo usermod -aG docker `whoami`
```

### Uninstall from Ubuntu
[ref](https://docs.docker.com/engine/install/ubuntu/#uninstall-docker-engine)
```bash
sudo apt-get purge docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin docker-ce-rootless-extras
sudo rm -rf /var/lib/docker
sudo rm -rf /var/lib/containerd
```

## Cleanup space
```bash
# VERIFY BACKUPS ARE IN PLACE FIRST!
docker system prune -a
docker volume rm $(docker volume ls -qf dangling=true)
```
## Migrate volume

https://stackoverflow.com/questions/21597463/how-to-port-data-only-volumes-from-one-host-to-another

### Various docker commands

ToDo:
- Try https://github.com/jesseduffield/lazydocker


Run anything in one line

```bash
docker run -d --restart=unless-stopped --name='tinyproxy' -p 6666:8888 dannydirect/tinyproxy:latest ANY
```


### make container always running (restart)

as per [StackOverflow](https://stackoverflow.com/questions/26852321/docker-add-a-restart-policy-to-a-container-that-was-already-created)

```bash
docker update --restart=always container_name
```

### Docker

Connect to the Docker instance
```bash
sudo docker exec -it `sudo docker ps --filter name=certbot -q` /bin/sh
```

Stop all Docker containers
```bash
docker ps --format "{{.Names}}" | sort | xargs --verbose --max-args=1 -- docker stop
```

Remove all Docker containers:
```bash
docker ps --format "{{.Names}}" -a | sort | xargs --verbose --max-args=1 -- docker rm
```

Clear Docker build cache

```bash
sudo docker builder prune --all
```

Get resources map for the Dockers

```bash
sudo docker stats --all
```

See the logs
```bash
watch 'docker ps --format "{{.Names}}" | sort | xargs --verbose --max-args=1 -- docker logs --tail=8 --timestamps'
```
