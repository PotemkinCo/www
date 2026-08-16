# S3 things

## SSE-S3 vs SSE-KMS

SSE-S3 - is at rest encryption. KMS requires external services.

Description from [reddit](https://www.reddit.com/r/aws/comments/hsf3zr/talking_about_server_side_encryption_sse_what_is/):

> SSE-S3 is encryption as a box ticking exercise. It is there for people who need to be able to say "yes this data is encrypted at rest". It only adds security in the case somebody wanders into an AWS data centre and rips out a hard drive.
>
>SSE-KMS requires a key to exist and for users reading or writing objects to have access to both the object and the key. Meaning when a junior staffer can't figure out IAM and just opens your bucket to the world instead there's a much bigger chance that nobody can read all your tasty tasty data. It also enables things like automatic key rotation so over a long period of time a single key being breached doesn't give access to all your stuff.

### Installation

```bash
sudo apt-get install awscli
aws configure # use us-east-1 for MinIO
aws --endpoint-url=https://endpoint.com s3 cp your_file s3://db-backups
```

### S3 sync (migration, etc)

```bash
aws --endpoint-url=https://endpoint.com s3 sync s3://src s3://dst
```

See also [[rclone]]

# Minio

## Versioning

Minio Versioning - requires data cluster to be enabled first as per [https://docs.min.io/docs/minio-erasure-code-quickstart-guide.html](https://docs.min.io/docs/minio-erasure-code-quickstart-guide.html) with `minio server /data{1...12}`.
Key commands as per https://docs.min.io/docs/minio-client-complete-guide.html

```bash
wget https://dl.minio.io/client/mc/release/linux-amd64/mc --no-check-certificate
chmod +x mc
./mc alias set minio https://FQDN access_key access_pass --api S3v4

/app/code/minio-credentials get #get cloudron stored credentials

./mc version info minio/mis-files

#then versioning is enabled with:
mc version enable myminio/mybucket #Suspend versioning for bucket mybucket

mc version TARGET enable|suspend|info
mc version suspend myminio/mybucket #Suspend versioning for bucket mybucket

mc ls --versions instance/bucket #list all versions
mc ls --rewind value instance/bucket #list all object versions no later than specified date
mc du --versions instance/bucket #include all object versions
mc ls --versions myminio/mybucket/prefix/comp.csv  #check if your objects still exist with
mc retention set --default compliance 30d myminio/mybucket #Set compliance for 30 days as default retention setting on bucket mybucket; Objects created in the above bucket mybucket cannot be deleted until the compliance period is over
mc cp --version-id value #select an object version to copy
mc cp --rewind value #roll back object(s) to current version at specified time
mc cp --rewind 10d play/mybucket/myobject.txt myobject.txt #Example: Roll back to object version to 10 days earlier while copying.
mc rm  --versions  #remove object(s) and all its versions
mc rm --rewind value  #roll back object(s) to current versions at specified time
mc rm  --version-id value #delete a specific version of an object
mc rm myminio/docs/money.xls --version-id "f20f3792-4bd4-4288-8d3c-b9d05b3b62f6" #Remove a particular version ID.
mc rm myminio/docs/ --recursive --versions --rewind 365d #Remove all object versions older than one year.
mc stat -rewind value  #stat on older version(s)
mc stat  --versions #stat all versions
mc stat --version-id "CL3sWgdSN2pNntSf6UnZAuh2kcu8E8si" s3/personal-docs/2018-account_report.docx #Stat a specific object version
```

### Script that do bucket backup and keep n recent copies (keeping latest version)

```bash
#!/bin/bash
# Backup S3 bucket(s)
# #./mc alias set minio https://FQDN access_key access_pass --api S3v4 -> to configure 'minio'
set -e
set -x

WORK_FOLDER='/home/'
BACKUP_FOLDER=${WORK_FOLDER}/s3_backups
DAYS_TO_KEEP=2
FILE_SUFFIX=_s3_backup.tgz

mkdir -p ${BACKUP_FOLDER}

#mirror & archive
#MIS-FILES
${WORK_FOLDER}/mc mirror minio/mis-files ${WORK_FOLDER}/mis-files
tar czf /${WORK_FOLDER}/mis-files.tgz ${WORK_FOLDER}/mis-files
mv ${WORK_FOLDER}/mis-files.tgz  ${BACKUP_FOLDER}/mis-files-`date +"%Y_%m_%d_%H-%M"`${FILE_SUFFIX}
rm -rf ${WORK_FOLDER}/mis-files

#MIS-DB
${WORK_FOLDER}/mc mirror minio/mis-db ${WORK_FOLDER}/mis-db
tar czf /${WORK_FOLDER}/mis-db.tgz ${WORK_FOLDER}/mis-db
mv ${WORK_FOLDER}/mis-db.tgz  ${BACKUP_FOLDER}/mis-db-`date +"%Y_%m_%d_%H-%M"`${FILE_SUFFIX}
rm -rf ${WORK_FOLDER}/mis-db

#clean-up
cd ${BACKUP_FOLDER} #just in case, before find with rm notation
find ${BACKUP_FOLDER}/ -maxdepth 1 -mtime +$DAYS_TO_KEEP -name "*${FILE_SUFFIX}*" -exec rm -rf '{}' ';'

echo "Done."
```