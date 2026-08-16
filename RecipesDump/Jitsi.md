# Jitsi

## Architecture

Architecture ([ref](https://jitsi.github.io/handbook/docs/architecture/)):
- jitsi meet - static JS app (web thing)
- jvb - streams bridge / router, mix traffic between users (main thing)
- jicofo - manage sessions & load balancer
- prosody - xmpp server, used for signalling (required)
- jigasi - SIP gateway (optional)
- jibri - broadcasting service (optional)
- etherpad - for docs sharing (optional)


- JVB_TCP_HARVESTER_DISABLED set to true 'won’t help people with poor connections but people behind spartan firewalls' ([ref](https://github.com/jitsi/docker-jitsi-meet/issues/296#issuecomment-604264719)).
- jvb seems like could be a replacement for TURN ([ref](https://community.jitsi.org/t/corporate-firewalls-use-port-443-for-videobridge-with-jitsi-docker/28285)): 'If the network equipment uses deep packet inspection your only shot is a turnserver, jvb does not support a standard https link for the TCP fallback, and anyway coturn handling TCP traffic performs better than jvb.'
- got [a confirmation](https://github.com/jitsi/jitsi-meet/issues/324#issuecomment-123425539): 'As jitsi-videobridge received TCP support, turn server is not needed anymore, as it was used to take the participants who has problems using UDP.'
- jvb/videobridge can [route traffic over TCP only, but it's not recommended](https://github.com/jitsi/jitsi-videobridge/blob/master/doc/tcp.md), as handshake is easily recognizeable.
- WebSockets are possible instead of [WebRTC (but not recommended, though)](https://github.com/jitsi/jitsi-videobridge/blob/master/doc/web-sockets.md)

Overall it seems like the best configuration - it's TCP only configuration with public available TURN services.

On videobridge ([ref](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-manual#running-behind-nat)): 'Jitsi Videobridge can run behind a NAT, provided that both required ports are routed (forwarded) to the machine that it runs on. By default these ports are `TCP/4443` and `UDP/10000`. If you do not route these two ports, Jitsi Meet will only work with video for two people, breaking upon 3 or more people trying to show video.'

## System requirements

Hetzner recommends CPX21 for Jitsi - it's 3vCPUs 4GB RAM 80GB SSD configuration for 7EUR.

## JVB & turn-server
As [per](https://github.com/jitsi/docker-jitsi-meet/issues/1959#issuecomment-2452581158):
> The turnserver is needed in two cases. When a participant cannot use UDP, it will fallback to using TCP for the media via the turnserver. And the second one is to offload traffic from jvb in p2p calls when participants are not able to establish a direct connection, they need a relay - jvb and turnserver are such relays, if turn is not available the jvb will be used, but this only in case when direct p2p does not succeed.

## How to change STUN server
As [per](https://github.com/jitsi/docker-jitsi-meet/issues/675#issuecomment-2445465152):
> It's a template using a gotemplate-like syntax:
> The file you want is to review is probably:
[https://github.com/jitsi/docker-jitsi-meet/blob/master/jvb/rootfs/defaults/jvb.conf](https://github.com/jitsi/docker-jitsi-meet/blob/master/jvb/rootfs/defaults/jvb.conf)
Then the tpl command is run on every container startup:
[tpl /defaults/jvb.conf > /config/jvb.conf  
](https://github.com/jitsi/docker-jitsi-meet/blob/47d974d88cba7d1e70a88ea83f65394e96787cc1/jvb/rootfs/etc/cont-init.d/10-config#L74C1-L75C1)
For tpl syntax you can see the project here:
[https://github.com/jitsi/tpl](https://github.com/jitsi/tpl)
You can also see plenty of examples in the defaults/ directories in this repo.

# Docker setup

```bash
curl https://get.docker.com/ | sh
sudo apt install unzip
mkdir jitsi
wget $(curl -s https://api.github.com/repos/jitsi/docker-jitsi-meet/releases/latest | grep 'zip' | cut -d\" -f4)
unzip stable-*
cd jitsi-docker-jitsi-meet-*
cp env.example .env
./gen-passwords.sh
mkdir -p ./data/{web,transcripts,prosody/config,prosody/prosody-plugins-custom,jicofo,jvb,jigasi,jibri}
cp docker-compose.yml .env ../
cd ..
vi .env # as per example below
docker compose up -d
```

That seems to be a working `.env` file. That file and docker-compose are the only two files required.
```TOML
TZ=Europe/Berlin
PUBLIC_URL=https://jitsi.example.com
JVB_ADVERTISE_IPS=<server-ip>
JVB_STUN_SERVERS=stun.example.com:3478
STUN_HOST=stun.example.com
STUN_PORT=3478
TURN_HOST=stun.example.com
TURN_PORT=5349
TURN_TRANSPORT=tcp
TURN_CREDENTIALS=<turn-secret>
TURNS_HOST=stun.example.com
TURNS_PORT=5349

ENABLE_CLOSE_PAGE=0
ENABLE_PREJOIN_PAGE=0
ENABLE_WELCOME_PAGE=0

JVB_ADVERTISE_PRIVATE_CANDIDATES=false
ENABLE_P2P=false

CONFIG=./data
# JVB port to be public facing
JVB_PORT=10000
# HTTP port to be proxied via Caddy
HTTP_PORT=127.0.0.1:8000
HTTPS_PORT=127.0.0.1:8443
RESTART_POLICY=unless-stopped
ENABLE_JAAS_COMPONENTS=0
ENABLE_LETSENCRYPT=0
# enable recording here
ENABLE_RECORDING=1
JIBRI_RECORDING_DIR=/config/recordings
JIBRI_FINALIZE_RECORDING_SCRIPT_PATH=/config/finalize.sh
XMPP_MUC_MODULES=muc_allowners # everyone is moderator -> to let anyone switch on recording 

JICOFO_AUTH_PASSWORD=...
JVB_AUTH_PASSWORD=...  
JIGASI_XMPP_PASSWORD=...  
JIBRI_RECORDER_PASSWORD=...  
JIBRI_XMPP_PASSWORD=...  

#JITSI_IMAGE_VERSION=latest
```

Setup Caddy:
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list sudo apt update sudo apt install caddy

```

`vi /etc/caddy/Caddyfile`

```Caddyfile
# Global
(logging) {
 log {
  hostnames {args[0]}
  output file //var/log/caddy/{args[0]}.log
 }
}

# This enables full logging of the credentials, useful in debugging Authorization header
{
 servers {
  log_credentials
 }
}

meet.example.com {
  import logging meet.example.com
  reverse_proxy 127.0.0.1:8000
}
```

## Jibri
```bash
wget https://raw.githubusercontent.com/jitsi/docker-jitsi-meet/refs/heads/master/jibri.yml
tail -n +3 jibri.yml # add at to docker-compose.yml manually
docker compose up -d
```

Additional parameters config is [here](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-docker/#recording--live-streaming-configuration-with-jibri).
Recording is available as mp4 file at data/jibri/recordings (or smth like that)

## proxy JVB via socat in docker
```yaml
services:
  jitsi_jvb_udp:
    image: alpine/socat
    container_name: jitsi_jvb_udp
    command: "UDP4-LISTEN:10000,reuseaddr,fork UDP4:jitsi-server:10000"
    network_mode: "host"
    restart: unless-stopped
```

Ports:
- 8000 (HTTP) proxy by Caddy
- 10000 UDP - JVB, available for publicly
- 8080 TCP - not in use
- 8888 TCP - not in use

## shell script

Nice docs are available here: https://jitsi.github.io/handbook/docs/intro

Prepare clean empty server, that will only do the Jitsi conference for the people.

This guide follows scripted installation as per [this page](https://github.com/jitsi-contrib/installers/tree/main/jitsi-base).

Create A DNS records for this server, ideally: `*.meet` - this will hide the exact configured names.
Wait for some time for the DNS records to propagate - the script verify via public DNS services.


> [!NOTE] Add `resolver1.opendns.com` server to the firewall exception
> Otherwise `dig -4 +short $TURN_HOST @resolver1.opendns.com` would fail for no good reason. It's `208.67.222.222` as of 2023-07-09


<aside>
💡 If server's memory is less than 8Gb, you might want to comment out 126 line of the script, that do 'exit' after that check.

</aside>

```bash
apt update && apt upgrade -y
wget -T 10 -O jitsi-base-installer https://raw.githubusercontent.com/jitsi-contrib/installers/main/jitsi-base/jitsi-base-installer
export JITSI_HOST=open.meet.domain.com
export TURN_HOST=turn.meet.domain.com
host $JITSI_HOST # test DNS is populated
bash jitsi-base-installer
```

## Jitsi with password protection

Jitsi's config files are at `/etc/prosody` (as per [this page](https://jitsi.github.io/handbook/docs/devops-guide/devops-guide-manual)).
```bash
apt-get update
apt-get install wget

wget -T 10 -O jitsi-secure-installer https://raw.githubusercontent.com/jitsi-contrib/installers/main/jitsi-secure/jitsi-secure-installer

export JITSI_HOST=jitsi.yourdomain.com
export TURN_HOST=turn.yourdomain.com

bash jitsi-secure-installer
prosodyctl register <USERNAME> <FQDN> <PASSWORD>
```

Пароль будет запрашиваться для администратора.

# Jitsi updates

> [!WARNING] Update likely to break the system
> Last time I did this (2023-12-08) - it did broke the whole Jitsi system.

```bash
apt list --installed | grep jitsi | grep video # >= 2.3.38
apt list --installed | grep jicofo # >= 1.0-1050
apt install jicofo jitsi-meet jitsi-meet-prosody jitsi-meet-turnserver jitsi-meet-web jitsi-meet-web-config jitsi-videobridge2
```
# Jitsi functional tests (torturer)

> [!NOTE] Server resources requirements
> At least 2 CPU cores required. Otherwise tests will fail with timeout error.

[Ref](https://github.com/jitsi/jitsi-meet-torture/tree/master/doc/grid).

```shell
wget -O - https://raw.githubusercontent.com/alexander-potemkin/quickies/main/docker_ubuntu.sh | bash
sudo apt install -y maven
git clone https://github.com/jitsi/jitsi-meet-torture.git
cd jitsi-meet-torture/doc/grid
cp -r ../../resources .
wget -P resources https://github.com/jitsi/jitsi-meet-torture/releases/download/example-video-source/FourPeople_1280x720_30.y4m
sudo docker build --build-arg VERSION=latest --build-arg BROWSER=chrome -t jitsi/selenium-standalone-chrome:latest .
sudo docker build --build-arg VERSION=latest --build-arg BROWSER=firefox -t jitsi/selenium-standalone-firefox:latest .
sudo docker build --build-arg VERSION=beta --build-arg BROWSER=firefox -t jitsi/selenium-standalone-firefox:beta .
sudo docker build --build-arg VERSION=beta --build-arg BROWSER=chrome -t jitsi/selenium-standalone-chrome:beta .
vi docker-compose-v3-dynamic-grid.yml # add 'restart: unless-stopped' to both images
#run single test
cd ../../
sudo docker compose -f ./doc/grid/docker-compose-v3-dynamic-grid.yml up -d
echo "10 seconds timeout" && sleep 10 && sudo docker ps # check that the containers are not restarting
mvn test -Djitsi-meet.instance.url=https://meet.example.com -Djitsi-meet.tests.toRun=AudioOnlyTest -Denable.headless=true \
-Dweb.participant1.isRemote=true -Dweb.participant2.isRemote=true -Dweb.participant3.isRemote=true -Dweb.participant4.isRemote=true -Dweb.participant5.isRemote=true -Dweb.participant6.isRemote=true -Dweb.participant7.isRemote=true -Dweb.participant8.isRemote=true -Dweb.participant9.isRemote=true -Dweb.participant10.isRemote=true -Dweb.participant11.isRemote=true -Dweb.participant12.isRemote=true \
-Dremote.resource.path=/usr/share/jitsi-meet-torture \
-Dremote.address=http://localhost:4444/wd/hub
vi scripts/malleus.sh
```
Replace `MALLEUS_TESTS_TO_RUN=MalleusJitsificus` (205 line as of 2024-02-02) with `MALLEUS_TESTS_TO_RUN=AudioOnlyTest,MuteTest`.

If more resources are available (4CPUs and 8Gb RAM at least was on the latest machine), the following tests could be executed: `MALLEUS_TESTS_TO_RUN=AudioOnlyTest,BreakoutRoomsTest,DisableSelfViewTest,EtherpadTest,FakeDialInAudioTest,FollowMeTest,LockRoomTest,ModeratorTest,MuteTest,OneOnOneTest,SinglePortTest,SwitchVideoTest,UrlNormalisationTest`.


`vi ~/test_jitsi.sh`:
```shell
#!/bin/bash
SERVER_TO_TEST="https://meet.example.com"

# logs and flag files
JITSI_TEST_OUTPUT="/tmp/jitsi_test_`date +%Y_%m_%d_%H-%M`"
JITSI_FAILS_FLAG_FILE="/root/jitsi.fails"

echo "Changing CWD"
SCRIPTDIR="$(dirname "$(readlink -f "${BASH_SOURCE[0]}")")" && cd $SCRIPTDIR/jitsi-meet-torture

echo "Starting Selenium grid"
docker compose -f ./doc/grid/docker-compose-v3-dynamic-grid.yml up -d

echo "Starting tests"
./scripts/malleus.sh --conferences=1 --participants=12 --senders=12 --audio-senders=12 --duration=120 --room-name-prefix=hammertesting --hub-url=http://127.0.0.1:4444/wd/hub --instance-url=$SERVER_TO_TEST 1>$JITSI_TEST_OUTPUT 2>$JITSI_TEST_OUTPUT.err

echo "Processing tests results"
# Check the exit status of the last command
if [ $? -ne 0 ]; then
  # Last command failed, so create the 'jitsi.fails' file
  touch $JITSI_FAILS_FLAG_FILE
  /root/matrix_dedicated_alert.sh "ERROR: Jitsi server $SERVER_TO_TEST **FAILED**!"
else
  # Last command succeeded, so remove the 'jitsi.fails' file if it exists
  if [ -e $JITSI_FAILS_FLAG_FILE ]; then
    rm $JITSI_FAILS_FLAG_FILE
    /root/matrix_dedicated_alert.sh "OK: Jitsi server $SERVER_TO_TEST **RECOVERED**"
  fi
fi

echo "Stopping Selenium grid"
docker ps --format "{{.Names}}" | sort | xargs --verbose --max-args=1 -- docker stop
docker compose -f ./doc/grid/docker-compose-v3-dynamic-grid.yml down

echo "Done."
```

Another (newer script)
```bash
#!/bin/bash
JITSI_TEST_OUTPUT="/tmp/jitsi_test_`date +%Y_%m_%d_%H-%M`"
JITSI_TEST_SUITE_FILE="/tmp/TestSuite.fails.`date +%Y_%m_%d_%H-%M`"
JITSI_FAILS_FLAG_FILE="/root/jitsi.fails"
#su - torturer -c 'cd /home/torturer/jitsi-meet-torture/ && ./scripts/malleus.sh --conferences=1 --participants=4 --senders=1 --audio-senders=2 --duration=120 --room-name-prefix=hammertesting --hub-url=http://127.0.0.1:4444/wd/hub --instance-url=https://meet.example.com' 1>$JITSI_TEST_OUTPUT 2>$JITSI_TEST_OUTPUT.err

su - torturer -c 'cd /home/torturer/jitsi-meet-torture/ && ./scripts/malleus.sh --conferences=2 --participants=4 --senders=2 --audio-senders=4 --duration=120 --room-name-prefix=hammertesting --hub-url=http://127.0.0.1:4444/wd/hub --instance-url=https://meet.example.com' 1>$JITSI_TEST_OUTPUT 2>$JITSI_TEST_OUTPUT.err

# Check the exit status of the last command
if [ $? -ne 0 ]; then
  # Last command failed, so create the 'jitsi.fails' file
  touch $JITSI_FAILS_FLAG_FILE
  /root/matrix_dedicated_alert.sh "Main Jitsi server is failing!"
  cp /home/torturer/jitsi-meet-torture/target/surefire-reports/TestSuite.txt $JITSI_TEST_SUITE_FILE
else
  # Last command succeeded, so remove the 'jitsi.fails' file if it exists
  if [ -e $JITSI_FAILS_FLAG_FILE ]; then
    rm $JITSI_FAILS_FLAG_FILE
    /root/matrix_dedicated_alert.sh "Main Jitsi server NO longer failing (shall be Ok)"
  fi
fi
```

crontab entry - execute test every 2 hours at working hours:
```cron
0 8-20/2 * * * /root/jitsi_test.sh > /root/jitsi_test.log
```

`vi /root/matrix_dedicated_alert.sh`:
```bash
#!/bin/bash
HOST='DNS'
ROOM_ID='!id:domain_name'
TOKEN='<matrix-access-token>'

MESSAGE="<i><b>$1</b></i>"

/usr/bin/curl -XPOST -k -d "{\"msgtype\":\"m.text\", \"body\": \"\", \"format\": \"org.matrix.custom.html\", \"formatted_body\":\"$MESSAGE\"}" "https://$HOST/_matrix/client/r0/rooms/$ROOM_ID/send/m.room.message?access_token=$TOKEN"
```

**Note:**
This config is only for 4 people concurrent video call. You can raise the number by adding more `NODE_MAX_INSTANCES` & `NODE_MAX_SESSION` parameter, or add more node with same configuration (just copy-paste node2 and name it node3, 4, etc.).


> [!NOTE] Close server with firewall!
> Close at least port 4444 from an outside world.


# Archive

## Docker - deprecated
```bash
wget -O - https://raw.githubusercontent.com/alexander-potemkin/quickies/main/docker_ubuntu.sh | bash
sudo apt-get install docker-compose-plugin unzip
sudo usermod -aG docker `whoami`
JITSI_ARCHIVE=`curl -s https://api.github.com/repos/jitsi/docker-jitsi-meet/releases/latest | grep 'zip' | cut -d\" -f4`
wget --output-document=$(basename "$JITSI_ARCHIVE").zip "$JITSI_ARCHIVE"
unzip $(basename "$JITSI_ARCHIVE").zip
cd jitsi-docker-jitsi-meet-*/
cp env.example .env
./gen-passwords.sh
mkdir -p ~/.jitsi-meet-cfg/{web,transcripts,prosody/config,prosody/prosody-plugins-custom,jicofo,jvb,jigasi,jibri}
vi .env
docker compose up -d
```

Jitsi shall be available at [`https://localhost:8443`](https://localhost:8443/)
