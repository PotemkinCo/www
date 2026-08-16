[ref](https://unix.stackexchange.com/questions/481939/how-to-export-a-gpg-private-key-and-public-key-to-a-file)

```bash
gpg --full-generate-key # generates keys
gpg --list-keys
gpg --output public.pgp --armor --export username@email
gpg --output private.pgp --armor --export-secret-key username@email


gpg --import public.gpg
gpg  --batch --yes --trust-model always  --output file_enc --encrypt --recipient username@email file
gpg --output file --decrypt file_enc
```