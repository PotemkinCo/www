---
title: "Monit and MMonit monitoring tool"
---

*Plenty of notes at *2023-07-17**

# Monit (client)

```bash
apt install monit
```

## Disk monitoring

```bash
sudo apt install smartmontools 
lsblk # to get disks id
```
Create `disk_health.sh` script:
```bash
#!/bin/sh
#set -x

DISK1=nvme0n1
DISK2=nvme1n1
DISK3=nvme2n1
STATUS1=`sudo /usr/sbin/smartctl -H /dev/${DISK1} | grep overall-health | awk 'match($0,"result:"){print substr($0,RSTART+8,6)}'`
STATUS2=`sudo /usr/sbin/smartctl -H /dev/${DISK2} | grep overall-health | awk 'match($0,"result:"){print substr($0,RSTART+8,6)}'`
STATUS3=`sudo /usr/sbin/smartctl -H /dev/${DISK3} | grep overall-health | awk 'match($0,"result:"){print substr($0,RSTART+8,6)}'`
if [ "$STATUS1" = "PASSED" ] && [ "$STATUS2" = "PASSED" ] && [ "$STATUS3" = "PASSED" ]; then
    RC=0
else
    RC=1
fi
echo "${DISK1}: ${STATUS1}, ${DISK2}: ${STATUS2}, ${DISK3}: ${STATUS3}"
exit $RC
```
And add it to the `monit` config:
```bash
check program disk_health with path "/home/ubuntu/tools/disk_health.sh"
    every 120 cycles
    if status > 0 then alert
    group health
```

## Custom Installation


