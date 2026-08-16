---
title: "livekit & coturn"
---

Some information is at *2025-05-02* and *2025-05-01*

Guide: https://docs.livekit.io/home/self-hosting/vm/

Test functionality: https://livekit.io/connection-test
# Quick-start

```bash
docker pull livekit/generate
docker run --rm -it -v./livekit_generated:/output livekit/generate
```


For LiveKit:

```bash
echo "* soft nofile 2048" > /etc/security/limits.d/10-livekit.conf
echo "vm.overcommit_memory = 1" > /etc/sysctl.d/90-redis.conf
service procps force-reload
```

# Get token

```bash
python3 -m venv env
source env/bin/activate
pip install livekit-api
export LIVEKIT_API_KEY=<your-api-key>
export LIVEKIT_API_SECRET=<your-api-secret>
python livekit_token.py
```

```python
import os
from livekit import api

token = api.AccessToken(os.getenv('LIVEKIT_API_KEY'), os.getenv('LIVEKIT_API_SECRET')) \
  .with_identity("identity") \
  .with_name("my name") \
  .with_grants(api.VideoGrants(
      room_join=True,
      room="test",
  ))

print(token.to_jwt())
```
# CLI

```bash
curl -sSL https://get.livekit.io/cli | bash
export LIVEKIT_URL="https://livekit.example.com"
export LIVEKIT_API_KEY=<your-api-key>
export LIVEKIT_API_SECRET=<your-api-secret>
```

# Check configuration

https://livekit.io/connection-test -> takes `wss://` with domain name and room token (the one - comes from `generate` script)


# coturn

there is a [turnadmin tool](https://github.com/coturn/coturn/blob/master/README.turnadmin) to create users; sqlite (`userdb=/var/db/turndb` in [config](https://github.com/coturn/coturn/blob/master/docker/coturn/turnserver.conf))

/> 128 symbols password [advised](https://medium.com/l7mp-technologies/lets-talk-about-turn-authentication-c2767514bc0c)
