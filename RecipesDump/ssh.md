# SSHFS

```bash
sshfs user@<server-ip>:/var/www /var/www -p 22 -o IdentityFile=~/.ssh/id_ed25519,ServerAliveInterval=60
```

/etc/fstab:
```
user@<server-ip>:/var/www /var/www fuse.sshfs port=22,IdentityFile=~/.ssh/id_ed25519,ServerAliveInterval=60,_netdev,allow_other,reconnect 0 0
```

# connect FROM specific port

`ssh  -o 'ProxyCommand nc -p 32154 %h %p' user@<server-ip> -p 32154`

# ssh bookmarks

put every host you need at `~/.ssh/config` like that:

```
Host your-host-name
    HostName IP
    Port 22
    User $user
    IdentityFile ~/.ssh/mykey
    ServerAliveInterval=60
```

Install your shell autocomplete to enable `ssh <Tab>` to work for you at the terminal; [[zshrc]] provides an example of that for zsh.

## Generate SSH key
```
ssh-keygen -t ed25519 -C "my-key"
```

## PuTTy key to SSH
```
ssh-keygen -i -f pv-wh.ppk > pv-wh.pub
```

## Port forward
```
ssh -L local_port:destination_server_ip:remote_port ssh_server_hostname
```

example:
```
ssh –L 8443:10.6.7.147:443 server-label
```