# Linux => FreeBSD install (depenguin.me)

Boot into rescue system:

```bash
# prepare
lspci  | grep -i net # check if NIC made is Intel 82575/82576/82580/i210/i211/i35x - they are served by igb, not em
lsblk -e 1,7,43 -d -o NAME,SIZE,MODEL,ROTA,TRAN # to see the disks type - NVME/SSD normally

ssh-keygen -t ed25519 -C "my-key"
wget https://depenguin.me/run.sh && chmod +x run.sh
./run.sh -d /root/.ssh/id_ed25519.pub
ssh -p 1022 mfsbsd@127.0.0.1

sudo su -
geom disk list | wc -l # verify the disks are recognized
./mfsbsd_clean.sh zroot ada0 ada1 # cleanup disks - after every bsdinstall
pkg bootstrap -f # for FreeBSD 15.0
# Hetzner: manual network configuration might be required, netmask could be in "human" form
# OVHCloud: leave it to DHCP
bsdinstall #check below for the hints
```
Installation configs:
	- add 'optional' package
	- accept all proposed security features 
	- create non root user and do not enable encryption on a newly added user, or ssh won't work

After the installation is done - leave installer and do:
	- open the shell at the end check `/etc/fstab` &  for disks and interfaces names
		- `vi /etc/rc.conf` for Intel 82575/82576/82580/i210/i211/i35x replace `ifconfig_em0` with `ifconfig_igb0`
		- `vi /etc/fstab`: for NVMe replace `a` with `n` => `/dev/ada0p3.eli` with `/dev/nda0p3.eli`

Once everything is in place - do `shutdown -h now` on FreeBSD and
	- `shutdown -r now` on host Linux for Hetzner
	- `shutdown -h now` for OVHcloud- followed by changing back to the boot disk, instead of rescue (Hetzner does that automatically upon reboot).
	
After a few minutes, ssh to FreeBSD now.
## After reboot

```bash
su -
pkg install -y bash sudo curl htop sysutils/py-glances smartmontools arpwatch pftop nmap monit  vim
chsh -s /usr/local/bin/bash $(tail -1 /etc/passwd | cut -d: -f1) # change shell to bash
visudo # uncomment `%wheel ALL=(ALL:ALL) NOPASSWD: ALL`
exit

printf 'syntax on\ncolorscheme default\n' >> ~/.vimrc # add colors
mkdir .ssh
vi ~/.ssh/authorized_keys
sudo vi /etc/ssh/sshd_config # `PasswordAuthentication` => `no`, `Port` => ...
sudo service sshd restart
# try ssh connection from another console

sudo zpool status zroot # to check mirror status
sudo pkg update # for FreeBSD >= 15
# sudo freebsd-update fetch && sudo freebsd-update install # for FreeBSD < 15
sudo netstat -an4 && sudo sockstat -l4 # to check ports opened 
sudo vipw # remove passwords for the root and user
```

Your server is good to go.

## Some typical configs

`/etc/rc.conf`
```bash
clear_tmp_enable="YES"
syslogd_flags="-b localhost -C"
sshd_enable="YES"
ntpd_enable="YES"
ntpd_sync_on_start="YES"
moused_nondefault_enable="NO"
dumpdev="AUTO"

zfs_enable="YES"
vm_enable="YES"
vm_dir="zfs:zroot/vm"
vm_list=""

gateway_enable="YES"

pf_enable="YES"
pflog_enable="YES"
pflog_logfile="/var/log/pflog"

monit_enable="YES"
haproxy_enable="YES"
smartd_enable="YES"
```

`/etc/pf.conf`
```bash
# pfctl -nf /etc/pf.conf
# sudo pfctl -vnf /etc/pf.conf # test rules
# sudo pfctl -F all -f /etc/pf.conf # reload all rules
# sudo pfctl -s [ rules | nat | states ] # show rules / nat / states
# sudo pfctl -t users_vpns -T show # show IPs in the table
# https://chatgpt.com/c/690d074a-1c0c-8329-8ee7-8b9db8df4595

ext_if = "igb0"
vm_public = "vm-public"

internal_net = "192.168.8.0/24"

# Tables (fast ip set lookup)
# <vpn_ip1> - vpn wireguard
# <vpn_ip2> - cloaked openvpn
# <vpn_ip3> - access server
# <vpn_ip4> - cloud server
table <users_vpns> { 198.51.100.1, 198.51.100.2, 198.51.100.3, 198.51.100.4 }
# <other_ip1> - synapse host
# <other_ip2> - app host
table <other_servers> { 198.51.100.10, 198.51.100.11 }

# Ports forwarding
rdr on $ext_if proto { tcp udp } to ($ext_if) port 20339 -> 192.168.8.12 port 20339 # RDP
rdr on $ext_if proto tcp to ($ext_if) port { 25, 465, 587, 993, 4190 } -> 192.168.8.15 # Web services / mail
# NAT
nat on $ext_if from $internal_net to any -> ($ext_if)

# Quick optimization for local loopback
set skip on lo0

# Allow everything on vm-public (as in original)
pass quick on $vm_public all

# Default outbound allow on public interface (stateful)
pass out quick on $ext_if keep state

# Inbound allow rules on public interface
pass in log quick on $ext_if proto tcp to any port 38610 keep state # SSH
pass in log quick on $ext_if proto tcp to any port 25 keep state # SMTP

pass in log quick on $ext_if proto { tcp udp } from { <users_vpns>, <other_servers> } to any port 443 keep state # HTTPS

pass in log quick on $ext_if proto tcp from <users_vpns> to any port 20339 keep state # RDP
# pass in log quick on $ext_if proto tcp from <users_vpns> to any port 5900 keep state # VNC

pass in log quick on $ext_if proto tcp from <users_vpns> to any port { 465, 587, 993, 4190 } keep state # MTU & Sieve ports

# Default deny inbound on public interface (log)
block in log quick on $ext_if
```

