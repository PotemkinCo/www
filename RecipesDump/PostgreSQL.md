# PostgreSQL notes


## Connect using connection string

([source](https://tapoueh.org/blog/2019/09/postgres-connection-strings-and-psql/))
```bash
psql -Atx postgresql://taop@localhost:5432/taop -c 'select current_date'
```
```
## Installing newer version

```bash
sudo apt install -y postgresql-common  
sudo /usr/share/postgresql-common/pgdg/apt.postgresql.org.sh
sudo apt install postgresql-client-16
```

### Command line hacks

```bash
\dt lago_db.* # shows all tables within defined schema
\dn # shows all schemas
```

[ref](https://stackoverflow.com/questions/15644152/how-to-list-the-tables-of-schemas-in-postgresql)
### PostgreSQL ping
Only checks connection!
```bash
apt install -y postgresql-client
pg_isready -d <db_name> -h <host_name> -p <port_number> -U <db_user>   
```
### PostgreSQL's repo version

Prepare software required

```bash
sudo apt -y install vim bash-completion wget s3cmd
```

Install PostgreSQL client first (18.04 Ubuntu contains PostgreSQL v10):

```bash
# Create the file repository configuration:
# Import the repository signing key - download first, to avoid "no valid OpenPGP data found." error
sudo sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
sudo wget http://apt.postgresql.org/pub/repos/apt/ACCC4CF8.asc && sudo apt-key add ACCC4CF8.asc
sudo apt-get update

# Install specific version of PostgreSQL.
sudo apt -y install postgresql-16 postgresql-client-16 #postgresql-12 - if required
```

If PostgreSQL is Docker-ized, then make sure to create port mapping (App Config tab on CapRover).

Verify the connection:

```bash
psql -U user -h 127.0.0.1 -p 65432 db_name
\d # shows tables
SHOW search_path; # shows schema
SET search_path TO myschema; 
```

If the connection is there, create database authentification file - `~/.pgpass`, `chmod 0600` and put the content in the following format: `hostname:port:database:username:password` (as per [this answer](https://stackoverflow.com/questions/2893954/how-to-pass-in-password-to-pg-dump) + there is [this article](https://sleeplessbeastie.eu/2014/03/23/how-to-non-interactively-provide-password-for-the-postgresql-interactive-terminal/)).

```bash
echo "hostname:port:database:username:password" >> ~/.pgpass && chmod 0600 ~/.pgpass
```

### S3 cmd toolset

```bash
sudo apt -y install s3cmd
s3cmd --configure --no-check-certificate #to create config file
```

For MinIO, in configuration, when asked about `DNS-style bucket+hostname:port template for accessing a bucket` just put it equal to the endpoint.
For AWS S3, just press 'Enter' for all of the fields, that are unclear.

### Backup

**Backup from docker approach**

<aside>
💡 Mind that filtering is happening by the name, not the IMG tag (which is visible by default)

</aside>

As per the [doc](https://stackoverflow.com/questions/24718706/backup-restore-a-dockerized-postgresql-database):

```shell
docker exec -t `sudo docker ps --filter name=$DOCKER_NAME_NOT_IMG -q` pg_dumpall -c -U $USER |  gzip > db_dump_$(date +"%Y-%m-%d_%H_%M_%S").gz
```

User defined in environment variables has to be provided, as it's becoming a super-user, as per [PostgreSQL Docker image documentation](https://hub.docker.com/_/postgres).

Inside the Docker image **restore** could be done with this approach: [https://stackoverflow.com/questions/36781984/load-postgres-dump-after-docker-compose-up](https://stackoverflow.com/questions/36781984/load-postgres-dump-after-docker-compose-up)

**Script**

```bash
#!/bin/bash
# Backup a Postgresql database into a daily file.
set -e
set -x

DAYS_TO_KEEP=2
FILE_SUFFIX=_db_backup.sql
BACKUP_ID=identity
HOST="127.0.0.1"
PORT=65432
DATABASE=db
USER=user
S3_BUCKET_NAME=db-backups

FILE=${BACKUP_ID}`-date +"%Y_%m_%d_%H-%M"`${FILE_SUFFIX}

pg_dump -U ${USER} -h ${HOST} -p $PORT ${DATABASE} -F p -f ${FILE}

# gzip the database dump file
#gzip $OUTPUT_FILE

# prune old local backups
find ./ -maxdepth 1 -mtime +$DAYS_TO_KEEP -name "*${FILE_SUFFIX}*" -exec rm -rf '{}' ';'

s3cmd put ${FILE} s3://$S3_BUCKET_NAME/ --no-check-certificate
```

Add script to the crontab (do backups every day at 1 am)

```bash
0 1 * * * pg_backup.sh
```

## Recovery from the database dump

<aside>
💡 Make sure to create local port mapping, if PostgreSQL is Docker-ized (6432 container port to 6432 server's port). `psql -U user -h 127.0.0.1 -p 5432 db_name` shall be then used to connect.

</aside>

1. Prepare or create (i.e. `createdb -T template0 dbname`) database where it shall be restored
2. `psql --set ON_ERROR_STOP=on -h 127.0.0.1 -p 5432 -U user db < 2021_06_10_03-00_db_backup.sql`