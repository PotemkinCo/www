---
title: "FrameWork laptop"
---

# Linux
## WiFi / other crashes troubleshooting

`curl -s https://raw.githubusercontent.com/FrameworkComputer/linux-docs/main/log-helper/combined.sh -o combined.sh && clear && bash combined.sh`


as of 2025-09-19, I have ` Linux freezed on AMD FW13` issue raised.
## Fingerprint
[ref](https://framework.kustomer.help/ubuntu-fingerprint-troubleshooting-r1_DA0TMn)
```bash
sudo apt install libpam-fprintd
sudo pam-auth-update
```


SSD, encryption, CPU_IOWAIT research done *2025-08-22*.

- fix for high CPU_IOWAIT:
```bash
sudo tee -a /etc/sysctl.d/10-disable-io_uring.conf  >> /dev/null << 'EOF'
 kernel.io_uring_disabled = 1
EOF
```
# FreeBSD

- Download normal ISO
- Write with BalenaEtcher or equivalent
- Follow instructions: https://github.com/FrameworkComputer/freebsd-on-framework/tree/main?tab=readme-ov-file