### Tune-ups
```bash
echo 'vfs.zfs.arc_max="4G"' | sudo tee -a /boot/loader.conf > /dev/null # to limit ARC to 4Gb
```

# Secure level

for securelevel > 0 to work with vmbhyve & jails / docker add the following to `/boot/loader.conf`
```
vmm_load="YES"
nmdm_load="YES"
if_tap_load="YES"
if_bridge_load="YES"
nullfs_load="YES"
```

and, to `/etc/rc.conf`
```
kern_securelevel_enable="YES"
kern_securelevel=2
```

### smartd (disks check) with securelevel > 1

modify `/usr/local/etc/rc.d/smartd`:
```
# PROVIDE: smartd
# REQUIRE: FILESYSTEMS
# BEFORE: netif NETWORKING DAEMON LOGIN securelevel
# KEYWORD: shutdown nojail
```

# OS updates / upgrades

```bash
sudo freebsd-update -r 14.4-RELEASE upgrade
sudo freebsd-update install
sudo shutdown -r now
sudo freebsd-update install
sudo pkg-static install -f pkg
sudo pkg upgrade # -f flag, if major update / versions mismatch
sudo freebsd-update fetch
sudo freebsd-update install
sudo shutdown -r now
```

# Jails

## setup

```bash
sudo pkg install -y bastille
sudo sysrc bastille_enable="YES"
sudo sysrc bastille_list=""
sudo sysrc bastille_rcorder="YES"

sudo bastille bootstrap 15.0-RELEASE update
sudo sysrc -f /usr/local/etc/bastille/bastille.conf bastille_zfs_enable="YES"
sudo sysrc -f /usr/local/etc/bastille/bastille.conf bastille_zfs_zpool="tank"

sudo sysrc cloned_interfaces+="lo1" # got to clone via lo to configure the driver
sudo sysrc ifconfig_lo1_name="bastille0"
sudo service netif cloneup

sudo vi /etc/pf.conf
```

### firewall

`table <jails> persist` -> at the very top, with all other macroses
`rdr-anchor "rdr/*"` -> before filtering (block/pass) rules, could be after table, `rdr` if hard-coded in bastille
`nat on $ext_if inet from <jails> to any -> ($ext_if)` -> in NAT section
`set skip on lo` -> pass traffic via loopback, replace an existing, as it skip on all loopback interfaces

## acme-dns in jail

```bash
# create jail -- why .0.5?
sudo bastille create acmedns 15.0-RELEASE 10.0.0.5
# sudo bastille create -V acmedns 15.0-RELEASE 10.0.0.5 vnet0 # for a separate vnet network, if required

# ports forwarding
sudo bastille rdr acmedns udp 53 53
sudo bastille rdr acmedns tcp 53 53

# hardening
sudo bastille config acmedns set allow.raw_sockets 0
sudo bastille config acmedns set allow.sysvipc 0
sudo bastille config acmedns set enforce_statfs 2
sudo bastille config acmedns set devfs_ruleset 4

sudo bastille pkg acmedns install dns/acme-dns
sudo bastille cmd acmedns pw useradd acmedns -d /var/db/acme-dns -s /usr/sbin/nologin
sudo bastille cmd acmedns mkdir -p /var/db/acme-dns
sudo bastille cmd acmedns chown acmedns:acmedns /var/db/acme-dns

sudo bastille cmd acmedns vi /usr/local/etc/acme-dns/config.cfg # the config is below

sudo bastille sysrc acmedns acme_dns_enable="YES"
sudo bastille service acmedns acme_dns start

sudo bastille edit acmedns # if any settings needs to be edited
sudo bastille cmd acmedns service acme_dns status
sudo bastille cmd acmedns tail -f /var/log/messages # to check the jail logs
sudo bastille cmd acmedns tail -f /var/log/acme-dns.log # to check the service logs
```

the acme-dns's config file:

```bash
$ sudo bastille cmd acmedns cat /usr/local/etc/acme-dns/config.cfg

[acmedns]:
[general]
listen = "0.0.0.0:53"
protocol = "both"
# The domain acme-dns is authoritative for
domain = "auth.acme-dns.example.com"
# The name of the nameserver itself
nsname = "auth.acme-dns.example.com"
# The admin email (formatted as a domain)
nsadmin = "devnull.auth.acme-dns.example.com"
# These records allow the acme-dns server to resolve its own identity
records = [
    "auth.acme-dns.example.com. A <acmedns-ip>",
    "auth.acme-dns.example.com. NS auth.acme-dns.example.com.",
]
debug = false

[database]
engine = "sqlite3"
connection = "/var/db/acme-dns/acme-dns.db"

[api]
# Listen on all local interfaces for the Docker bridge
ip = "0.0.0.0"
port = "8080"
tls = "none"
# Change this to 'true' AFTER you have registered your domain via the API
disable_registration = true
corsorigins = [
    "*"
]
use_header = true
header_name = "X-Forwarded-For"

[logconfig]
loglevel = "debug"
logtype = "syslog" 
# logtype = "stdout" is only good for docker
logformat = "text"
```

