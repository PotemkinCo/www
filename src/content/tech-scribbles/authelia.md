---
title: "Authelia"
---

```bash
yamllint configuration.yml

openssl rand -hex 512 # to generate random string

docker run -it docker.io/authelia/authelia:latest authelia crypto hash generate argon2 # edit the users_database.yml file. Replace the HASHPASS string with the hashed password

# validate
docker run --rm -v ./authelia/configuration.yml:/config/configuration.yml:ro docker.io/authelia/authelia:latest authelia config validate

# generates ssl private certitifate
openssl genrsa -out rsa.2048.key 2048
```

## Create new user

```bash
user:
	password: $argon2id$v=19$m=65536,t=3,p=4$<argon2_hash>
	displayname: ...
	email: user@server.com

```

Let user reset password via https://auth.example.com/reset-password/step1
