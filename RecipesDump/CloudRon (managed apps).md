Много полезных заметок про переезд - [[2023-07-17]] и в датах вокруг.
Много полезных заметок про рутинный сетап в [[2023-07-26]]

### Install
```bash
wget https://cloudron.io/cloudron-setup && chmod +x ./cloudron-setup && sudo ./cloudron-setup
```

And here is a command if you wish to setup some specific version:
```bash
wget https://cloudron.io/cloudron-setup
chmod +x ./cloudron-setup
./cloudron-setup --version 8.3.2
```


> [!NOTE] SSH custom port
> Note, that Cloudron's firewall only have 'holes' for SSHD on 22 or 202 port.


It will take some time (10-30 minutes, depending on the server speed).

Then process to the [https://server_ip](https://server_ip) for further web based setup (in Chrome type `thisisunsafe` to proceed through SSL certificate warning).

## Fix AppStore access behind strict firewall


> [!NOTE] DNS configuration in case of strict firewall
> In case of strict firewall (like on UpCloud) follow the instructions below to configure unbound DNS, otherwise DNS resolution will fail, and hence Cloudron web admin page won't work. Refer to [[2023-07-15]] for the history.

To reconfigure Unbound server under a strict firewall environment ([as it tries to reach directly to the root servers](https://forum.netgate.com/topic/103322/solved-which-dns-servers-does-unbound-use/2?_=1689447709227&lang=en-GB) ), define your DNS servers at `/etc/unbound/unbound.conf.d/private-dns.conf`:
```
# this disables DNSSEC
server:
    val-permissive-mode: yes
    
# forward all queries to the internal DNS
forward-zone:
    name: "."
    forward-addr: 1.1.1.1
    forward-addr: 8.8.8.8
```
Followed by:
```
systemctl restart unbound
host www.cloudron.io 127.0.0.1
```


### For manual DNS management

Manual DNS management is not a problem - **use wildcard**  - it requires 3 things to do/consider:

1. Create A type record for * and for [hostname.domain.com](http://hostname.domain.com) to IP address, which usually requires hostname ⇒ IP address type record (without domain.com)
2. Creating same kind of record with `my` at the beggining: `my.hostname` ⇒ IP address
3. Direct A record for every app that is installed (the app will give a hint)

### To get embedded turn credentials
`env | grep CLOUDRON_TURN` inside TURN enabled app, as per this [forum thread](https://forum.cloudron.io/topic/2467/how-to-use-cloudron-s-coturn-server-with-non-cloudron-apps). 

## Mail setup

E-mail relay is required to deliver mails to Google & Microsoft. From the [forum threads](https://forum.cloudron.io/topic/5268/e-mail-relay-service-recommendation/2) it seems, that [ElasticMail](https://elasticemail.com/email-api-pricing) and [PostMark](https://postmarkapp.com/pricing) are the best options. Both configured via [Web UI](https://docs.cloudron.io/email/#relay-outbound-mails) for e-mail relay.

### Moving mailbox
([ref](https://forum.cloudron.io/topic/9706/move-e-mail-mailbox-data-to-a-mounted-disk/4))
```bash
systemctl stop|start docker docker.socket postgresql mysql nginx
rsync --archive /mnt/old_root/home/yellowtent/boxdata /mnt/data/cloudron-mail/
find /home/yellowtent/boxdata/ -type f -printf "." | wc -c
find /mnt/data/cloudron-mail/boxdata/ -type f -printf "." | wc -c
diff -r -q /home/yellowtent/boxdata /mnt/data/cloudron-mail/boxdata
```


## Change linked account for the instance

As per [the doc](https://docs.cloudron.io/appstore/#change-associated-account).

ssh to the server, execute:

```bash
mysql -uroot -ppassword -e "DELETE FROM box.settings WHERE name='cloudron_token';"
```

Then login to the AppStore under the account, that needs to be linked. That's it.


# Manual wildcard SSL certificate injection (for acme.sh, for example)

Ref - [[2026-03-26]] notes, here is a recipy:

```bash
sudo su - acme -c bash
DOMAIN="domain.net"
TOKEN="..."
cd /var/db/acme/certs/*.${DOMAIN}_ecc

CERT=$(awk 'NF {printf "%s\\n", $0}' fullchain.cer)
KEY=$(awk 'NF {printf "%s\\n", $0}' "*.${DOMAIN}.key")

curl -X POST "https://my.${DOMAIN}/api/v1/domains/${DOMAIN}/config" \
-H "Authorization: Bearer $TOKEN" \
-H "Content-Type: application/json" \
-d "{
\"zoneName\": \"${DOMAIN}\",
\"provider\": \"manual\",
\"config\": {},
\"tlsConfig\": { \"provider\": \"fallback\" },
\"fallbackCertificate\": { \"cert\": \"${CERT}\", \"key\": \"${KEY}\" }
}"
```

verify with

```bash
openssl s_client -showcerts -connect 192.168.9.10:443 -servername my.${DOMAIN}.net
```

## Automated HTTPS certificated update

As per this [forum thread](https://forum.cloudron.io/topic/5648/update-domain-names-with-the-cli-yet-another-topic/11); updated 2023-09-18 as per my findings on the new API change.

```bash
#!/bin/bash
set -e
#set -x

dns_host_name=''
token=''

echo "Bringing firewall down"
/root/firewall_down.sh

taskId=`curl -k -X POST -H 'Content-Type: application/json' -H "authorization: Bearer $token" --data '{}' https://$dns_host_name/api/v1/reverseproxy/renew_certs 2>/dev/null | jq -r '.taskId'`

echo "Renewal task log /home/yellowtent/platformdata/logs/tasks/$taskId.log"

echo
echo "Giving it time to work things out..."
sleep 120

echo "Bringing firewall back up"
/root/firewall_up.sh
```

Firewall up & down for route based 'firewalling':
```bash
# Up
sudo netstat -nr 
sudo route add default gw `sipcalc -I ens3 -i | grep "Usable range" | cut -d "-" -f 2 | xargs` ens3
sudo route del default gw 192.168.168.1 ens4
sudo netstat -nr

# Down
sudo route add default gw 192.168.168.1 ens4
sudo route del default gw `sipcalc -I ens3 -i | grep "Usable range" | cut -d "-" -f 2 | xargs` ens3
sudo netstat -nr
```

Could add it to the cron monitoring

```bash
@weekly https_certs_update.sh >> https_certs_update.log 2>&1
```

# LDAP sync

```bash
curl 'https://my.intra.example.com/api/v1/external_ldap/sync' \
-X 'POST' \
-H 'Content-Type: application/json;charset=utf-8' \
-H 'Accept: application/json, text/plain, */*' \
-H 'Authorization: Bearer <your-bearer-token>' \
-H 'Sec-Fetch-Site: same-origin' \
-H 'Accept-Language: en-GB,en;q=0.9' \
-H 'Accept-Encoding: gzip, deflate, br' \
-H 'Sec-Fetch-Mode: cors' \
-H 'Host: my.intra.example.com' \
-H 'Origin: https://my.intra.example.com' \
-H 'Content-Length: 2' \
-H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15' \
-H 'Referer: https://my.intra.example.com/' \
-H 'Connection: keep-alive' \
-H 'Sec-Fetch-Dest: empty' \
--data-binary '{}'
```

# Troubleshooting

## Recovering from backup
[ref](https://docs.cloudron.io/guides/decrypt-backups/)
	```bash
	sudo npm install -g cloudron
	cloudron backup decrypt --password=passphrase backupid.tar.gz.enc backupid.tar.gz	
	tar xzf *.tar.gz
	cd vmail
	docker stop mail
	mail email /home/yellowtent/boxdata/mail/vmail/
	# verify permissions and do chmod -R 1000:1000 
	docker start mail
```

## Firewall issues
```bash
systemctl restart cloudron-firewall # to restart script
journalctl -u cloudron-firewall -fa # to see the logs
view /home/yellowtent/box/setup/start/cloudron-firewall.sh # to see the script
cat /home/yellowtent/platformdata/firewall/ldap_allowlist.txt # to check LDAP whitelist file
```
## LDAP

The ldap logs can be enabled by editing `/etc/systemd/system/box.service`.
There is a part that says "-box:ldap" . Just remove the "-".
Then:
```
systemctl daemon-reload
systemctl restart box
```
Look into box.log (and not nginx logs). You will see LDAP traces.

LDAP actual server is running on port 3004 (636 forward to 3004 via iptables).

If LDAP doesn't work, login with `cloudron-support --admin-login` password.

## Admin's one time password

```bash
cloudron-support --admin-login
```
## Enable remote access
Add ssh keys to `/home/cloudron-support/.ssh/authorized_keys` with `cloudron-support --enable-ssh`

## Emails issue

Login failures are in the dovecot logs. You can see "/run/dovecot/dovecot.log" in the mail container (docker exec -ti mail /bin/bash). This is currently not exposed in the Cloudron dashboard. In any case, it will only report if login worked or not, it will hard to make out why it failed.

## Update failure

In case if Cloudron failed during the update process:
> Overall it is safe to run **/home/yellowtent/box/setup/start.sh** in such cases which can be run again and again ensuring dependencies and also failing if it can't <...> giving the option to fix things and re-run it.

## Remove 2FA for admin user

As per the [doc](https://forum.cloudron.io/topic/5794/how-to-reset-2fa-for-admin): ssh to the server and execute:

```bash
#display the current status
mysql -uroot -ppassword -e "select username, email, resetToken, twoFactorAuthenticationSecret, twoFactorAuthenticationEnabled from box.users";

#reset the 2FA
mysql -uroot -ppassword -e "UPDATE box.users set twoFactorAuthenticationEnabled=0 where username='admin'";
```

Two factor auth reset for admin: [http://forum.cloudron.io/topic/5794/how-to-reset-2fa-for-admin](http://forum.cloudron.io/topic/5794/how-to-reset-2fa-for-admin)

# How to send e-mail via CloudRon

```bash
docker inspect --format '{{ .NetworkSettings.Networks.cloudron.IPAddress }}' mail #gives IP address
docker inspect --format '{{ .Config.Env }}' mail | tr ' ' '\n' | grep CLOUDRON_RELAY_TOKEN | sed 's/^.*=//' #gives token

```

```bash
swaks -s `docker inspect --format '{{ .NetworkSettings.Networks.cloudron.IPAddress }}' mail` -p 2525 --au user@domain.com --ap `docker inspect --format '{{ .Config.Env }}' mail | tr ' ' '\n' | grep CLOUDRON_RELAY_TOKEN | sed 's/^.*=//'` -f 'user@domain.com' -t 'user@domain.com' --h-Subject "Test mail"
```


### Command line app install
as per https://docs.cloudron.io/packaging/tutorial/#update

```bash
npx cloudron login my.domain.com
wget https://raw.githubusercontent.com/GetZenDev/build-openfire-docker/main/CloudronManifest.json
npx cloudron install --image getzendev/openfire:latest
```

to update:
```bash
export DOMAIN_NAME=mydomain.com
wget https://raw.githubusercontent.com/GetZenDev/build-openfire-docker/main/CloudronManifest.json
npx cloudron status --app $DOMAIN_NAME
npx cloudron update --image getzendev/openfire:latest --app $DOMAIN_NAME
npx cloudron status --app $DOMAIN_NAME
```

# Various
SSL certificates are stored at the host Linux at ` /home/yellowtent/platformdata/nginx/cert/`

Unsend mail is stored at unsend mail is stored at `/home/yellowtent/boxdata/mail/haraka-queue`

Dump all users and passwords with salt:
`mysql -uroot -ppassword box -e "select username,password,salt from users;" > users.list`