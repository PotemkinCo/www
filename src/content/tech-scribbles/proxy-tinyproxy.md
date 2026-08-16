---
title: "Proxy (tinyproxy)"
---

# Proxy (tinyproxy)

At 2024-03-06 docker commands has been removed, as docker version is seriously out of date.

```bash
apt install -y tinyproxy
chown -R tinyproxy:tinyproxy /var/log/tinyproxy/
vi /etc/tinyproxy/tinyproxy.conf
# XTinyproxy -> No
# BasicAuth $user1 $ $password1
# comment out all 'Allow' to allow all.
service tinyproxy restart
```

Stat: [http://tinyproxy.stats/](http://tinyproxy.stats/)