## garage-s3 in jail
(migration from docker)
```bash
sudo bastille create s3garage 15.0-RELEASE 10.0.0.6 bastille0

sudo bastille config s3garage set allow.raw_sockets 0
sudo bastille config s3garage set allow.sysvipc 0
sudo bastille config s3garage set allow.mount 0
sudo bastille config s3garage set enforce_statfs 2
sudo bastille config s3garage set securelevel 3

sudo bastille pkg s3garage install garage
sudo bastille mount s3garage /tank/s3-garage/data var/db/garage/data nullfs rw 0 0
sudo bastille mount s3garage /zroot/tank-cache/s3-garage-meta var/db/garage/meta nullfs rw 0 0

sudo bastille cmd s3garage chown -R garage:garage /var/db/garage
sudo bastille cmd s3garage chmod -R 750 /var/db/garage

sudo bastille cmd s3garage vi /usr/local/etc/garage.toml # the config is below

sudo bastille sysrc s3garage garage_enable=YES
sudo bastille restart s3garage

sudo bastille cmd s3garage service garage status
sudo bastille cmd s3garage garage status
sudo bastille cmd s3garage tail -f /var/log/messages 
sudo bastille cmd s3garage tail -f /var/log/garage.log

sudo bastille sysrc s3garage garage_env="RUST_LOG=garage=debug" # for debug

```

how to **update/install garage from the ports** (*not tested*):
```bash
sudo bastille cmd s3garage sh -c "cd /usr/ports/www/garage && make install clean"
sudo bastille cmd s3garage garage --version
```

the actual garage config:

```bash
metadata_dir = "/var/db/garage/meta"
data_dir = "/var/db/garage/data"
metadata_snapshots_dir = "/var/db/garage/data/snapshots"

db_engine = "sqlite"
metadata_auto_snapshot_interval = "2h"
metadata_fsync = true

replication_factor = 1

compression_level = 5
block_size = 8388608

rpc_bind_addr = "127.0.0.1:3901"
rpc_public_addr = "127.0.0.1:3901"
rpc_secret = "<generated-rpc-secret>"

block_max_concurrent_reads = 8
block_max_concurrent_writes_per_request = 3

[s3_api]
s3_region = "garage"
api_bind_addr = "0.0.0.0:3900"
root_domain = ".s3.garage"

[admin]
api_bind_addr = "127.0.0.1:3903"
```

## updates

```bash
sudo bastille update acmedns
sudo bastille pkg acmedns update
sudo bastille pkg acmedns upgrade -y
```

**automatic updates**: `echo "0 3 * * * root bastille update acmedns && bastille pkg acmedns upgrade -y" >> /etc/crontab`

## snapshots (before updates)

```bash
bastille snapshot acmedns pre-update
bastille update acmedns
# if something breaks:
bastille rollback acmedns pre-update
```


# VM (bhyve)

Ref:
- https://github.com/freebsd/vm-bhyve
- https://github.com/freebsd/vm-bhyve/wiki/Running-Windows

## Setup
```bash
sudo pkg install -y vm-bhyve dnsmasq qemu-tools bhyve-firmware cdrkit-genisoimage grub2-bhyve # the last three - is for cloud-init & Ubuntu images

# give VMs more time to shutdown
sudo sysrc rcshutdown_timeout=600
echo "kern.init_shutdown_timeout=600" | sudo tee -a /etc/sysctl.conf && sudo sysctl kern.init_shutdown_timeout=600

# optimal settings for NVMe with VMs as images
ZFS_PART='zroot/vm'
sudo zfs create $ZFS_PART
sudo zfs set recordsize=64K $ZFS_PART
sudo zfs set compression=zstd $ZFS_PART
sudo zfs set atime=off $ZFS_PART
sudo zfs set primarycache=metadata $ZFS_PART

sudo sysrc vm_enable="YES"
sudo sysrc vm_dir="zfs:${ZFS_PART}"
ssh-keygen -t ed25519 # the key used to ssh into Linux created images (if `-f key_name` is used - it will have to be provided for every ssh into the vm)
sudo vm init
sudo cp /usr/local/share/examples/vm-bhyve/* /${ZFS_PART}/.templates/
sudo vm img https://cloud-images.ubuntu.com/releases/jammy/release/ubuntu-22.04-server-cloudimg-amd64.img # latest Ubuntu image
sudo vm switch create -a 192.168.10.1/24 public
sudo vm switch vlan public 0
sudo vm switch add public igb0
```

## 2-FA on SSH

- adding 2FA for SSHD on FreeBSD:
```bash

sudo pkg install pam_google_authenticator

google-authenticator # accept all

# 1. Add `AuthenticationMethods publickey,keyboard-interactive` to /etc/ssh/sshd_config

grep -E 'KbdInteractiveAuthentication|UsePAM|PasswordAuthentication' /etc/ssh/sshd_config # to check they are yes/yes/no / default

# change auth line in /etc/pam.d/sshd to be

$ grep auth /etc/pam.d/sshd | grep -v "^#"
auth            required        /usr/local/lib/pam_google_authenticator.so

sudo service sshd restart

# verify it's all working from another session

```
## Create VM
### Ubuntu (grub)

