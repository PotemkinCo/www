## Install

[Ref](https://learn.netdata.cloud/docs/netdata-agent/installation/linux)

```bash
wget -O /tmp/netdata-kickstart.sh https://get.netdata.cloud/kickstart.sh && sh /tmp/netdata-kickstart.sh --stable-channel --disable-telemetry
netdatacli dumpconfig > /etc/netdata/netdata.conf
vi /etc/netdata/netdata.conf # [web]->bind to -> 127.0.0.1
systemctl restart netdata
ss -tulnp | grep 19999 # verify it's 127.0.0.1 indeed
```

## Agregate logs

[Ref](https://learn.netdata.cloud/docs/observability-centralization-points/metrics-centralization-points/configuring-metrics-centralization-points)
on parent:

```bash
cd /etc/netdata 2>/dev/null || cd /opt/netdata/etc/netdata  
sudo ./edit-config --editor vim stream.conf
# search for API_KEY string and replace it with output of `uuidgen`, change to `enabled = yes`
cd ssl
openssl req -newkey rsa:2048 -nodes -sha512 -x509 -days 365 -keyout key.pem -out cert.pem
cd ..
chmod -R 777 ssl
sudo ./edit-config --editor vim netdata.conf
# in [web] - uncomment ssl key & ssl certificate, port
systemctl restart netdata
```

on children:

```bash
cd /etc/netdata 2>/dev/null || cd /opt/netdata/etc/netdata  
sudo ./edit-config --editor vim stream.conf
# at the top - pick up `stream` section, `enabled = yes`, `destination = PARENT_IP_ADDRESS:19999`, `api key = API_KEY`
systemctl restart netdata
```
# Use

to work-around cloud invitation screen, use `/v3` URL
# Troubleshooting

- `openssl s_client -connect <parent-ip>:19999 -showcerts` -> ssl connection issues
- `journalctl -f --namespace=netdata MESSAGE_ID=6e2e3839067648968b646045dbf28d66` connection issues
- verify permissions are Ok

