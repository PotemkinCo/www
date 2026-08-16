---
title: "Nessus server"
---

# Nessus server

In any case - get activation code at [Tennable page](https://www.tenable.com/products/nessus/nessus-essentials).

Download Nessus from [here](https://www.tenable.com/downloads/nessus?loginAttempted=true).

## Docker option

*(as per the [following doc](https://community.tenable.com/s/article/Deploy-Nessus-docker-image-with-docker-compose))*


> [!NOTE] No persistent directory
> Hence Nessus probably won't be updated?


Create `docker-compose.yml` as follows:
```bash
services:

  nessus:
    image: tenable/nessus:latest-ubuntu
    restart: always
    container_name: nessus
    environment:
      USERNAME: admin
      PASSWORD: <password>
      ACTIVATION_CODE: <code>
    ports:
      - 443:8834
```

Followed by the following commands:
```bash
wget -O - https://raw.githubusercontent.com/alexander-potemkin/quickies/main/docker_ubuntu.sh | bash
sudo usermod -aG docker `whoami`
docker compose up
docker compose up -d
docker container ls
docker-compose down
```

## Deb option

```bash
curl --request GET --url 'https://www.tenable.com/downloads/api/v2/pages/nessus/files/Nessus-10.9.2-ubuntu1604_amd64.deb' --output 'Nessus-10.9.2-ubuntu1604_amd64.deb'
sudo  dpkg -i Nessus*.deb
sudo service nessusd start
```

- fetch license at Nessus or get it at [https://www.tenable.com/products/nessus/nessus-essentials](https://www.tenable.com/products/nessus/nessus-essentials) (with Chrome based browser) 
- login at https://localhost:8834 with Chrome based browser (not FireFox)
- done