> [!NOTE] It's not easy
> It might be better to stick with version offered by OS. Fresh files are provided at [BitBucket](https://bitbucket.org/tildeslash/monit/downloads/?tab=downloads), but I can't see easy way to extract that. [REST API](https://developer.atlassian.com/cloud/bitbucket/rest/api-group-downloads/#api-group-downloads) seems to be there, but it requires a key.


Version could be verified at [download page](https://mmonit.com/monit/#download):
```bash
wget https://mmonit.com/monit/dist/binary/5.33.0/monit-5.33.0-linux-x64.tar.gz
tar zxvf monit*.tar.gz
cd monit-*
cp bin/monit /usr/local/bin/
cp conf/monitrc /etc/
```

For autostart - use systemd: https://mmonit.com/wiki/MMonit/Setup#autolaunchsystemd
monit way is quite broken.

Note:
> <...> the official Monit is looking for /etc/monitrc or ~/.monitrc.
> Some distributions are looking e.g. for /etc/monit.conf or /etc/monit/monitrc, etc. To share the configuration between 3rd party and official Monit, you can create e.g. a hardlink from for example /etc/monit.conf (the path and name depends on 3rd party defaults) to /etc/monitrc:

`ln /etc/monit.conf /etc/monitrc`

A lot of checks could be also implemented via some script - [doc here](https://mmonit.com/monit/documentation/monit.html#PROGRAM-OUTPUT-CONTENT-TEST).

Preparation.
1. Make sure to change IP address and password according to the environment
2. ! Don't use HTTP without SSL in unprotected environment.
```bash
apt install monit && echo && monit -V # must be 5.2 or higher
cp /etc/monit/monitrc /etc/monit/monitrc-backup
vi /etc/monit/monitrc
```
And here is a template:
```yaml
#Send alerts to M/Monit aggregator
set mmonit https://monit:<password>@mmonit.example.com/collector
  with timeout 10 seconds

set daemon 60 # check services at ... seconds intervals

#Test certificate validity
#check host ssl_cert_expiration with address foobar.com
#  if failed
#        port 443
#        protocol https and certificate valid for > 25 days
#  then alert


#Basic system check
check system $HOST
  if loadavg (1min) per core > 2 for 5 cycles then alert
  if loadavg (5min) per core > 1.5 for 10 cycles then alert
  if cpu usage > 90% for 10 cycles then alert
  if memory usage > 85% then alert
  if swap usage > 35% then alert

#Test fs
check filesystem rootfs with path /
  if space usage > 85% then alert

#Notify about reboot comming
check file reboot-required with path /var/run/reboot-required
    if exist then alert

#Monitor modification of the access files
check file root_ssh_keys with path /root/.ssh/authorized_keys
     if changed checksum then alert
check file etc_passwd with path /etc/passwd
     if changed checksum then alert
check file etc_shadow with path /etc/shadow
     if changed checksum then alert

#Test outside connectivity
check host 1.1.1.1 with address 1.1.1.1
  if failed ping count 1 then exec "/bin/bash -c '/usr/bin/mtr -c 4 -C 1.1.1.1 > /tmp/mtr_trace_`date +%Y_%m_%d_%H-%M`'"
  #if failed ping count 2 responsetime < 50 ms then alert # Only works starting with 5.3.3

set httpd port 2812 use address 127.0.0.1 allow monicli:<generated-password>
set log /var/log/monit.log
set idfile /var/lib/monit/id
set statefile /var/lib/monit/state
set eventqueue
  basedir /var/lib/monit/events  # set the base directory where events will be stored
  slots 500                      # optionally limit the queue size

#include /etc/monit/conf.d/*
#include /etc/monit/conf-enabled/*
```

### Starting (troubleshooting `start all`)

> The "monit start all" will start all services - but it is just one-time action, similar to e.g. "systemctl start apache". The "systemctl start apache" just passes the command to systemd daemon, which needs to be started first - Monit is similar.
> 
> When Monit is running in the background, the "monit start all" will pass the command to it and exit. The Monit daemon will perform services start (and also performs regular service monitoring).
> 
> When Monit is NOT running in the background, the "monit start all" will start all services in its own context and exit. If Monit is not running in the background, no regular monitoring is performed.
> 
> => if you need to monitor services regularly, you need to start the monitoring service (Monit).
### Matrix alerts

https://spec.matrix.org/v1.7/client-server-api/#examples

Here is my `alert.sh` script:
```bash
#!/bin/bash
HOST='matrix.example.com'
ROOM_ID='!roomid:matrix.example.com'
TOKEN='<matrix-access-token>'

MESSAGE="<b>$MONIT_SERVICE</b>@<i>$MONIT_HOST</i> at $MONIT_DATE:<br/>$MONIT_EVENT: $MONIT_DESCRIPTION"

/usr/bin/curl -XPOST -k -d "{\"msgtype\":\"m.text\", \"body\": \"\", \"format\": \"org.matrix.custom.html\", \"formatted_body\":\"$MESSAGE\"}" "https://$HOST/_matrix/client/r0/rooms/$ROOM_ID/send/m.room.message?access_token=$TOKEN"

#/usr/bin/curl -s -X POST -H 'Content-type: application/json' --data "{\"type\":\"m.message\", \"content\": {\"m.markup\": {\"mimetype\": \"text/plain\", \"body\": \"$MESSAGE\"}} }" "https://$HOST/_matrix/client/r0/rooms/$ROOM_ID/send/m.room.message?access_token=$TOKEN"
```

# M/Monit (server)

## Installation

System requirements on M/Monit:

> Memory and Disk space. A minimum of 10 megabytes of RAM is required and around 25 MB of free disk space.


> [!NOTE] Existing license is for 3.7.15 version
> Latest version is v4 - if required, requires purchasing new license.

### Server license key (v3)

MMonit `mmonit/conf/license.xml`:
```xml
<License owner="...">
    <YOUR-MMONIT-LICENSE-KEY>
</License>
```


Get appropriate URL from https://www.mmonit.com/dist/3/ page, followed by:
```bash
cd /usr/local
wget https://mmonit.com/dist/3/mmonit-3.7.15-linux-x64.tar.gz
tar xzf mmonit*.tar.gz && rm mmonit-*-linux-x64.tar.gz
ln -s mmonit-3.7.15 mmonit
cd mmonit/
/usr/local/mmonit/bin/mmonit 
nc -vv localhost 8080
```

**To enable daemon to run behind nginx proxy**

the following string has to be done / adjusted at `config/server.xml` at mmonit installation path:

find
```xml
<Connector address="*" port="8080" processors="10" />
```
Replace with:
```xml
<Connector address="*" port="8080" processors="10" proxyScheme="https" proxyName="mmonit.example.com" proxyPort="443" />
```

At CloudRon add app proxy with upstream URL: `http://127.0.0.1:8080`.

Login to MMonit with admin/swordfish

Auto-start m/monit via monit (`vi /etc/monit/conf.d/mmonit`) - add the following lines:
```bash
check process mmonit with pidfile /usr/local/mmonit/logs/mmonit.pid  
start program = "/usr/local/mmonit/bin/mmonit -d" as uid 0 and gid 0  
stop program = "/usr/local/mmonit/bin/mmonit stop" as uid 0 and gid 0
```

### Configuration

Things to change in UI:
- change admin & monit password: admin is used to authenticate on the web dashboard and monit is used to add users 


# Hardware monitoring
as [per](https://mmonit.com/wiki/Monit/CustomTests) (other examples [there](https://mmonit.com/wiki/Monit/ConfigurationExamples#CPUTemp), not applied currently)
```bash
sudo apt-get install lm-sensors
sudo sensors-detect
```

add the following lines to the config:
```bash
#HW sensors
check program sensors with path /usr/bin/sensors
    if status != 0 then alert

#SW RAID
# Using simple regular expression matching
check file raid with path /proc/mdstat
if match "\[.*_.*\]" then alert

# Using mdadm for improved granularity
check program raid-md0 with path "/sbin/mdadm --misc --detail --test /dev/md0"
if status != 0 then alert

check program raid-md1 with path "/sbin/mdadm --misc --detail --test /dev/md1"
if status != 0 then alert
```

# Troubleshooting

`monit -vv start all -I` catch run time errors

From support:
`monit -v` (enable debug mode in background)
`monit -vI` (debug mode in foreground)

Usefull links:
- configuration with [m/monit](https://monitdevops.home.blog/getting-started-with-monit-and-m-monit/)
	- configuration with [m/monit including launching m/monit from monit](https://manishpaneri.blogspot.com/2017/08/how-to-install-setup-mmonit-on-ubuntu.html)
