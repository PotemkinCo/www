---
title: "VirtualBox"
---

To let shared folders work: 
```bash
sudo adduser $USER vboxsf
sudo shutdown -r now
```


To shut down conflicting Docker services:

```bash
#!/bin/bash
sudo systemctl stop docker
sudo systemctl disable docker
sudo rmmod kvm_amd
```
