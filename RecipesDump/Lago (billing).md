Installing Lago, as per [official doc](https://docs.getlago.com/guide/self-hosted/docker) and my notes combined:

```bash
sudo fallocate -l 6G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo "/swapfile    none    swap    sw    0   0" >> /etc/fstab
sudo swapon --show

apt-get install docker-compose-plugin git
wget -O - https://raw.githubusercontent.com/alexander-potemkin/quickies/main/docker_ubuntu.sh | bash

## TODO
Add my docker-compose file here!!!
## TODO

# echo "DATABASE_URL=postgres://" >> .env
echo "LAGO_API_URL=http://host:3000" >> .env # api
echo "LAGO_FRONT_URL=http://host" >> .env # admin
echo "LAGO_RSA_PRIVATE_KEY=\"`openssl genrsa 2048 | base64`\"" >> .env
echo "SECRET_KEY_BASE=\"`openssl rand -hex 64`\"" >> .env
echo "LAGO_ENCRYPTION_DETERMINISTIC_KEY=\"`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1`\"" >> .env
echo "LAGO_ENCRYPTION_KEY_DERIVATION_SALT=\"`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1`\"" >> .env
##
echo "REDIS_PASSWORD=\"`tr -dc 'A-Za-z0-9!?%=' < /dev/urandom | head -c 25`\"" >> .env
echo "LAGO_ENCRYPTION_PRIMARY_KEY=\"`cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 32 | head -n 1`\"" >> .env
vi .env # replace environment variables with your actual values
source .env
docker compose up
docker compose up -d # ports 80 is for web; 3000 for API
```

# install caddy
```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update
sudo apt install caddy
```

`vi /etc/caddy/Caddyfile`:
```/etc/caddy/Caddyfile
{
auto_https disable_redirects
}

billing.example.com {
	reverse_proxy localhost:80
}

api.billing.example.com {
	reverse_proxy localhost:3000
}
```

followed by `service caddy restart`.


In Docker compose:

```bash
mkdir caddy_data caddy_config

```

### Disable registration

`LAGO_DISABLE_SIGNUP=false`


```
admin.billing.example.com {
	reverse_proxy front:80
}

api.billing.example.com {
	reverse_proxy api:3000
}
```