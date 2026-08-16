---
title: "rclone"
---

# Install

```bash
sudo snap install rclone
# OR
curl https://rclone.org/install.sh | sudo bash
```


Some more examples are at *2024-02-03*.

<aside>
💡 Important: make sure there is always a semicolon `:` after endpoint, even if it's crypted - otherwise rclone will think it's working with local file system.

</aside>

```bash
curl https://rclone.org/install.sh | sudo bash
rclone --version
sudo rclone selfupdate #update rclone
rclone config #to create source and destination
rclone lsd point_name:bucket_name #show bucket folders
rclone sync old:mattermost-files new:mattermost-files
rclone copy ${FILE} endpoint: #for one file
```

add `-vv --dump responses --retries 1` for debugging

```bash
rclone listremotes
```

To **decrypt** files - just reverse the command and provide destination to recover:

```bash
rclone sync enc_mis_files_backup_s3: /tmp/mis_dec -vv
```

# S3 proxy



```yaml
  rclone:
    image: "rclone/rclone:latest"
    container_name: rclone
    restart: unless-stopped
    command: >
      --log-level DEBUG
      serve s3 enc_pitr-backups:/wal/
      --addr :9000
      --auth-key <access-key>,<secret-key>
      --cert /certs/server.crt --key /certs/server.key
    volumes:
      - /home/ubuntu/.config/rclone/rclone.conf:/config/rclone/rclone.conf:ro
      - /home/ubuntu/rclone_serve_certs:/certs:ro # openssl req -x509 -newkey rsa:4096 -sha256 -days 3650 -nodes -keyout server.key -out server.crt -subj "/CN=localhost"
    ports:
      - "127.0.0.1:9000:9000"
```


bucket for the destination - is actually a folder; need to create it via file name creation `rclone touch enc_backup_s3:bckp/filename`
