---
title: "Network connectivity & troubleshooting"
---

# MTR

`mtr -b --tcp -P 443 IP`

https://www.cloudflare.com/learning/network-layer/what-is-mtr/

## Prettyping (network monitor)

### Linux

```bash
curl -O https://raw.githubusercontent.com/denilsonsa/prettyping/master/prettyping
chmod +x prettyping
./prettyping 1.1.1.1
```

### MacOS

```bash
brew install prettyping
rehash
prettyping 1.1.1.1
```

## Visual traceroute (mtr)

### MacOS

```bash
brew install mtr
sudo mtr 1.1.1.1
```

### Linux

```bash
sudo apt install mtr #not tested
sudo mtr 1.1.1.1
```

## Kernel packet inspection

On Linux - `pwru` to see packets inside the kernel:
- https://github.com/cilium/pwru

## Other options

- [speedtest cli](https://www.speedtest.net/apps/cli)