**Inside ZVOL**
```bash
sudo vm create -c 1 -m 1G -s 20G -t linux-zvol -i ubuntu-22.04-server-cloudimg-amd64.img -C -n "ip=192.168.8.10/24;gateway=192.168.8.1;nameservers=1.1.1.1,8.8.8.8" -k ~/.ssh/id_ed25519.pub dear-ubuntu-server
```

**As a RAW file image (faster on NVMe, works with GELI)**
```bash
sudo vm create -c 2 -m 2G -s 20G -t linux-grub -i ubuntu-22.04-server-cloudimg-amd64.img -C -n "ip=192.168.8.3/24;gateway=192.168.8.1;nameservers=1.1.1.1" -k ~/.ssh/id_ed25519.pub dear-ubuntu-server
```

Followed by:
```
sudo vm start dear-ubuntu-server
sudo vm info dear-ubuntu-server
ssh ubuntu@192.168.8.10 # note - ubuntu user here, not root
```

Make sure it autostart via `rc.conf`: `vm_list="ubuntu vm1 vm2 ..."`

### Windows

Upload Windows ISO file, then:
```bash
sudo vm iso Windows-2022-std_ru.iso # inject the image into the 
sudo vm create -m 12G -t windows win-server-2022
sudo vm install win-server-2022 Windows-2022-std_ru.iso # '-f' option if needs to be started in foreground 
sudo vm list # shows VNC connection
```

**To enable VNC**: `graphics` => `yes`


## Public IPv6 for a VM configuration

DO not create public switch (or remove it `sudo vm switch remove public igb0`)
```bash
# Assign the IPv4 gateway to the switch (vm-bhyve remembers this)
sudo vm switch address public 192.168.10.1/24

# Assign the IPv6 gateway (apply immediately)
sudo ifconfig vm-public inet6 2001:db8::1 prefixlen 64 alias

# Add this to the /etc/rc.conf; or to your VM start script, if it is all managed manually
echo 'ifconfig_vm_public_ipv6="inet6 2001:db8::1 prefixlen 64 alias"' | sudo tee -a /etc/rc.conf

# Enable gateway
sudo sysrc gateway_enable="YES"
sudo sysrc ipv6_gateway_enable="YES"

sudo sysctl net.inet.ip.forwarding=1
sudo sysctl net.inet6.ip6.forwarding=1

sudo vm create -c 1 -m 1G -s 20G -t linux-zvol -i ubuntu-22.04-server-cloudimg-amd64.img -C -k ~/.ssh/server-key.pub saas-server-vm1

grep 'mac=' /tank/vms/saas-server-vm1/saas-server-vm1.conf # get MAC address

sudo vm edit saas-server-vm1 network-config

# OR

cat << 'EOF' | sudo tee /tank/vms/saas-server-vm1/.cloud-init/network-config > /dev/null
network:
  version: 2
  ethernets:
    id0:
      set-name: eth0
      match:
        macaddress: "58:9c:fc:0c:37:9f"
      addresses:
        - 192.168.10.2/24
        - "2a01:4f9:3a:1ee7:ffff:ffff:ffff:fffe/64"
      routes:
        - to: 0.0.0.0/0
          via: 192.168.10.1
        - to: "::/0"
          via: "2001:db8::1"
      nameservers:
        addresses:
          - 1.1.1.1
          - 8.8.8.8
EOF

# run hostnames to IP script

ssh ubuntu@saas-server-vm1 
```
## Changing configuration

```bash
sudo vm stop $vmname
sudo vm configure $vmname
```

### For the network change (cloud-init)

```bash
sudo vm edit vm_name network-config
sudo vm edit vm_name meta-data # change / increment it

sudo vm poweroff saas-server-vm1
sudo rm /.../seed.iso
sudo vm start vm_name
```

### For disk resize, if it's a zvol:
```bash
sudo zfs list -t volume # to find appropriate
sudo zfs get volsize $volume # to see current size
sudo zfs set volsize=40G $volume # to set a new size
```

### if it's a file:

```bash
sudo truncate -s +15G vm.disk
```

## Over-provisioning resources

Add that to the VM's configuration file
```bash
wired_memory="no"
```

!Important! Make sure to limit ZFS's ARC memory (`vfs.zfs.arc_max`) and limit ZFS cache to metadata only.
## Notes

```bash
sudo vm switch destroy public # destroys the bridge, non-disruptive for the ssh
ls /zroot/vm/.config # vm's config files
```
# Jails


