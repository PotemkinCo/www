---
title: "Multipass"
---

## Multipass

## Install

```bash
apt install snapd
snap install multipass
multipass find
multipass launch 22.04 --cpus 1 --disk 20G --memory 1G --name flying-fish
multipass info flying-fish
```
### Restart instance
```bash
mutlipass delete flying-fish
multipass purge
```
### Transfer file
[ref](https://multipass.run/docs/transfer-command)
```bash
multipass transfer local_file.txt good-prawn:.
```
### Restart
```bash
sudo snap restart multipass.multipassd
```

## Generate hosts
```bash
m list --format=csv | tr -d '"' | cut -d, -f1,6 | awk -F, '{print $2 "\t" $2 "\t" $1}' | grep -v AllIPv4
```
## Additional IP address configuration

Multipass as a cloud: https://www.rootisgod.com/2022/Using-Multipass-Like-a-Personal-Cloud-Service/; guess - it's a [bridge doc](https://multipass.run/docs/configure-static-ips), [Hetzner doc](https://docs.hetzner.com/robot/dedicated-server/ip/additional-ip-adresses/) -> guess I just need to setup config, which doesn't seem to be so much complicated, to be honest.

## Backup & restore

### unix way (filesystem)
(as [per](https://askubuntu.com/questions/1180895/import-export-vms-from-multipass))
```bash
snap stop multipass
tar cf multipass_data.tar /var/snap/multipass/common/data/multipassd/
scp ...
tar xz multipass_data.tar 
snap restart multipass
```

### snapshot -> only inside one server
```bash
multipass snapshot instance
multipass list --snapshots# shall display snapshots as well
multipass restore instance.snapshot2 
multipass delete instance.snapshot1
```

### snap (all instances)
```bash
multipass stop --all
sudo snap save multipass
multipass start --all
sudo snap export-snapshot <set> snap.zip # set - is 'Set' from previous command
sudo snap forget 2
scp to another server
sudo snap install multipass # if it was not yet
sudo snap import-snapshot multipass-snapshot.zip
sudo snap restore 1
multipass list
multipass start --all
```
