---
title: "CapRover (local kind of Heroku)"
---

# CapRover (local kind of Heroku)


### Prerequisite

- server (Ubuntu LTS) and ssh access
- DNS A type record (to the server's IP)
- e-mail address for HTTPS registration (could be a fake one)
- network ports opened as per [CapRover documentation](https://caprover.com/docs/firewall.html):

```bash
ufw allow 80,443,3000,996,7946,4789,2377/tcp; ufw allow 7946,4789,2377/udp;
```

Only 80 & 443 ports need to be opened to the public internet (as per [ticket](https://github.com/caprover/caprover/issues/990)) + 22 for SSH (or whatever the port is).

### Installing CapRover
*(as per [CapRover](https://caprover.com/docs/get-started.html#step-1-caprover-installation), [NodeJS](https://github.com/nodesource/distributions#debinstall) docs)*

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile    none    swap    sw    0   0" >> /etc/fstab
sudo swapon --show

wget -O - https://raw.githubusercontent.com/alexander-potemkin/quickies/main/docker_ubuntu.sh | bash
# sudo usermod -aG docker `whoami` # only for non-root
sudo snap install node --classic --channel=18
sudo npm install -g caprover # cli
docker run -p 80:80 -p 443:443 -p 3000:3000 -e ACCEPTED_TERMS=true -v /var/run/docker.sock:/var/run/docker.sock -v /captain:/captain caprover/caprover
curl -4 ifconfig.co #note IP address
vi caprover.json
```

caprover.json template below ([doc](https://github.com/caprover/caprover-cli/blob/master/readme.md)):
```json
{
  "caproverIP": "127.0.0.1",
  "caproverPassword": "captain42",
  "caproverRootDomain": "domain_name",
  "newPassword": "",
  "certificateEmail": "your@email.com",
  "caproverName": "captain-01"
}
```

Followed by:
```bash
caprover setup -c caprover.json
```

Interactive (Q&A) setup could be executed via `caprover serversetup` 

Now go to [http://IP_address:3000](http://ip_address:3000) (note HTTP, without `**S`**) port, and proceed with `captain42` as a default password.


## Migrating CapRover
(as per [doc](https://caprover.com/docs/backup-and-restore.html#backup--restore)).

Rollout a new server as per 'Installation process', but **without** last `docker run` command, then run the following commands:
```bash
sftp server-label
mkdir /captain
cp caprover-backup-*.tar /captain/backup.tar
docker run -p 80:80 -p 443:443 -p 3000:3000 -v /var/run/docker.sock:/var/run/docker.sock -v /captain:/captain caprover/caprover
sudo docker ps # compare the output with the initial server
```

> [!NOTE] Good instruction is at *2023-07-09*
> Steps below are moved from there, but not verified / purified.

 
 Install new instance.
 Make a backup and restore from it.


> [!NOTE] Steps below corrupts source system!
> It will fail with 'invalid mount config for type "bind": bind source path does not exist'


 Data backup:
```bash
docker service ls --format {{.Name}} | while read in; do docker service scale "$in"=0; done
docker ps # to verify - no containers are running
docker volume ls
docker volume ls --format {{.Name}} | while read in; do echo "$in:" && docker run -v "$in":/volume --rm --log-driver none loomchild/volume-backup backup -v > ""$in"".tbz2; done
docker service ls --format {{.Name}} | while read in; do docker service scale "$in"=1; done
```

sftp with 'get' to the source and 'put' to the destination, followed by:

```bash
docker service ls --format {{.Name}} | while read in; do docker service scale "$in"=0; done
docker ps

ls *.tbz2 | while read in; do echo "$in => "${in%.tbz2}":" && docker run -i -v ${in%.tbz2}:/volume --rm loomchild/volume-backup restore -v -f < "$in"; done # WARNING: '-f' parameter is in place - override 

docker volume ls

service docker restart # seems to be a more reliable way to restart
# docker service ls --format {{.Name}} | while read in; do docker service scale "$in"=1; done
```

Make DNS change, otherwise nginx & captain dockers are failing; do deploy of the main app.

### DNS configuration

create DNS record like that one:

*.sub-domain A 1H IP address

1. At the Dashboard, link with DNS name: `lhk.domain.name` 
2. After CapRover updates to HTTPS, at Chrome type `thisisunsafe` to ignore invalid SSL certificate.
3. Enable HTTPS
4. Enjoy!

### Logs monitoring

Install Dozzle from one click apps, as per this advice: https://github.com/caprover/caprover/issues/1140

# Local registry setup

Cluster -> Setup 
```bash
caprover ls
# make sure you're logged in to your instance. It should be in the list.

caprover api
# select your server
# for path, use /user/registries
# for method, use "GET"
# for API data JSON string, leave it empty.
# the output is like this:
{
  "registries": [
    {
      "id": "abcd-abcd-abcd-abcd-abcd",
      "registryDomain": "registry.root.domain.com:996",
      "registryImagePrefix": "captain",
      "registryUser": "captain",
      "registryPassword": "abcd-abcd-abcd-abcd-abcd",
      "registryType": "LOCAL_REG"
    }
  ],
  "defaultPushRegistryId": ""
}
```

### GitHub Deployment keys

 `ssh-keygen -m PEM -t rsa -b 4096 -C projectname` , enter `./id_rsa` and get the keys.

`cat id_rsa` and send that to CapRover's Deployment page

 `cat id_rsa.pub` and deliver that key to GitHub's Deployment Key (under settings of repository) 

### Automatic updates with the source code

Gather webhook URL from CapRover settings.

GitHub → Repository → Settings → Webhooks →add it there,  

### SSL certificate update

```bash
#!/bin/bash
set -e

echo "Bringing firewall down"
/root/firewall_down.sh

echo "Starting renewal task"
docker exec `sudo docker ps --filter name=certbot -q` /usr/local/bin/certbot renew # -it for interactive mode

echo "Giving it time to work things out (60 seconds sleep)"
sleep 60

echo "Bringing firewall back up"
/root/firewall_up.sh
```

### One-click app update

[https://github.com/caprover/caprover/issues/1008](https://github.com/caprover/caprover/issues/1008)


### Troubleshooting CapRover

**Cleaning up cache** 

**Don't do that, unless absolutely required. Can have unexpected side effects.**

as per [GitHub issue](https://github.com/caprover/caprover/issues/1135)

```bash
docker builder prune --all
```

[https://caprover.com/docs/troubleshooting.html](https://caprover.com/docs/troubleshooting.html)

CapRover logs

```bash
docker service logs captain-captain --since 60m --follow
```

From the server

```bash
sudo docker exec -it `sudo docker ps --filter name=srv-captain -q` /bin/sh
```

Password reset

```bash
sudo su -
apt install jq
docker service scale captain-captain=0
cp /captain/data/config-captain.json /captain/data/config-captain.json.backup
jq 'del(.hashedPassword)' /captain/data/config-captain.json > /captain/data/config-captain.json.new
cat /captain/data/config-captain.json.new > /captain/data/config-captain.json
rm /captain/data/config-captain.json.new
# set a temporary password
docker service update --env-add DEFAULT_PASSWORD=captain42 captain-captain
docker service scale captain-captain=1
```

### Restart CapRover

```bash
docker service update captain-captain --force
```

### Removing CapRover

```bash
docker service rm $(docker service ls -q)
## remove CapRover settings directory
rm -rf /captain
## leave swarm if you don't want it
docker swarm leave --force
## full cleanup of docker
docker system prune --all --force
```


# Notes

I considered Coolify, didn't it didn't work well - more details at *2023-10-20*, but on a high level - the features doesn't work as I expected them to work, original installation was not working, MongoDB never started, as I expected.

<aside>
❗ If the app is not adapted to Heroku or was not adapted to CapRover earlier, a *captain_definition* file has to be added, as it's the one that lets CapRover knows which stack it's launching, examples [available](https://github.com/caprover/caprover/tree/master/captain-sample-apps).

</aside>
