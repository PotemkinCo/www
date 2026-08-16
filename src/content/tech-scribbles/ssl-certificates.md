---
title: "SSL certificates"
---

# ACME-DNS - free \*.domain.com certificate

as resolved *2026-03-21*:

```bash
# Create DNS records on dns.example.com:
# NS: auth.acme-dns.agent => auth.acme-dns.agent.example.com.
# A: auth.acme-dns.agent => <server-ip>
sudo pkg install acme.sh jq
sudo su - acme -c bash

# enable registration temprarily
curl -X POST "https://auth.acme-dns.agent.example.com/register" \
     -H "Content-Type: application/json" \
     -d '{"allowfrom": []}' | tee acme-dns_response.json

DOMAIN="example.com" 
     
eval "$(jq -r '
  "export ACMEDNS_BASE_URL=https://auth.acme-dns.agent.example.com",
  @sh "export ACMEDNS_USERNAME=\(.username)",
  @sh "export ACMEDNS_PASSWORD=\(.password)",
  @sh "export ACMEDNS_SUBDOMAIN=\(.subdomain)",
  @sh "export ACMEDNS_FULLDOMAIN=\(.fulldomain)"
' acme-dns_response.json)"

echo "Create CNAME: _acme-challenge => $ACMEDNS_FULLDOMAIN" 
     
acme.sh --set-default-ca --server letsencrypt # to avoid providing e-mails
env | grep ACMEDNS_
acme.sh --issue -d "*.$DOMAIN" -d "$DOMAIN" --dns dns_acmedns

(crontab -l 2>/dev/null; echo "$((RANDOM % 60)) $((RANDOM % 4 + 2)) * * * /usr/local/sbin/acme.sh --cron --home \"/var/db/acme/.acme.sh\" > /dev/null") | crontab -
```

in haproxy.conf - make sure the `stats socket /var/run/haproxy/admin.sock mode 660 level admin group acme` line is there 

# WildCard paid certificate from SSLs.com

Resulting files explanation:
- `.ca-bundle` => CA bundle, aka intermediate certificate
- `.co.crt` => leaf certificate
- `_key.txt` => *private* key
- `*.p7b` => PKCS#7 format, used mostly on Windows / IIS (ignore it)

