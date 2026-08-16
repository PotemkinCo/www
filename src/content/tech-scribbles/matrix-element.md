---
title: "Matrix & Element"
---

**Synapse server health test** [matrix test](https://codeberg.org/spaetz/testmatrix): `uv run --with testmatrix testmatrix matrix.example.com

**Generate signature file**: `docker run --rm --entrypoint="" matrixdotorg/synapse:latest generate_signing_key -o /dev/stdout > ./synapse_signing.key`

**MAS config file**: `docker run ghcr.io/element-hq/matrix-authentication-service config generate > mas_config.yaml`
# Caddy, Synapse, MAS

- [Sample Caddyfile for Synapse and MAS](https://github.com/element-hq/matrix-authentication-service/issues/3614) and a resulting [Caddyfile](https://github.com/rriemann/element-docker-demo/blob/podman-caddy/Caddyfile):
```yaml
	# kate: tab-indents on; tab-width 4; space-indent off;
	{
		acme_ca https://acme-staging-v02.api.letsencrypt.org/directory
		email {$LETS_ENCRYPT_EMAIL}
		# admin off # keep on for healthcheck and graceful reloads
		# local_certs is default option for *.local domains
		# more: https://caddyserver.com/docs/automatic-https#hostname-requirements
		skip_install_trust
		http_port {$CADDY_HTTP_PORT}
		https_port {$CADDY_HTTPS_PORT}
	}
	
	http://{$DOMAIN} {
		root * /srv
	
		# Directives contained in a route block will not be reordered internally.
		route {
			file_server /.well-known/matrix/*
			file_server /.well-known/element/*
			reverse_proxy /.well-known/openid-configuration http://mas:8080
			# redirect with status 301 all other requests to https
			redir https://{host}:{$CADDY_HTTPS_PORT}{uri} permanent
		}
	}
	
	# TODO if redirects for /.well-known/ are permissive, block for http and https can be merged
	
	https://{$DOMAIN} {
		root * /srv
	
		# Directives contained in a route block will not be reordered internally.
		route {
			redir / https://{$ELEMENT_WEB_FQDN}:{$CADDY_HTTPS_PORT} temporary
			file_server /.well-known/matrix/*
			file_server /.well-known/element/*
			reverse_proxy /.well-known/openid-configuration http://mas:8080
		}
	}
	
	{$ELEMENT_WEB_FQDN} {
		reverse_proxy http://element-web:8080
	}
	
	{$ELEMENT_CALL_FQDN} {
		reverse_proxy http://element-call:8080
	}
	
	{$MAS_FQDN} {
		reverse_proxy http://mas:8080
	}
	
	{$LIVEKIT_FQDN} {
		reverse_proxy http://livekit:7880
	}
	
	{$LIVEKIT_JWT_FQDN} {
		reverse_proxy http://livekit-jwt:8080
	}
	
	# for the federation port 8448
	{$HOMESERVER_FQDN}, {$HOMESERVER_FQDN}:8448 {
		request_body {
			max_size 50MB
		}
	
		route {
			# pass auth to MAS
			@mas expression path_regexp('^/_matrix/client/(.*)/(login|logout|refresh)')
			reverse_proxy @mas http://mas:8080
	
			# use the generic worker as a synchrotron:
			# taken from https://element-hq.github.io/synapse/latest/workers.html#synapseappgeneric_worker
			@generic <<CEL
	            path_regexp('^/_matrix/client/(r0|v3)/sync$') ||
	            path_regexp('^/_matrix/client/(api/v1|r0|v3)/events$') ||
	            path_regexp('^/_matrix/client/(api/v1|r0|v3)/initialSync$') ||
	            path_regexp('^/_matrix/client/(api/v1|r0|v3)/rooms/[^/]+/initialSync$')
	        CEL
			reverse_proxy @generic http://synapse-generic-worker-1:8081
	
			reverse_proxy * http://synapse:8008
		}
	}
```

## S3 and media_storage

```bash
sudo chown -R 100990:100990 ../media_store/
```

```bash
cd /data
s3_media_upload update --homeserver-config-path /data/homeserver.yaml /data/media_store/ 0h # but it needs databse port be defined
```


## Cloudron
- after installation - before entering - adjust config
- restart the server
- at well-known domains add full hostname with `:443` port on it

# MAS admin


```bash
alias mas-cli='docker compose run mas_service --config=/config.yaml'
mas-cli manage register-user --yes ubuntu
mas-cli manage set-password admin '<your-password>'
```


*Creating the user*
```bash
pwgen -s 11
mas-cli manage register-user --yes 'test3'
mas-cli manage set-^Cssword test_user '<your-password>'

```

## disabling the user
[ref](https://element-hq.github.io/matrix-authentication-service/reference/cli/manage.html)
```bash
alias mas-cli='docker compose run mas'
mas-cli --config /data/config.yaml doctor
mas-cli --config /data/config.yaml manage lock-user "username" --deactivate
```

## connecting to the MAS database

```bash
sudo docker compose exec -it postgres_mas psql -U user_mas -d mas -h localhost
\d
```

## connecting to the Synapse database
```bash
sudo docker compose exec -it postgres_synapse psql -U user_synapse -d synapse -h localhost
\d
```



# 'Upstream account provider returned ".." as username, which is not linked to that upstream account' - error fix

1. Connect to the database (above)
```sql
SELECT * FROM users WHERE username = 'username';
SELECT user_id FROM upstream_oauth_links WHERE subject='username'; -- if that is empty - that is the root cause  
UPDATE upstream_oauth_links SET user_id='<user-uuid>' WHERE subject='username'; -- user_id == users.user_id
```


## docker compose

Ref / example:
- https://github.com/element-hq/synapse/tree/develop/contrib/docker
- https://github.com/element-hq/element-docker-demo
- https://sspaeth.de/2024/08/tldr-matrix-nextcloud-setup/ - on MAS auth

```yaml
services:

  synapse:
    image: "matrixdotorg/synapse:latest"
    pull_policy: always
    container_name: synapse
    restart: unless-stopped
    volumes:
      - ./data:/data
    ports:
      - 8008:8008
    environment:
      - SYNAPSE_CONFIG_PATH=/data/homeserver.yaml
```

Generating config and user
```bash
	docker compose run --rm -e SYNAPSE_SERVER_NAME=${DOMAIN_NAME} -e SYNAPSE_REPORT_STATS=no synapse generate
	vi data/homeserver.yaml
	sudo docker compose up -d
```


```yaml
server_name: "matrix.example.com"
pid_file: /data/homeserver.pid
listeners:
  - port: 8008
    tls: false
    type: http
    x_forwarded: true
    resources:
      - names: [client, federation]
        compress: false
# database:
#  name: sqlite3
#  args:
#    database: /data/homeserver.db
log_config: "/data/matrix.example.com.log.config"
media_store_path: /data/media_store

federation_domain_whitelist:
federation_ip_range_blacklist:
  - '127.0.0.0/8'
  - '10.0.0.0/8'
  - '172.16.0.0/12'
  - '192.168.0.0/16'
  - '100.64.0.0/10'
  - '169.254.0.0/16'
  - '::1/128'
  - 'fe80::/64'
  - 'fc00::/7'
enable_registration: false
enable_registration_without_verification: true
registration_shared_secret: "..."
federation_domain_whitelist:
  - domain1.example.com
  - dinglewhirl.domain1.example.com
  - domain3.example.com

trusted_key_servers:
  - server_name: "matrix.example.com"
    #trusted_key_servers: []

report_stats: false
macaroon_secret_key: "..."
form_secret: "..."
signing_key_path: "/data/matrix.example.com.signing.key"


# vim:ft=yaml

```


## Migration from Cloudron

Install Caddy as per caddy web servr

### Synapse

- Adjust DNS's entries lifetime to 60 seconds (to speed up DNS propogation)
	- for `@` record
	- for `auth` record as well!
- Roll-out caddy & element using docker compose files
- Using `env | grep -i postgre` from Cloudron get and copy-paste user & password (in both environment & healt-check cmd)
- Prepare: using filemanager 
	- copy `homeserver.yaml` over
	- copy `signing.key` (!)
	- check `log.config` (optional)
	- `sudo rm data/signing.key`
	- `sudo mv matrix.log.config log.config`
	- at `homeserver.yaml` change:
		- database:
			- user & password -> move from the config to the compose file
			- host -> synapse_db from compose file
		- email: smtp_host to FQDN, smtp_port to 25 (require_transport_security -> True?)
		- `signing_key_path` => '/data'
		- `media_store_path` => '/data'
		- `log_config` => '/data'

- PostgreSQL dump ([ref](https://docs.cloudron.io/guides/import-postgresql/#dump)):
	- `PGPASSWORD=${CLOUDRON_POSTGRESQL_PASSWORD} pg_dump --no-owner --no-privileges --username=${CLOUDRON_POSTGRESQL_USERNAME} --host=${CLOUDRON_POSTGRESQL_HOST} ${CLOUDRON_POSTGRESQL_DATABASE} > /tmp/pgdump.sql` from the Synapse's console -> `cd /tmp && gzip -9 pgdump.sql` (compress twice)-> 'Download' -> `sftp` to the server

> [!NOTE] PostgreSQL dump has to be done on running app. media_store has to be downloaded on shutdown app.

	- `mkdir data/db_synapse data/db_mas`
	- `docker compose up -d db_synapse`
	- `sudo mv pgdump.sql data/db_synapse`
	- `docker exec -it $(docker compose ps -q db_synapse) /bin/bash`
	- `psql --set ON_ERROR_STOP=on -U synapse_user synapse < /var/lib/postgresql/data/pgdump.sql`
	- `exit`
	- `sudo rm data/postgresql/pgdump.sql`
	- `docker compose restart`
	- `docker compose up -d`

- MAS migration
	- `docker compose run mas config generate > data/mas/config.yaml`
	- `docker compose run mas config check --config=/data/config.yaml`
	- `alias syn2mas='docker compose run syn2mas'`
	- `syn2mas --command advisor --synapseConfigFile /homeserver.yaml`
	- Configure OpenID on Cloudron (MAS [doc](https://element-hq.github.io/matrix-authentication-service/setup/sso.html#general-configuration), Cloudron doc)
		- go to https://my.example.com/#/user-directory
		- create new with callback URL: `https://auth.example.com/upstream/callback/$ULID`
		- take clientID and clientSecret -> add them to the upstream provider
	- `sudo vi ./data/mas/config.yaml`
		- add client
		- upstream_oauth2
			- [ULID generator](https://ulidgenerator.com/)
		- change public_base & issuer: `https://auth.example.com/`
		- adjust database - remove URL, add
		  !Note: password 81 is Ok, no more!
```yaml
			  host: mas_db
			  port: 5432
			  username: user_mas
			  password: $pass$
			  database: mas
```
		- disable passwords ??
			- disable `passwords`->`enabled` - to disable passwords auth 
		- change matrix 
			- MAS's `matrix:secret` == Synapse's `registration_shared_secret`
	- `docker compose run mas config sync --prune --config=/data/config.yaml`
	- `syn2mas --command migrate --synapseConfigFile /homeserver.yaml --masConfigFile /mas.yaml --upstreamProviderMapping oidc-provider:<provider-id> --dryRun` -> `upstream_oauth2:providers:id`
	- `docker compose down`
	- `docker compose up db_synapse db_mas -d`
	- `syn2mas --command migrate --synapseConfigFile /homeserver.yaml --masConfigFile /mas.yaml --upstreamProviderMapping oidc-provider:<provider-id> --dryRun false`
	- add the following lines to Synapse server config:
```yaml
experimental_features:
  msc3861:
    enabled: true
    issuer: http://auth.example.com/
    # Matches the `client_id` in the MAS config
    client_id: 00000000000000000SYNAPSE00
    # Matches the `client_auth_method` in the MAS config
    client_auth_method: client_secret_basic
    # Matches the `client_secret` in the MAS config
    client_secret: <client-secret>
    # Matches the `matrix.secret` in the MAS config
    admin_token: <admin-token>
```
	- disable `password_config` & `oidc_providers` in Synapse
- Caddy
	- add to `sites/`
	- add network to `docker-compose.yml` at Caddy
- `docker compose up -d`
- `docker compose run mas doctor --config=/data/config.yaml`
- try ([ref](https://element-hq.github.io/matrix-authentication-service/setup/))
	- https://example.com/.well-known/matrix/client
	- https://auth.example.com/.well-known/openid-configuration
	- https://auth.domain.com

ToDo:
- [ ] test what is the impact of [e2e keys cleanup](https://element-hq.github.io/synapse/latest/usage/administration/backups.html#synapse-specfic-details)
- [ ] setup backup script (as [per](https://element-hq.github.io/synapse/latest/usage/administration/backups.html#quick-and-easy-database-backup-and-restore))

## MAS

`test: ["CMD", "mas-cli", "--config", "/data/config.yaml", "doctor"]` is a working health-check string

NextCloud & MAS doc: https://sspaeth.de/2024/08/tldr-matrix-nextcloud-setup/
Docs - https://github.com/element-hq/matrix-authentication-service/tree/main/docs
Docker reference: https://github.com/element-hq/matrix-authentication-service/issues/2912
Config reference: https://github.com/element-hq/matrix-authentication-service/blob/main/docs/reference/configuration.md
Dedicated guide on SSO: https://github.com/element-hq/matrix-authentication-service/blob/main/docs/setup/sso.md#sample-configurations
Migration guide: https://github.com/spantaleev/matrix-docker-ansible-deploy/blob/master/docs/configuring-playbook-matrix-authentication-service.md#configuring-upstream-oidc-provider-mapping-for-syn2mas

Docker way:
```bash
mkdir -p ./data/mas
docker run ghcr.io/element-hq/matrix-authentication-service config generate > ./data/mas/config.yaml
```

### Troubleshooting
Docker compose troubleshooting:
```bash
docker compose run mas doctor --config=/data/config.yaml
```

- https://auth.domain.com shall work without errors


## Users in MAS

```bash
mas-cli --config=/data/config.yaml manage register-user --yes ag
mas-cli --config=/data/config.yaml manage set-password ag '...'
```
## Federation

Tester tool: https://federationtester.matrix.org/
Reverse proxy configuration for well-known handler: https://github.com/matrix-org/synapse/blob/develop/docs/reverse_proxy.md (specific for [Caddy](https://github.com/matrix-org/synapse/blob/develop/docs/reverse_proxy.md#caddy-v2)); the docs are [here](https://github.com/spantaleev/matrix-docker-ansible-deploy/blob/master/docs/configuring-well-known.md).

```bash
uimblor.at.nocloud.today {
        import logging matrix.example.com
        header /.well-known/matrix/* Content-Type application/json
        header /.well-known/matrix/* Access-Control-Allow-Origin *
        respond /.well-known/matrix/server `{"m.server": "matrix.example.com:443"}`
        #respond /.well-known/matrix/client `{"m.homeserver":{"base_url":"https://matrix.example.com"},"m.identity_server":{"base_url":"https://identity.example.com"}}`
        respond /.well-known/matrix/client `{"m.homeserver":{"base_url":"https://matrix.example.com:443"},"im.vector.riot.jitsi":{"preferredDomain":"meet.example.com"}}`
        reverse_proxy /_matrix/* synapse:8008
}
```

### Troubleshooting
```bash
nc -vv domain.name 443
docker compose restart synapse
```

Synapse servers has to be restarted in order to pick up connectivity and deliver messages.

## Trusted key server info

`trusted_key_servers` - https://matrix.org/blog/2019/06/30/tightening-up-privacy-in-matrix/
Notary servers.
Some useful info on that: https://github.com/matrix-org/synapse/issues/7047

## Install web admin

For a SQlite install:
```bash
sqlite3 homeserver.db
UPDATE users SET admin=1 WHERE name='@ubuntu:matrix.example.com'
select name, admin from users; # to check
```


### enable user as admin - open console on Synapse container:
With MAS it seems:

as [per](https://github.com/Awesome-Technologies/synapse-admin/issues/429)
```bash
alias mas-cli='docker compose run mas'
mas-cli --config /data/config.yaml manage issue-compatibility-token --yes-i-want-to-grant-synapse-admin-privileges ubuntu
```

```bash
PGPASSWORD=${CLOUDRON_POSTGRESQL_PASSWORD} psql -h ${CLOUDRON_POSTGRESQL_HOST} -p ${CLOUDRON_POSTGRESQL_PORT} -U ${CLOUDRON_POSTGRESQL_USERNAME} -d ${CLOUDRON_POSTGRESQL_DATABASE} -c "UPDATE users SET admin=1 WHERE name='@admin:matrix.example.com'"
```

- install surfer on cloudron
- download [latest release](https://github.com/Awesome-Technologies/synapse-admin/releases/) - dirty format
- extract it and place on the web server
- Ready

"Your session has ended, please reconnect. " error most probably means that user is not admin (SQL steps is missed).

## Adjust files limits
It's ~50Mb by default.

```yaml
max_upload_size: 100M 
```

Probably could make sense to put it just below `media_store_path` to keep things in one place. [ref](https://github.com/matrix-org/synapse/blob/develop/docker/conf/homeserver.yaml).


### Generating new user

docker exec -it synapse register_new_matrix_user http://localhost:8008 -c /data/homeserver.yaml

## Print sessions info
```bash
matrix-commander --devices # shows list of what is called 'sessions' in GUI

```
Just in case: inactive sessions, older than 90 days could get marked as unverified, probably - by a server or the protocol.

## Get token for the user
Only works if login & password auth enabled. Otherwise, use `matrix-commander --login sso` followed by `matrix-commander --verify`:

```bash
curl -XPOST -d '{"type": "m.login.password", "identifier": {"user": "monitoring.bot", "type": "m.id.user"}, "password": "<reducted>"}' "https://domain1.example.com/_matrix/client/r0/login"
```


## Disable federation
Add / verify server config contains the following:
```bash
allow_public_rooms_without_auth: false
allow_public_rooms_over_federation: false
trusted_key_servers:
  - server_name: ""
```


## URL to open custom domain
(from Notes):
`https://app.element.io/register/?hs_url=domain.com` - Android & iOS
`https://mobile.element.io/?hs_url=https://domain.com` - iOS only

On Android side can check which URLs are registered on the app (as [per](https://github.com/element-hq/element-android/issues/5748)).

> [!NOTE] NOTE `https://` in `hs_url` parameter!

[^1]:
