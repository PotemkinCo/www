import os
import re

src_dir = '/home/alex/ai/potemkin.co/RecipesDump'
dst_dir = '/home/alex/ai/potemkin.co/src/content/tech-scribbles'
os.makedirs(dst_dir, exist_ok=True)

recipe_meta = {
    'Authelia.md': {
        'slug': 'authelia-authentication-server',
        'title': 'Authelia Authentication Server Setup',
        'desc': 'Configuring Authelia 2FA portal, Argon2 password hashing, and user database management.',
        'tags': ['authelia', 'auth', 'security', 'docker'],
    },
    'CapRover (local kind of Heroku).md': {
        'slug': 'caprover-self-hosted-paas',
        'title': 'CapRover Self-Hosted PaaS Setup and Migration',
        'desc': 'Complete guide for installing, configuring, deploying, backing up, and migrating CapRover PaaS.',
        'tags': ['caprover', 'paas', 'docker', 'devops', 'self-hosted'],
    },
    'Cheap GPUs and LLMs.md': {
        'slug': 'cheap-gpus-and-llms',
        'title': 'Cheap Cloud GPUs and LLM Compute Pricing',
        'desc': 'Hourly pricing benchmarks and reference notes for renting H100, A100, and RTX 4090 GPUs.',
        'tags': ['gpu', 'llm', 'ai', 'cloud'],
    },
    'Check IP address (if it\'s good for e-mail).md': {
        'slug': 'check-ip-address-email-reputation',
        'title': 'IP Blacklist and Email Reputation Check',
        'desc': 'Tools and services for verifying mail server IP reputation and blacklist status.',
        'tags': ['email', 'networking', 'dns', 'sysadmin'],
    },
    'CloudRon (managed apps).md': {
        'slug': 'cloudron-managed-apps',
        'title': 'Cloudron Managed Apps and Infrastructure',
        'desc': 'Deployment, unbound DNS, wildcard SSL, LDAP synchronization, and troubleshooting for Cloudron.',
        'tags': ['cloudron', 'self-hosted', 'sysadmin', 'ldap', 'ssl'],
    },
    'Docker (on Ubuntu).md': {
        'slug': 'docker-on-ubuntu',
        'title': 'Docker on Ubuntu Administration and Rootless Setup',
        'desc': 'One-liner installs, rootless Docker configuration, systemd pasta networking, storage migration, and CLI tips.',
        'tags': ['docker', 'ubuntu', 'linux', 'devops', 'rootless'],
    },
    'Element Calls.md': {
        'slug': 'element-call-and-matrixrtc',
        'title': 'Element Call and MatrixRTC Self-Hosting',
        'desc': 'Hosting Element Call with LiveKit, JWT authentication service, Caddy reverse proxy, and Synapse MSC3266.',
        'tags': ['matrix', 'element', 'livekit', 'webrtc', 'caddy'],
    },
    'Flashing Android.md': {
        'slug': 'flashing-android-and-pixel',
        'title': 'Android Bootloader and Fastboot Flashing',
        'desc': 'Restoring stock OS, ADB sideloading, fastboot commands, and web flashing on Google Pixel devices.',
        'tags': ['android', 'pixel', 'fastboot', 'adb'],
    },
    'FrameWork laptop.md': {
        'slug': 'framework-laptop-linux-freebsd',
        'title': 'Framework Laptop Linux and FreeBSD Configuration',
        'desc': 'Fixing WiFi freezes, fingerprint reader setup, sysctl io_uring tweaks, and FreeBSD installation on Framework 13.',
        'tags': ['framework', 'linux', 'freebsd', 'hardware'],
    },
    'Garage (S3).md': {
        'slug': 'garage-distributed-s3',
        'title': 'Garage Distributed S3 Storage Setup',
        'desc': 'Deploying lightweight Garage S3 storage on FreeBSD and Linux with ZFS datasets, Podman, and Rclone.',
        'tags': ['garage', 's3', 'storage', 'freebsd', 'zfs', 'podman'],
    },
    'GitHub.md': {
        'slug': 'github-actions-runners-and-pages',
        'title': 'GitHub Actions Runners and GitHub Pages DNS',
        'desc': 'Configuring self-hosted GitHub Actions runners as system services and setting up root domain apex DNS records.',
        'tags': ['github', 'actions', 'ci-cd', 'dns'],
    },
    'Hetzner.md': {
        'slug': 'hetzner-server-hardware-and-storage-box',
        'title': 'Hetzner Server Hardware, Storage Box, and iGPU',
        'desc': 'Managing Hetzner Storage Box via SFTP/Rclone, enabling Intel iGPU on Linux, and Vulkan LLM inference.',
        'tags': ['hetzner', 'storage-box', 'hardware', 'igpu', 'linux'],
    },
    'Jitsi.md': {
        'slug': 'jitsi-meet-video-conferencing',
        'title': 'Jitsi Meet Video Conferencing and JVB Setup',
        'desc': 'Deploying Jitsi Meet via Docker, JVB STUN/TURN routing, Caddy reverse proxy, Jibri recording, and automated testing.',
        'tags': ['jitsi', 'webrtc', 'video', 'docker', 'caddy'],
    },
    'Lago (billing).md': {
        'slug': 'lago-open-source-billing',
        'title': 'Lago Open-Source Billing Setup',
        'desc': 'Deploying self-hosted Lago metering and billing system using Docker Compose and Caddy.',
        'tags': ['lago', 'billing', 'docker', 'caddy', 'fintech'],
    },
    'MacOS.md': {
        'slug': 'macos-power-and-cli-utilities',
        'title': 'macOS Power Management and CLI Utilities',
        'desc': 'Managing hibernatemode, discrete GPU switching, PDF flattening, EXIF metadata stripping, and SMC resets on macOS.',
        'tags': ['macos', 'cli', 'apple', 'sysadmin'],
    },
    'Matrix & Element.md': {
        'slug': 'matrix-synapse-and-mas-auth',
        'title': 'Matrix Synapse and MAS Authentication',
        'desc': 'Running Synapse homeserver, Matrix Authentication Service (MAS), PostgreSQL migration, and Caddy integration.',
        'tags': ['matrix', 'synapse', 'element', 'mas', 'caddy', 'postgresql'],
    },
    'Mattermost.md': {
        'slug': 'mattermost-cli-and-github-integration',
        'title': 'Mattermost Configuration and GitHub Integration',
        'desc': 'CLI channel administration, rate-limit adjustments, and GitHub webhook subscriptions in Mattermost.',
        'tags': ['mattermost', 'chat', 'github', 'devops'],
    },
    'MkDocs on GitHub Pages.md': {
        'slug': 'mkdocs-material-on-github-pages',
        'title': 'MkDocs Material Setup on GitHub Pages',
        'desc': 'Building and automating documentation websites using Material for MkDocs and GitHub Actions.',
        'tags': ['mkdocs', 'docs', 'github-pages', 'python'],
    },
    'Monit and MMonit monitoring tool.md': {
        'slug': 'monit-and-mmonit-monitoring',
        'title': 'Monit and M-Monit Infrastructure Monitoring',
        'desc': 'System health checks, SMART disk monitoring, software RAID verification, and Matrix webhook alerts with Monit and M/Monit.',
        'tags': ['monit', 'mmonit', 'monitoring', 'sysadmin', 'devops'],
    },
    'Multipass.md': {
        'slug': 'multipass-vm-management',
        'title': 'Multipass VM Management and Snapshots',
        'desc': 'Creating lightweight Ubuntu VMs with Canonical Multipass, configuring host bridges, snapshots, and backups.',
        'tags': ['multipass', 'virtualization', 'ubuntu', 'linux'],
    },
    'Nessus server.md': {
        'slug': 'nessus-vulnerability-scanner',
        'title': 'Nessus Vulnerability Scanner Installation',
        'desc': 'Deploying Tenable Nessus Essentials vulnerability scanner using Docker Compose or standalone Debian packages.',
        'tags': ['nessus', 'security', 'vulnerability', 'docker'],
    },
    'Netdata.md': {
        'slug': 'netdata-performance-monitoring',
        'title': 'Netdata Real-Time Performance Monitoring',
        'desc': 'Installing Netdata agent, configuring local bindings, and setting up parent-child log aggregation with SSL.',
        'tags': ['netdata', 'monitoring', 'metrics', 'linux'],
    },
    'Network connectivity.md': {
        'slug': 'network-connectivity-and-diagnostics',
        'title': 'Network Connectivity and Diagnostic Tools',
        'desc': 'Diagnosing network latency, packet loss, and routing issues with MTR, PrettyPing, and Speedtest CLI.',
        'tags': ['networking', 'mtr', 'latency', 'troubleshooting'],
    },
    'Network troubleshooting.md': {
        'slug': 'network-packet-tracing-pwru',
        'title': 'Linux Kernel Packet Tracing with pwru',
        'desc': 'Inspecting network packets in the Linux kernel using eBPF and pwru.',
        'tags': ['networking', 'ebpf', 'kernel', 'linux'],
    },
    'NextCloud.md': {
        'slug': 'nextcloud-oidc-login-configuration',
        'title': 'Nextcloud OIDC Direct Login Configuration',
        'desc': 'Bypassing the default Nextcloud login page when OpenID Connect (OIDC) SSO is enabled.',
        'tags': ['nextcloud', 'oidc', 'sso', 'self-hosted'],
    },
    'Pictures for AppStore & Google Play.md': {
        'slug': 'app-store-screenshot-tools',
        'title': 'App Store and Google Play Screenshot Tools',
        'desc': 'Curated generator and mockup tools for designing mobile app screenshots and previews.',
        'tags': ['mobile', 'design', 'app-store', 'tools'],
    },
    'PostgreSQL.md': {
        'slug': 'postgresql-administration-and-backups',
        'title': 'PostgreSQL Administration, Backups, and S3 Archival',
        'desc': 'Client connections, automated pg_dumpall backup scripts, S3 archival with s3cmd, and database restores.',
        'tags': ['postgresql', 'database', 'sql', 'backups', 's3'],
    },
    'Proxy (tinyproxy).md': {
        'slug': 'tinyproxy-http-proxy',
        'title': 'Tinyproxy Lightweight HTTP Proxy Setup',
        'desc': 'Installing and securing Tinyproxy HTTP/HTTPS proxy daemon with basic auth and access controls.',
        'tags': ['tinyproxy', 'proxy', 'networking', 'linux'],
    },
    'RustDesk server.md': {
        'slug': 'rustdesk-remote-desktop-server',
        'title': 'RustDesk Remote Desktop Server Setup',
        'desc': 'Self-hosting RustDesk OSS relay and rendezvous servers (hbbs/hbbr) with Docker Compose and automated updates.',
        'tags': ['rustdesk', 'remote-desktop', 'docker', 'self-hosted'],
    },
    'S3 things.md': {
        'slug': 's3-storage-and-minio-versioning',
        'title': 'S3 Storage, MinIO Versioning, and Retention',
        'desc': 'AWS CLI commands, SSE-S3 vs SSE-KMS encryption differences, MinIO bucket versioning, retention policies, and mirror backups.',
        'tags': ['s3', 'minio', 'storage', 'aws', 'backups'],
    },
    'SSL certificates.md': {
        'slug': 'ssl-certificates-and-acme-dns',
        'title': 'SSL Certificates and ACME-DNS Wildcard Automation',
        'desc': 'Free wildcard SSL issuance via acme-dns, acme.sh automation, commercial certificate bundle concatenation, and Nginx Certbot setup.',
        'tags': ['ssl', 'acme', 'letsencrypt', 'security', 'caddy', 'nginx'],
    },
    'Swagger (&GitHub).md': {
        'slug': 'hosting-swagger-ui-on-github-pages',
        'title': 'Hosting Swagger UI on GitHub Pages',
        'desc': 'Embedding standalone Swagger UI documentation bundles on GitHub Pages using CDN scripts.',
        'tags': ['swagger', 'openapi', 'api', 'github-pages'],
    },
    'Telegram.md': {
        'slug': 'telegram-installation-and-chat-id',
        'title': 'Telegram Installation and Chat ID Extraction',
        'desc': 'Installing Telegram desktop on Ubuntu via PPA and obtaining group chat IDs for notification bots.',
        'tags': ['telegram', 'chat', 'bot', 'ubuntu'],
    },
    'Ubuntu.md': {
        'slug': 'ubuntu-server-administration-and-hardening',
        'title': 'Ubuntu Server Administration and Hardening',
        'desc': 'Home folder fscrypt encryption, PAM SSH security, UFW + Docker iptables integration, disk tools, and systemd services.',
        'tags': ['ubuntu', 'linux', 'security', 'fscrypt', 'systemd', 'ufw'],
    },
    'UpCloud.md': {
        'slug': 'upcloud-cli-storage-and-firewall',
        'title': 'UpCloud CLI, Storage, and Firewall Configuration',
        'desc': 'Managing UpCloud floating IPs, online disk expansion, live filesystem migration, and CLI firewall rule automation.',
        'tags': ['upcloud', 'cloud', 'cli', 'firewall', 'storage'],
    },
    'VPNs.md': {
        'slug': 'wireguard-vless-reality-and-vpns',
        'title': 'WireGuard, VLESS Reality, and VPN Infrastructure',
        'desc': 'WireGuard site-to-site tunnels via Netplan, Shadowsocks over WebSockets, VLESS XTLS Reality with Sing-box and XRay, and geo-routing.',
        'tags': ['vpn', 'wireguard', 'vless', 'reality', 'shadowsocks', 'sing-box'],
    },
    'VirtualBox.md': {
        'slug': 'virtualbox-linux-shared-folders',
        'title': 'VirtualBox Linux Setup and Shared Folders',
        'desc': 'Enabling vboxsf shared folders permissions and resolving KVM/Docker kernel module conflicts.',
        'tags': ['virtualbox', 'virtualization', 'linux'],
    },
    'Windows Activation.md': {
        'slug': 'windows-activation-helper',
        'title': 'Windows Activation Helper',
        'desc': 'PowerShell activation command reference for Windows operating systems.',
        'tags': ['windows', 'powershell', 'sysadmin'],
    },
    'caddy web servr.md': {
        'slug': 'caddy-web-server-and-proxy',
        'title': 'Caddy Web Server Configuration and Reverse Proxy',
        'desc': 'Caddy rate limiting, xcaddy custom build persistence, rootless Docker slirp4netns proxying, and logging setups.',
        'tags': ['caddy', 'web-server', 'proxy', 'http', 'xcaddy'],
    },
    'ffmpeg (images conversion).md': {
        'slug': 'ffmpeg-image-conversion',
        'title': 'FFmpeg Image Conversion Recipes',
        'desc': 'Batch converting WebP images to PNG and installing FFmpeg.',
        'tags': ['ffmpeg', 'media', 'cli', 'images'],
    },
    'git.md': {
        'slug': 'git-divergent-branches-and-credentials',
        'title': 'Git Divergent Branches and Credentials',
        'desc': 'Resolving divergent git branch conflicts with rebase/fast-forward and storing credential helper credentials.',
        'tags': ['git', 'version-control', 'cli'],
    },
    'gpg aka gnupg.md': {
        'slug': 'gpg-key-management-and-encryption',
        'title': 'GPG Key Export, Import, and File Encryption',
        'desc': 'Generating, exporting ASCII-armored public/private keys, and encrypting/decrypting files with GnuPG.',
        'tags': ['gpg', 'gnupg', 'crypto', 'security'],
    },
    'libkvm.md': {
        'slug': 'kvm-libvirt-vm-management',
        'title': 'KVM and Libvirt Virtual Machine Management',
        'desc': 'Managing KVM virtual machines with virsh, performing live backups, Virt-manager tips, and Cockpit comparison.',
        'tags': ['kvm', 'libvirt', 'virtualization', 'linux', 'qemu'],
    },
    'livekit & coturn.md': {
        'slug': 'livekit-and-coturn-webrtc',
        'title': 'LiveKit and Coturn WebRTC Setup',
        'desc': 'Self-hosting LiveKit server on VM, generating room access tokens with Python, and Coturn TURN server auth configuration.',
        'tags': ['livekit', 'coturn', 'webrtc', 'python', 'turn'],
    },
    'llama.cpp.md': {
        'slug': 'llama-cpp-server-and-gpu-acceleration',
        'title': 'llama.cpp Server Setup and GPU Acceleration',
        'desc': 'Building llama.cpp with SSL and Vulkan/BLIS support, running Qwen and Mistral models with API tokens.',
        'tags': ['llm', 'llama-cpp', 'ai', 'gpu', 'vulkan'],
    },
    'ntfy.md': {
        'slug': 'ntfy-notification-server',
        'title': 'Ntfy Notification Server Setup',
        'desc': 'Installing and configuring ntfy HTTP push notification client and service on Debian/Ubuntu.',
        'tags': ['ntfy', 'notifications', 'linux', 'self-hosted'],
    },
    'ollama.md': {
        'slug': 'ollama-server-with-caddy-auth',
        'title': 'Ollama LLM Server with Caddy Auth',
        'desc': 'Installing Ollama, executing large models, and securing API endpoints behind Caddy Bearer token authorization.',
        'tags': ['ollama', 'llm', 'ai', 'caddy', 'security'],
    },
    'rclone.md': {
        'slug': 'rclone-s3-sync-and-storage',
        'title': 'Rclone S3 Sync and Storage Management',
        'desc': 'Installing Rclone, synchronizing S3 buckets, encrypted remotes, and serving local folders as S3 endpoints via Docker.',
        'tags': ['rclone', 's3', 'storage', 'backup', 'cloud'],
    },
    'ssh.md': {
        'slug': 'ssh-tips-sshfs-and-port-forwarding',
        'title': 'SSH Tips, SSHFS, and Key Management',
        'desc': 'Mounting remote directories with SSHFS, ~/.ssh/config shortcuts, PuTTY PPK conversion, and local port forwarding.',
        'tags': ['ssh', 'sshfs', 'networking', 'linux', 'security'],
    },
    'vllm on cpu.md': {
        'slug': 'vllm-inference-on-cpu',
        'title': 'vLLM Inference on CPU',
        'desc': 'Building and serving vLLM models (e.g. Nanonets OCR) on CPU architecture using systemd services.',
        'tags': ['vllm', 'ai', 'ocr', 'python', 'systemd'],
    },
    '😈 FreeBSD bare metal.md': {
        'slug': 'freebsd-bare-metal-zfs-and-jails',
        'title': 'FreeBSD Bare Metal, ZFS, and Bastille Jails',
        'desc': 'Rescue system deployment (depenguin.me), GELI disk encryption, ZFS tuning, Bastille jails, bhyve VMs, PF firewall, and HAProxy.',
        'tags': ['freebsd', 'zfs', 'jails', 'bastille', 'bhyve', 'pf', 'haproxy', 'bare-metal'],
    },
}

def clean_body(filename, raw_text):
    # Remove raw obsidian wiki links like [[2025-08-22]] or [[caddy web servr]]
    def clean_wiki(match):
        inner = match.group(1).strip()
        if re.match(r'^\d{4}-\d{2}-\d{2}$', inner):
            return f'*{inner}*'
        return inner
    text = re.sub(r'\[\[(.*?)\]\]', clean_wiki, raw_text)
    
    # Clean any top-level H1 headers that duplicate title or have emojis
    lines = text.splitlines()
    cleaned_lines = []
    
    in_codeblock = False
    for line in lines:
        if line.strip().startswith('```'):
            in_codeblock = not in_codeblock
            cleaned_lines.append(line)
            continue
        
        if not in_codeblock:
            # Demote H1 to H2 if not code block
            if line.startswith('# '):
                h_text = line[2:].strip()
                # Remove emojis
                h_text = h_text.replace('😈 ', '').replace('😈', '')
                cleaned_lines.append(f'## {h_text}')
                continue
        
        cleaned_lines.append(line)
        
    res = '\n'.join(cleaned_lines).strip()
    return res

for filename, meta in recipe_meta.items():
    src_file = os.path.join(src_dir, filename)
    with open(src_file, 'r', encoding='utf-8') as fp:
        raw = fp.read()
    
    body = clean_body(filename, raw)
    
    # Format YAML frontmatter
    tags_yaml = '[' + ', '.join([f'"{t}"' for t in meta['tags']]) + ']'
    frontmatter = f"""---
title: "{meta['title']}"
description: "{meta['desc']}"
publishDate: 2026-08-16
updatedDate: 2026-08-16
tags: {tags_yaml}
draft: false
---

"""
    full_content = frontmatter + body + '\n'
    out_file = os.path.join(dst_dir, f"{meta['slug']}.md")
    with open(out_file, 'w', encoding='utf-8') as fp:
        fp.write(full_content)
    print(f"Generated: {meta['slug']}.md ({len(full_content.splitlines())} lines)")

print(f"Successfully processed {len(recipe_meta)} recipes into {dst_dir}")