# HAProxy proxying
great [ref](https://www.server-world.info/en/note?os=FreeBSD_14&p=haproxy&f=1)

```bash
sudo pkg install haproxy
sudo pw useradd haproxy -u 200 -d /var/empty -s /usr/sbin/nologin

sudo tee -a /etc/syslog.d/local1.conf >> /dev/null << 'EOF'
local1.*                                                /var/log/haproxy.log
EOF
sudo tee -a /usr/local/etc/newsyslog.conf.d/haproxy.conf >> /dev/null << 'EOF'
/var/log/haproxy.log root:wheel 640 30 * @T00 JC
EOF

sudo sysrc syslogd_flags="-b localhost -C"
sudo touch /var/log/haproxy.log && sudo chown haproxy:haproxy /var/log/haproxy.log

sudo vim /usr/local/etc/haproxy.conf
sudo haproxy -c -f /usr/local/etc/haproxy.conf

sudo service haproxy enable
sudo service haproxy start
```

Starter haproxy configuration file:

```
global
    log 127.0.0.1:514 local1 debug

	# TLS tunning
    ssl-default-bind-options ssl-min-ver TLSv1.3
    tune.ssl.default-dh-param 4096
    tune.ssl.cachesize 2500 # number of entries, 5'000 is a default
    tune.ssl.lifetime 60 # expiration for TLS1.3, in seconds
	stats socket /var/run/haproxy/admin.sock mode 660 level admin group acme

    chroot      /var/empty
    pidfile     /var/run/haproxy.pid
    stats socket /var/run/haproxy.sock mode 600 level admin expose-fd listeners
    maxconn     4000
    user        haproxy
    group       haproxy
    daemon


defaults
    log                     global
    #timeout tunnel 1h # for web-socket to work
    option http-server-close
    retries                 3
    timeout http-request    10s
    timeout queue           1m
    timeout connect         10s
    timeout client          1m
    timeout server          1m
    timeout http-keep-alive 10s
    timeout check           10s
    maxconn                 3000

frontend ingres
    bind :443 ssl crt /usr/local/etc/haproxy/certs/
    mode http

    option httplog
    http-request capture req.hdr(Host) len 100
    log-format "%ci:%cp %hr %hs => %b HTTP %ST: %B bytes in %Tr ms"

    #http-response set-header Cache-Control "no-cache, no-store, must-revalidate"
    #http-response set-header Pragma "no-cache"
    #http-response set-header Expires "0"
    
    # multiple sub-domains via reg-exp
    use_backend one_vm if    { hdr(host) -m reg -i ^(sub-domain1|sub-domain2)\.domain\.com$ }
    # multiple sub-domains via reg-exp + bare domain
	use_backend second_vm if { hdr(host) -m reg -i ^((sub-domain1|sub-domain2)\.)?domain\.com$ }
	# single sub-domain only
	use_backend one_sub_endpoint if { hdr(host) -i one-sub.domain.com }

    default_backend null_backend

# null
backend null_backend
    mode http
    http-request return status 501 content-type "text/plain" lf-string "Nah."

# a very specific cloudron setup - re-encrypt and only use http/1.1
backend cloudron_vm
    mode http
    server local_cloudron cloudron_backend:443 ssl verify none sni req.hdr(Host) alpn http/1.1

backend s3_garage
    server garage 127.0.0.1:3900 check
```

## SSL certificates

### Wildcard via acme-dns

Place in haproxy's **global** section:

```
stats socket /var/run/haproxy/admin.sock mode 660 level admin group acme
```

Create necessary directories:
```bash
sudo mkdir -p /usr/local/etc/haproxy/certs
sudo chown acme:haproxy /usr/local/etc/haproxy/certs
sudo chmod 750 /usr/local/etc/haproxy/certs

sudo mkdir -p /var/run/haproxy
sudo chown haproxy:haproxy /var/run/haproxy

# to preserve the folder after the reboot
sudo sysrc haproxy_precmd="mkdir -p /var/run/haproxy && chown haproxy:haproxy /var/run/haproxy"

(sudo crontab -u acme -l 2>/dev/null; echo '25 2 * * * /usr/local/sbin/acme.sh --cron --home "/var/db/acme/.acme.sh" > /dev/null') | sudo crontab -u acme - && sudo crontab -u acme -l 2>/dev/null
```

Now, on the client side:

```bash
# Create DNS records on dns.example.com:
# NS: auth.acme-dns.agent => auth.acme-dns.example.com.
# A: auth.acme-dns.agent => <acmedns-ip>
sudo pkg install acme.sh jq
sudo su - acme -c bash

export TARGET_DOMAIN=\'example.com\'

curl -X POST "https://auth.acme-dns.example.com/register" \
	 -H "Content-Type: application/json" \
	 -d '{"allowfrom": []}' | tee uden_response.json
	 
eval "$(jq -r '
  "export ACMEDNS_BASE_URL=https://auth.acme-dns.example.com",
  @sh "export ACMEDNS_USERNAME=\(.username)",
  @sh "export ACMEDNS_PASSWORD=\(.password)",
  @sh "export ACMEDNS_SUBDOMAIN=\(.subdomain)",
  @sh "export ACMEDNS_FULLDOMAIN=\(.fulldomain)"
' uden_response.json)"

echo "Create CNAME: _acme-challenge => $ACMEDNS_FULLDOMAIN" 
	 
acme.sh --set-default-ca --server letsencrypt # to avoid providing e-mails
env | grep ACMEDNS_
acme.sh --issue -d "*.${TARGET_DOMAIN}" -d "$TARGET_DOMAIN" --dns dns_acmedns


# Configuration for haproxy

export DEPLOY_HAPROXY_HOT_UPDATE=yes
export DEPLOY_HAPROXY_STATS_SOCKET=/var/run/haproxy/admin.sock
export DEPLOY_HAPROXY_PEM_PATH=/usr/local/etc/haproxy/certs

# VERIFY HAPROXY IS RUNNING - otherwise a socket error will appear

acme.sh --deploy -d "*.${TARGET_DOMAIN}" --deploy-hook haproxy
```

### Placing already existing / purchased one 

```bash
sudo mkdir /usr/local/etc/ssl
sudo cp domain_co.crt domain_co.crt.key /usr/local/etc/ssl/ # KEY file shall be $certname.key
```

# Disks operations

## Optimizations: trim


> [!NOTE] Better for HW, worse for security
> That enables TRIM (for longevity), BUT reveals which blocks are free


```bash
sudo geom disk list | grep Name
geli tunefs -t /dev/adaX
zpool set autotrim=on your_pool_name
```

## ZFS encrypted on HDDs

```bash
sudo zpool create -o ashift=12 -O compression=zstd -O encryption=on -O keyformat=passphrase tank mirror /dev/ada0 /dev/ada1
sudo zpool status
sudo zfs create tank/vms          # For VM images (inactive storage)
sudo zfs create tank/backups      # Sequential dumps
sudo zfs create tank/files        # General files
sudo zfs create tank/databases    # DB dumps/files

```

## ZFS SW RAID -> GELI -> UFS 

```bash
sudo geom disk list

# cleanup SSD via
sudo gpart destroy -F /dev/ada0
sudo gpart destroy -F /dev/ada1
# ...or - if fails with 'gpart: arg0 'ada0': Invalid argument' - wipe out the headers:
sudo dd if=/dev/zero of=/dev/ada0 bs=1M count=10
sudo dd if=/dev/zero of=/dev/ada1 bs=1M count=10

# create partition map
sudo gpart create -s gpt /dev/ada0
sudo gpart create -s gpt /dev/ada1

# Create the ZFS partitions using the full disk space.
# -a 4k (or -a 1M which is mathematically identical for 4K boundaries) is critical for SSD performance and longevity
sudo gpart add -t freebsd-zfs -l ssd0 -a 4k /dev/ada0
sudo gpart add -t freebsd-zfs -l ssd1 -a 4k /dev/ada1

# Create the mirrored ZFS pool
# -o ashift=12   : Tells ZFS the disks use 4K physical sectors
sudo zpool create -o ashift=12 -o autotrim=on data_pool mirror gpt/ssd0 gpt/ssd1

# Create a sparse ZVOL matching UFS's 32K block size.
# -s              : Makes it a sparse (thin-provisioned) volume
# -o volblocksize : Matches the default UFS block size to prevent write amplification
sudo zfs create -V 850G -o volblocksize=32K -o compression=off data_pool/geli_zvol

# Initialize GELI on the ZVOL using a 4K sector size
sudo geli init -s 4096 /dev/zvol/data_pool/geli_zvol

# Attach (unlock) the GELI volume
sudo geli attach /dev/zvol/data_pool/geli_zvol

# Format the unlocked GELI volume with UFS.
# -U : Enables Soft Updates (critical for UFS performance)
# -t : Enables TRIM support on the filesystem
sudo newfs -U -t /dev/zvol/data_pool/geli_zvol.eli

# Create the folder and mount
# -o noatime : Prevents UFS from generating disk writes just for reading a VM image
sudo mkdir -p /mnt/enc_data_pool
sudo mount -o noatime /dev/zvol/data_pool/geli_zvol.eli /mnt/enc_data_pool
```
([ref](https://www.perplexity.ai/search/i-need-instructions-on-how-to-DZy.711WTji4Ln4wxnA_Yg))

### Moving VM from ZVOL to a disk

```bash
sudo zfs list -t volume
sudo dd if=/dev/zvol/zroot/vm/web-services-vm/disk0 of=/mnt/enc_data_pool/web-services-vm.img bs=1M status=progress
```
## ZFS for VMs, no encryption

```bash
sudo zfs set recordsize=64K zroot/vm
sudo zfs set compression=zstd zroot/vm
sudo zfs set atime=off zroot/vm
sudo zfs set primarycache=metadata zroot/vm
```

zstd is Ok/good for compression, increasing the level would decrease the performance.
On NVMe disks raw files are faster, compared to the zfs partitions ([ref](https://klarasystems.com/articles/virtualization-showdown-freebsd-bhyve-linux-kvm/), [ref2](https://www.perplexity.ai/search/how-do-i-enable-compression-on-2TUNxNHmS.mig3v7AnE9iQ))

## Optimizing ZFS ARC cache

for the server with VMs on it, the cache's max size is better be limited
```bash
echo 'vfs.zfs.arc_max="4G"' | sudo tee -a /boot/loader.conf > /dev/null # to limit to 4Gb
```

# CPU performance optimization

```bash
sysctl machdep.idle # better be `mwait`
sysctl dev.cpu.0.cx_lowest # better be C1 / C0 (not C2/C3)
```

# Tricks

### sudo to preserve home dir vars and envs

```bash
echo 'Defaults env_keep += "HOME"' | sudo tee /usr/local/etc/sudoers.d/env_keep && sudo chmod 0440 /usr/local/etc/sudoers.d/env_keep && sudo visudo -c
```

# Network

```bash
systat -ifstat # shows real-time interfaces statistics 
```

# ZFS

## Snapshots

```bash
sudo zfs snapshot zroot/vm/web-services-vm/disk0@before_cloudron_update
sudo zfs list -t snapshot
cd /zroot/vm/web-services-vm/.zfs/snapshot # to view the snapshot of interest
zfs destroy pool/dataset@snapshot_name
```
# Disks encryption

Grab data from [[2025-10-30]]

- creating encrypted partition inside ZFS (as [per](https://genneko.github.io/playing-with-bsd/storage/encrypted-temporary-storage/); [perplexity thread](https://www.perplexity.ai/search/find-do-not-create-ready-to-us-6r4rdFgYSyyUxuArzb_qxg)):
```bash
sudo zfs create -V 50g zroot/vm/data-disks
sudo geli init -s 4096 /dev/zvol/zroot/vm/data-disks # 4096 sector size is recommended for zvol
sudo geli attach /dev/zvol/zroot/vm/data-disks
sudo newfs /dev/zvol/zroot/vm/data-disks.eli
sudo mount /dev/zvol/zroot/vm/data-disks.eli /mnt/data-disks
cd /mnt/data-disks
# ... 
sudo umount /mnt/data-disks
sudo geli detach /dev/zvol/zroot/vm/data-disks
```

- creating a disk for the vm bhyve:
```bash
sudo truncate -s 50G /mnt/data-disks/app-storage.disk
```
with the following lines in the config file:
```
disk2_type="virtio-blk"
disk2_name="/mnt/data-disks/app-storage.disk"
disk2_dev="custom"
``````

# Troubleshooting

## Connect to Linux gues

```bash
sudo vm console $vm_name # ~ + Ctrl+D to exit
```

## FreeBSD boot via Linux Rescue system

1. Initiate recovery and *note down the root password* (`<generated-root-password>`)
2. Restart the server via Reset -> Press power button of the server (twice)
3. Duplicate your SSH entry with `root` user and `22` connection port, without `IdentityFile`
4. Connect via `ssh` (removing previous SSH key)
5. Let's do the recovery now (Linux's ZFS support is terrible, so booting FreeBSD for that):
```bash
ssh-keygen -t ed25519 -C "my-key"
wget https://depenguin.me/run.sh && chmod +x run.sh
./run.sh -d /root/.ssh/id_ed25519.pub
ssh -p 1022 mfsbsd@127.0.0.1

sudo su -

zpool import
mkdir /server_fs /server_fs_root
zpool import -f -R /server_fs zroot
zfs list 
zfs set mountpoint=/server_fs_root/ zroot/ROOT/default
# zfs list | grep "zroot/ROOT/default"
zfs mount zroot/ROOT/default
cd /server_fs/server_fs_root/etc

vi rc.conf # and do your thing; 'firewall_type="open"' is the fastest way to reboot actually disabling firewall

cd && zfs set mountpoint=/ zroot/ROOT/default # REVERT THINGS BACK
zpool export -a
sync
shutdown -h now # shuts down freebsd vm

shutdown -r now # rescue system
# the server might need to be started from Robot Console, despite '-r' flag

# Archive

### vm-bhyve

Making sense: [ref](https://wiki.freebsd.org/chengcui/install_Ubuntu_Linux_VM_via_bhyve), [ref2](https://xw.is/wiki/Install_Ubuntu_Linux_20.04_LTS_in_vm-bhyve)
[ref3](https://www.sisyphus.de/post/use-cloud-images-with-freebsd-bhyve-vm/) - the one with `-n` on it with network parameters, [ref4](https://forums.freebsd.org/threads/cloud-init-bhyve-virtual-machine.90389/) forum with network settings via `-n`, [ref5](https://skife.org/b4/setting-up-vm-bhyve/) - beautiful page with quick howto, [ref6](https://alfaexploit.com/en/posts/vm_bhyve/) - extensive cloud-init options for bhyve, 


**FreeBSD, etc - generic**
```bash
sudo vm iso https://download.freebsd.org/ftp/releases/ISO-IMAGES/14.2/FreeBSD-14.2-RELEASE-amd64-bootonly.iso
sudo vm create -t linux|freebsd my_server
sudo vm install [-f] my_server FreeBSD-14.2-RELEASE-amd64-bootonly.iso
sudo vm console my_server
```
**TPM emulation for Windows** - was not tested

[reference](https://forums.freebsd.org/threads/bhyve-tpm-2-0-emulation-with-swtpm.97692/)

```bash
sudo pkg install swtpm
sudo kldload fusefs # and add `kld_list="fusefs"` to /etc/rc.conf
```

**On Windows**
Other articles to read:
- https://forums.freebsd.org/threads/bhyve-graphics-install-and-vncviewer.88114/ - mostly refers the following articles
	- https://klarasystems.com/articles/from-0-to-bhyve-on-freebsd-13-1/ - quite of use!
	- https://srobb.net/vm-bhyve.html - very detailed guide
	- https://vermaden.wordpress.com/2023/08/18/freebsd-bhyve-virtualization/ - tramendeosly detailed article
	- https://github.com/churchers/vm-bhyve/wiki - a great Wiki
		- https://github.com/churchers/vm-bhyve/wiki/UEFI-Graphics-(VNC) - on VNC
		- https://github.com/churchers/vm-bhyve/wiki/Supported-Guest-Examples - examples
- https://github.com/freebsd/vm-bhyve - tool doc
- https://claude.ai/chat/52823a9c-f5ad-4f90-a165-4ea10dd9750a - how to setup static internal & public IP address for the guest




## IPF(ilter)

[FreeBSD Handbook](https://docs.freebsd.org/en/books/handbook/firewalls/#firewalls-ipf).

```bash
sudo tee -a /etc/rc.conf >> /dev/null << 'EOF'
ipfilter_enable="YES"             # Start ipf firewall
ipfilter_rules="/etc/ipf.rules"   # loads rules definition text file
ipv6_ipfilter_rules="/etc/ipf.rules" # loads rules definition text file for IPv6
ipmon_enable="YES"                # Start IP monitor log
ipmon_flags="-Ds"                 # D = start as daemon & s = log to syslog
gateway_enable="YES"              # Enable as LAN gateway
ipnat_enable="YES"                # Start ipnat function
ipnat_rules="/etc/ipnat.rules"    # rules definition file for ipnat
EOF

sudo ipfstat -io # see a list of the rules

cp /etc/ipf.rules new_ipf.rules
vi new_ipf.rules
sudo ipf -Fa -f new_ipf.rules
cat new_ipf.rules | sudo tee /etc/ipf.rules >> /dev/null
sudo ipf -Fa -f /etc/ipf.rules
sudo ipfstat -io


sudo tee -a new_ipnat.rules >> /dev/null << 'EOF'
map igb0 192.168.8.0/24 -> 0/32 # no protocols limits
EOF
sudo ipnat -CF -f new_ipnat.rules
sudo ipnat -l
cat new_ipnat.rules | sudo tee /etc/ipnat.rules >> /dev/null
sudo ipnat -CF -f /etc/ipnat.rules
```

Rules example below:
```
pass in quick on lo0 all
pass out quick on lo0 all

pass in quick on vm-public all
pass out quick on vm-public all

# Public interface - allow all out, but only HTTPS, SSH & VNC in
# SSH access narrowed down to NoCloud IP on Hetzner side

pass out quick on igb0 all keep state

pass in quick on igb0 proto tcp from any to any port = 38610 # SSH
pass in quick on igb0 proto tcp from any to any port = 5900 # VNC
pass in quick on igb0 from any to any port = 443 # HTTPS (TCP & UDP)

block in log first quick on igb0
```

## IPFW
IPFW feels like more native to FreeBSD

Refs: [1](https://blog.socruel.nu/freebsd/how-to-implement-an-internet-facing-freebsd-ipfw-firewall.html), [2](https://www.zenarmor.com/docs/network-security-tutorials/freebsd-firewall-configuration-with-ipfw), [some rules generator](https://imaprettykitty.com/wof/)

```bash
sudo sysrc firewall_enable="YES"
sudo sysrc firewall_type="open" # NEVER DO 'UNKNOWN'!!!!
sudo sysrc firewall_nat_enable="YES"
sudo service ipfw start


# disable TCP segmentation offloading, as otherwise in-kernel NAT won't work
sudo tee -a /etc/sysctl.conf >> /dev/null << 'EOF'
net.inet.tcp.tso="0"
EOF

sudo tee -a /boot/loader.conf >> /dev/null << 'EOF'
net.inet.ip.fw.default_to_accept="1"
EOF

sudo vi /etc/ipfw.rules # below

sudo sysrc -x firewall_type
sudo sysrc firewall_script="/etc/ipfw.rules" 
sudo service ipfw restart
```

Below is a basic working example - NON complete, allows communication on internal interfaces and NAT from virtual machines; and most probably many other things as well are permitted.
```bash
#!/bin/sh

fw="/sbin/ipfw"  

WAN="igb0"
SSH_PORT=38610
NAT_SKIP="skipto 1000"

# Flush all rules
$fw -f flush

# NAT
$fw disable one_pass
$fw nat 1 config if $WAN same_ports unreg_only reset

# NAT
$fw add 90 reass all from any to any in # reassemble inbound packets
$fw add 95 nat 1 ip from any to any in via $WAN #

# Track dynamic connections
$fw add 100 check-state

# Required to connect to VMs
$fw add 105 allow ip from any to any via vm-public

# SSH
$fw add 300 allow tcp from any to me ${SSH_PORT} in via ${WAN} setup keep-state

  

# Outbound policy: allow everything
$fw add 400 $NAT_SKIP ip from any to any out via ${WAN} keep-state
$fw add 410 $NAT_SKIP ipv6 from any to any out via ${WAN} keep-state

# Default deny (&log)
$fw add 999 deny log ip from any to any
$fw add 1000 nat 1 ip from any to any out via ${WAN} # skipto location for outbound stateful rules
$fw add 1001 allow ip from any to any
```


# Working with firewall 


> [!NOTE] Never change `/etc/ipfw.rules` directly!
> Create new rules file, try it. If thing go wrong - reboot will still bring a working server.



## DNSMasq setup

```bash
sudo tee /usr/local/etc/dnsmasq.conf > /dev/null << 'EOF'
port=0
domain-needed
no-resolv
except-interface=lo0
bind-interfaces
local-service
dhcp-authoritative

interface=vm-public
dhcp-range=192.168.8.10,192.168.8.254

dhcp-host=58:9c:fc:10:5f:1e,192.168.8.5 # masterisks
log-dhcp

# This fixes a security hole. see CERT Vulnerability VU#598349
dhcp-name-match=set:wpad-ignore,wpad
dhcp-ignore-names=tag:wpad-ignore
EOF
sudo service dnsmasq enable
sudo service dnsmasq start
```