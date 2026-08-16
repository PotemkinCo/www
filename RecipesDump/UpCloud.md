# Floating IP
[ref](https://upcloud.com/docs/guides/configure-floating-ip-ubuntu/)

```bash
sudo vi /etc/netplan/99-floating-ip.yaml
network:
    version: 2
    renderer: networkd
    ethernets:
        eth0:
            addresses:
                - $IP/32
sudo netplan try
ip addr
```

# Adding new disk
[ref](https://upcloud.com/resources/tutorials/adding-removing-storage-devices)
```bash
lsblk
fdisk /dev/vdb # n => p => w
lsblk
mkfs.ext4 /dev/vdb1
blkid | grep vdb1 # note UUID
vi /etc/fstab
```

## Disk resize

```bash
# both operations could be performed on-line
growpart /dev/vdb 1
resize2fs /dev/vdb1
```

# Disk migration

  - create new disk with default settings
```bash
apt install rsync
# stop all services -> databases, dockers, etc!
systemctl stop docker docker.socket postgresql mysql nginx
# something else?
lsblk # shows new device as vdb
fdisk /dev/vdb # n (with defaults) => a => p => w (to save) / d (if issues)
lsblk # shows new partition: vdb1
cat /etc/fstab | grep -v "^#" | head -1 # note UUID of root partition
mkfs.ext4 -U `cat /etc/fstab | grep -v "^#" | head -1 | awk -F/ '{print $5}'` /dev/vdb1 
mount /dev/vdb1 /mnt
rsync -avxHAX / /mnt
df -h # to check approximate size equality
grub-install /dev/vdb --root-directory=/mnt --recheck
shutdown -h now
```
- eject old disk
- start the server

# Firewall via cli

[cli app](https://github.com/UpCloudLtd/upcloud-cli)

1. Create special account
2. Make sure your account allows API connections. To do so, log into [UpCloud control panel](https://hub.upcloud.com/login) and go to **Account** -> **Permissions** -> **Allow API connections** checkbox.

```bash
apt install golang-go
go install github.com/UpCloudLtd/upcloud-cli/v3/...@latest
mkdir -p ~/.config
cat > ~/.config/upctl.yaml << EOT
username: your_upcloud_username
password: your_upcloud_password
EOT
vi ~/.config/upctl.yaml
/root/go/bin/upctl server list
```

```bash
	curl -Lo upcloud-cli.deb https://github.com/UpCloudLtd/upcloud-cli/releases/download/v3.11.1/upcloud-cli_3.11.1_amd64.deb
sudo dpkg -i upcloud-cli.deb
mkdir -p ~/.config
		cat > ~/.config/upctl.yaml << EOT
username: your_upcloud_username
password: your_upcloud_password
EOT
vi ~/.config/upctl.yaml
upctl server list
```

Так, вот работающая строка - которая включает или выключает firewall upcloud для текущего сервера:
```bash
#!/bin/bash
SERVER_ID=$(upctl server list 2>&1 | grep `hostname` | awk '{print $1}') && upctl server modify $SERVER_ID --enable-firewall # --disable-firewall
```

Script to renew certs:
```bash
#!/bin/bash
#set -e
set -x

PATH=$PATH:/root/go/bin

date # for the logs

SCRIPTDIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && cd $SCRIPTDIR

#echo "Bringing firewall down"
SERVER_ID=$(upctl server list 2>&1 | grep `hostname` | awk '{print $1}') && upctl server modify $SERVER_ID --disable-firewall

#echo "Starting renewal task"
certbot renew

#echo "Bringing firewall back up"
SERVER_ID=$(upctl server list 2>&1 | grep `hostname` | awk '{print $1}') && upctl server modify $SERVER_ID --enable-firewall
```

crontab:
```
15 2 * * * /root/cert_renew.sh >> /root/cert_renew.log 2>&1
```

And to reboot the server:
```
30 4 * * MON-THU /bin/sh -c '[ -f /var/run/reboot-required ] && sudo shutdown -r now'
```


# Disk clone (SSD to HDD)

````bash
upctl storage clone {storage_uuid} --title {example_standard_clone} --zone {my-zone1} --tier standard
```

I also needed to convert disk from SSD to HDD: `upctl storage clone <storage-uuid> --title \'Standard Disk\' --zone de-fra1 --tier standard --encrypt`