So, to create one file ([ref](https://www.ssls.com/knowledgebase/how-to-install-an-ssl-certificate-on-a-nginx-server/)) that is required by web servers:
```bash
unzip STAR.*_cert.zip
unzip STAR.*_key.zip
openssl x509 -noout -text -in STAR*.crt | grep 'Subject: CN' # should have domain name
openssl x509 -noout -text -in STAR*.ca-bundle | grep 'CA:TRUE' # should be CA:TRUE
cat STAR*.crt > ssl-complete-bundle.crt && echo >> ssl-complete-bundle.crt && cat STAR*.ca-bundle >> ssl-complete-bundle.crt
grep BEGIN ssl-complete-bundle.crt | wc -l # should be 3
openssl x509 -noout -in ssl-complete-bundle.crt -checkhost test.`basename STAR*.crt | sed -E 's/^STAR\.([^.]+(\.[^.]+)?)\.crt$/\1/'`
```


> [!NOTE] openssl on a concatenated file won't show it all
> `openssl x509 -noout -text -in ssl-complete-bundle.crt` will only show first certificate and stop there.


Check if *local* certificate is correct:
```bash
openssl x509 -noout -text -in file.crt
```

Check if *installed* certificate is correct:
```bash
openssl s_client -showcerts -connect site:443

openssl s_client -showcerts -connect 1.2.3.4:443 -servername site.com # to connect via different IP address
```

> [!NOTE] Intermediate certificate is missing at this moment.
> Proper way: get it from somewhere...
> Fast way: go to [decoder.link](https://decoder.link/), check your SSL - get bundle for nginx and provide it to the server.

Chain of the ssls.com certificates is supposed to work like that:
1. Leaf Certificate # 1 - `*.domain.com`
2. Intermediate certificate # 2 - Common Name: Sectigo RSA Domain Validation Secure Server CA
3. Certificate # 3 - Common Name: USERTrust RSA Certification Authority


# Intermediate certificates chain

If missing - here is a possible tool: https://github.com/jdmansour/fetch-intermediate-certs
Explanation on why they are requiered: https://www.reddit.com/r/ComputerSecurity/comments/14a2by3/why_do_we_really_need_intermediate_certificates/

# Check ssl certificate

```bash
openssl s_client -connect hostname:443 -showcerts # server
openssl x509 -in certificate.pem -text # local
```

```bash
openssl x509 -noout -modulus -in /etc/pki/ejabberd/certs/XXX.XXXX.de.fullchain.pem | openssl md5
(stdin)= 942c68d45666c4e59fd351f5c24da5ad

openssl x509 -noout -modulus -in /etc/pki/ejabberd/certs/XXX.XXXX.de.cert.pem | openssl md5
(stdin)= 942c68d45666c4e59fd351f5c24da5ad

openssl rsa -noout -modulus -in /etc/pki/ejabberd/private/XXX.XXXX.de.key.pem | openssl md5
(stdin)= 942c68d45666c4e59fd351f5c24da5ad
```

# nginx & certbot

Quite a nice DigitalOcean doc is [here](https://www.digitalocean.com/community/tutorials/how-to-secure-nginx-with-let-s-encrypt-on-ubuntu-18-04).

```bash
sudo nginx -t #check configuration file
sudo systemctl reload nginx #nginx to reread configuration changes; if problems - see below
sudo apt install python3-certbot-nginx
sudo certbot --nginx -d DNS_NAME_1 -d DNS_NAME_2 #certbot SSL certificate configuration
sudo certbot renew --dry-run #check how certificate renewal would work
systemctl list-timers #check if certbot will renew via system
crontab -l #check crontab
```

One more instruction: [https://certbot.eff.org/instructions?ws=nginx&os=ubuntu-18](https://certbot.eff.org/instructions?ws=nginx&os=ubuntu-18)

**certbot force renewal:**

```bash
certbot renew --force-renewal
```

## Troubleshooting

Check existing certificates:
```bash
certbot certificates
```

Delete some of them with `certbot delete`

Let's Encrypt certbot do configuration files backup, before any changes, that could be found at `/var/lib/letsencrypt/backups/`  (VERY handy when nginx stops working after certbot changes)

certbot commands and reference: [https://certbot.eff.org/docs/using.html#managing-certificates](https://certbot.eff.org/docs/using.html#managing-certificates)

Troubleshooting commands here: https://serverfault.com/questions/1151156/verify-return-code-21-unable-to-verify-the-first-certificate and here: https://unix.stackexchange.com/questions/198810/unable-to-locally-verify-the-issuers-authority


# Archive
## certbot wildcard certificate

Wildcard certificate works **only** with DNS challenge.
For this challenge to work, certbot plugin is required, which will perform DNS manipulations to satisfy the challenge.

## Hexonet
[https://gist.github.com/gfdsa/f35272ec22277412068f96e6dc13cac3](https://gist.github.com/gfdsa/f35272ec22277412068f96e6dc13cac3)

To be executed for DNS challenge as per [certbot doc](https://eff-certbot.readthedocs.io/en/stable/using.html#pre-and-post-validation-hooks):

```bash
export DOMAIN_NAME =
git clone https://github.com/retailify/ispapi.git
cp ispapi # remain there for the rest of the steps
vi setup.py
# s/setuptools/distutils.core as per https://stackoverflow.com/a/57707235/2188026
# remove packages
pip install ispapi
vi hexonet.py # put plugin content there, replacing name & password
sudo apt install certbot
sudo certbot certonly --manual --preferred-challenges=dns --manual-auth-hook /home/user/ispapi/hexonet.py --manual-cleanup-hook /home/user/ispapi/hexonet.py -d $DOMAIN_NAME -d \*.$DOMAIN_NAME
sudo certbot certificates # check the domains are as expected
```

add `0 0 * * 0 /home/user/ssl_renew.sh` cron with the following script:
```bash
#!/bin/bash
cd /home/user/ispapi #python environment is there
sudo certbot renew --preferred-challenges=dns --manual-auth-hook /home/user/ispapi/hexonet.py --manual-cleanup-hook /home/user/ispapi/hexonet.py
```

## Gandi

 [Gandi certbot plugin](https://github.com/obynio/certbot-plugin-gandi )

```bash
export DOMAIN_NAME =
sudo pip install certbot-plugin-gandi

sudo tee -a /etc/letsencrypt/gandi.ini > /dev/null <<EOT
# live dns v5 api key
dns_gandi_api_key=APIKEY

# optional organization id, remove it if not used
# dns_gandi_sharing_id=SHARINGID
EOT

sudo chmod 600 /etc/letsencrypt/gandi.ini

sudo certbot certonly --authenticator dns-gandi --dns-gandi-credentials /etc/letsencrypt/gandi.ini --server https://acme-v02.api.letsencrypt.org/directory -d $DOMAIN_NAME -d \*.$DOMAIN_NAME

sudo certbot certificates # check the domains are as expected
```

Create `ssl_renew.sh` script (as per [this doc](https://github.com/obynio/certbot-plugin-gandi)):
```bash
#!/bin/bash
sudo certbot renew -q --authenticator dns-gandi --dns-gandi-credentials /etc/letsencrypt/gandi/gandi.ini --server https://acme-v02.api.letsencrypt.org/directory
```

Then add it to cron with `crontab -e`

 `0 0 * * 0 /home/user/ssl_renew.sh` 


## non-API DNS provider (no certbot plugin)
If your provider doesn't provide certbot plugin, you can 'redirect' a specific subdomain to the provider who support it – could be Digital Ocean.

Here are the (not yet tested) steps to make it work:
-   create a DNS zone acme.MyDomain.com at DO
-   create 3 NS records at DeprecatedDNS provider for acme.MyDomain.com to point to ns1,2,3.digitalocean.com
- create CNAME at DeprecatedDNS provider for _acme-challenge.MyDomain.com that points to _acme-challenge.acme.MyDomain.com
-   use certbot digital ocean plugin, as described [here](https://www.digitalocean.com/community/tutorials/how-to-acquire-a-let-s-encrypt-certificate-using-dns-validation-with-certbot-dns-digitalocean-on-ubuntu-20-04)
-   pray, it should work
