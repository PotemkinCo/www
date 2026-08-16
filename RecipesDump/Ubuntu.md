# uv system wise

```bash
sudo sh -c 'curl -LsSf https://astral.sh/uv/install.sh | UV_INSTALL_DIR=/usr/local/bin sh'
```

# disks secure erase

For Hetznner's recovery image - `erase.sh`:

`curl -fsSL https://raw.githubusercontent.com/PotemkinCo/toolbelt/refs/heads/main/nvme_erase.sh | bash`

# quickly test ports

```bash
nmap -T4 -p- --open --min-rate=1000 --min-parallelism=100 -Pn 198.51.100.1
```

# fscrypt setup

```bash
# Install dependencies
sudo apt update && sudo apt install -y fscrypt libpam-fscrypt

# Enable encryption on the file system
# IMPORTANT: Replace '/dev/sda2' with your actual /home partition (check with: df -h /home)
sudo tune2fs -O encrypt /dev/sda2

# Initialize fscrypt configuration
sudo fscrypt setup # choose N on 'Allow users other than root to create fscrypt metadata on the root filesystem?'

# Enable PasswordAuthentication and PAM in sshd_config
sudo sed -i 's/^#PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/^PasswordAuthentication no/PasswordAuthentication yes/' /etc/ssh/sshd_config
sudo sed -i 's/^#UsePAM.*/UsePAM yes/' /etc/ssh/sshd_config

# Restart SSH service
sudo systemctl restart ssh

# Ensure PAM module is active (Select "Identity management for fscrypt" if prompted)
sudo pam-auth-update

USER_NAME="newuser"

# 1. Create the user
sudo adduser $USER_NAME

# 2. Move skeleton files out (directory must be empty to encrypt)
sudo mv /home/$USER_NAME /home/$USER_NAME.bak
sudo mkdir /home/$USER_NAME
sudo chown $USER_NAME:$USER_NAME /home/$USER_NAME

# 3. Encrypt the directory
# Select option "1 - Your login passphrase (pam_passphrase)"
# Enter the NEW USER'S password when prompted
sudo fscrypt encrypt /home/$USER_NAME --user=$USER_NAME

# 4. Restore skeleton files
# Unlock first to verify access
sudo fscrypt unlock /home/$USER_NAME --user=$USER_NAME
# Copy files back
sudo cp -a /home/$USER_NAME.bak/. /home/$USER_NAME/
# Cleanup
sudo rm -rf /home/$USER_NAME.bak

```

Manually change encryption password:
```
fscrypt status /
# Replace 5e2d... with your actual hash
fscrypt metadata change-passphrase --protector=/:5e2d14...

```

# CPU performance

by default is `powersave`, list CPU modes available:

```
cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_available_governors
```
Change mode:
```
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor
```

Also use `taskset -c 0-5` to bind some task to a specific CPU *cores*

And a permanent option:

```bash
sudo apt update && sudo apt -y install cpufrequtils
echo 'GOVERNOR="performance"' | sudo tee /etc/default/cpufrequtils
sudo systemctl restart cpufrequtils
sudo systemctl disable ondemand # may fail safely
```
# GPU & iGPU

`lspci -nnk | grep -A3 VGA` shows (i)GPU connected to the system.

## NVidia GPU

That is a summary of [[vLLM & NVidia GPU]], [vllm ref](https://docs.vllm.ai/en/stable/deployment/docker.html):
```bash
# GPU drivers and tools
ubuntu-drivers devices | grep recommended | grep -oP nvidia-driver-[0-9]* | awk '{sub(/driver-/,""); print}' | { read -d '' x; echo "sudo apt install -y linux-modules-$x-$(uname -r)"; } | bash
sudo apt install nvtop nvidia-utils-$(dpkg -l | awk '/nvidia-kernel-common-[0-9]+/ {print $2}' | sed -E 's/.*-([0-9]+)$/\1/')
sudo apt install nvtop nvidia-driver-$(dpkg -l | awk '/nvidia-kernel-common-[0-9]+/ {print $2}' | sed -E 's/.*-([0-9]+)$/\1/')
```

## Intel's iGPU

If `sudo lspci -v -s $(lspci | grep VGA | grep Intel | cut -d" " -f 1)` gives no kernel module / GPU, then enable it:

```bash
ls -la /dev/dri # expected to fail -> iGPU is disabled
vi /etc/modprobe.d/blacklist-hetzner.conf # comment out (disabled) i915 & i915_bdw
vi /etc/default/grub.d/hetzner.cfg # at GRUB_CMDLINE_LINUX_DEFAULT, 'nomodeset' to be removed
sudo grub-mkconfig -o /boot/grub/grub.cfg
sudo shutdown -r now
ls -la /dev/dri # shall give devices list
sudo lspci -v -s $(lspci | grep VGA | grep Intel | cut -d" " -f 1) # shall contain 'Kernel driver in use: i915'
sudo apt install intel-gpu-tools
sudo intel_gpu_top
#  modprobe i915 if top fails
```

## Docker & GPU support

```bash
# Docker & lazydocker
wget -O - https://get.docker.com | sudo bash
curl https://raw.githubusercontent.com/jesseduffield/lazydocker/master/scripts/install_update_linux.sh | bash
echo 'PATH=$PATH:~/.local/bin' >> ~/.bashrc
# GPU for Docker
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
apt update && apt install -y nvidia-container-toolkit
nvidia-ctk runtime configure --runtime=docker
systemctl restart docker

```
## llama.cpp

### Vanilla

[ref](https://github.com/ggml-org/llama.cpp/discussions/15396)
```bash
# vulcan
sudo apt install vulkan-tools libvulkan1 libnvidia-gl-580
curl -s https://api.github.com/repos/ggml-org/llama.cpp/releases/latest | grep 'vulkan' | grep 'ubuntu' | tail -1 | cut -d '"' -f 4 | wget -qi -
# ubuntu
# curl -s https://api.github.com/repos/ggml-org/llama.cpp/releases/latest | grep -v 'vulkan' | grep 'ubuntu' | tail -1 | cut -d '"' -f 4 | wget -qi -
apt install -y unzip
unzip *.zip && cd build/bin
./llama-server --list-devices
./llama-server -hf ggml-org/gpt-oss-120b-GGUF --ctx-size 32768 --jinja -ub 2048 -b 2048 --n-cpu-moe 28
```

`llama-server.service` file:

```
[Unit]
Description=Llama-Server GPT Inference
After=network.target

[Service]
# Run as root or change to your user
User=root
Group=root

# Always restart if it crashes
Restart=always
RestartSec=5

# The command to run
ExecStart=/root/llama-server/bin/llama-server -hf ggml-org/gpt-oss-120b-GGUF --ctx-size 32768 --jinja -ub 2048 -b 2048 --n-cpu-moe 28

[Install]
WantedBy=multi-user.target
```

Followed by activation:
```bash
sudo systemctl daemon-reload
sudo systemctl enable llama-server.service
sudo systemctl start llama-server.service
```

And monitoring via `nvtop`.


Adding protection with key file:
```Caddyfile
llm.example.com {
        log
        @unauthorized not header Authorization "Bearer <api-bearer-token>"
        respond @unauthorized "No chatter for you!"

        reverse_proxy 127.0.0.1:8080
}
```

And caddy install, as per [[caddy web servr]] - NON DOCKER!

### Docker

```bash
docker run --runtime nvidia --gpus all -v ./llama_data:/root -p 8000:8000 ghcr.io/ggml-org/llama.cpp:server-cuda -hf unsloth/gemma-3-27b-it-qat-GGUF --port 8000 --host 0.0.0.0
```

**The compose.yml file**:
```yaml
services:
  llama-server:
    restart: unless-stopped
    image: ghcr.io/ggml-org/llama.cpp:server-cuda-b6602
    runtime: nvidia
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
    volumes:
      - ./llama_data:/root
    command: >
      -hf unsloth/gemma-3-27b-it-qat-GGUF
      --port 8000
      --host 0.0.0.0
```

## vLLM

```bash
docker run --runtime nvidia --gpus all -v ./vllm:/root/.cache/huggingface -p 8000:8000 --ipc=host vllm/vllm-openai:v0.10.2-x86_64 --model unsloth/gemma-3-27b-it
# the later didn't work out for me on Hetzner's lowest requirements GPU machine
```

## Test

### localhost

```bash
time curl http://localhost:8000/v1/chat/completions -H "Content-Type: application/json" -d '{
"model": "gpt-4", "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello, write me a story"} ], "temperature": 0.7 }'
```

### remote

```bash
time curl https://llm.example.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <api-bearer-token>" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "system", "content": "You are a helpful assistant."},
      {"role": "user", "content": "Hello, write me a story"}
    ],
    "temperature": 0.7
  }'

```

# Disk space usage

One of
```bash
sudo apt install ncdu
sudo apt install gdu
sudo snap install dua
```

# WiFi doesn't connect - needs re-connecting

```bash
sudo tee /etc/systemd/system/wifi-resume.service << 'EOF'

[Unit]

Description=Re-enable WiFi after resume

After=suspend.target
[Service]

Type=oneshot

ExecStart=/bin/bash -c 'sleep 3 && nmcli radio wifi off && sleep 1 && nmcli radio wifi on'
[Install]

WantedBy=suspend.target

EOF

(and after that)


sudo systemctl daemon-reload

sudo systemctl enable wifi-resume.service

(Now you are set. Test it. If it fails, provide the log using these commands)

systemctl status wifi-resume.service
journalctl -u wifi-resume.service -b
```

# Thunderbird via deb

https://askubuntu.com/questions/1513445/how-to-install-thunderbird-as-a-traditional-deb-package-without-snap-in-ubuntu-2

`sudo su` followed by:

```bash
add-apt-repository ppa:mozillateam/ppa
echo '
Package: *
Pin: release o=LP-PPA-mozillateam
Pin-Priority: 1001

Package: thunderbird
Pin: version 2:1snap*
Pin-Priority: -1
' | sudo tee /etc/apt/preferences.d/thunderbird
snap remove thunderbird
apt install thunderbird
echo 'Unattended-Upgrade::Allowed-Origins:: "LP-PPA-mozillateam:${distro_codename}";' | sudo tee /etc/apt/apt.conf.d/51unattended-upgrades-thunderbird
```

# replace root on login

Login via root:
```bash
adduser --disabled-password --gecos "" alex
usermod -aG sudo alex
install -d -m 700 -o alex -g alex /home/alex/.ssh && \
install -m 600 -o alex -g alex /root/.ssh/authorized_keys /home/alex/.ssh/authorized_keys
echo '%sudo ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/sudo-nopasswd
```
Then, once logged in:
```bash
sudo cp /etc/ssh/sshd_config /etc/ssh/sshd_config-backup
sudo sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
grep -Ei 'permitrootlogin|passwordauthentication' /etc/ssh/sshd_config | grep -v "^#"
sudo systemctl restart ssh ssh.socket
sudo systemctl status ssh
```

Retry the ssh.

# change ssh port on Ubuntu 24.04

`sudo systemctl daemon-reload` followed by `sudo systemctl restart ssh.socket` ([source](https://serverfault.com/questions/1159599/how-to-change-the-ssh-server-port-on-ubuntu))


# update / verify grub

`sudo update-grub`

## Make it display menu

```bash
vi /etc/default/grub # GRUB_TIMEOUT_STYLE=menu
sudo update-grub
```

## clean up fill disk space (very quickly)
[ref](https://superuser.com/questions/223309/how-to-fill-a-hard-drive-in-linux)
```bash
yes abcdefghijklmnopqrstuvwxyz0123456789 > largefile
sync; sync
sudo fstrim -av
rm largefile
```

### a (much) slower approach

```
sudo apt update && sudo apt install secure-delete
nohup sudo sfill -v / &
```
or
```
nohup sudo sfill -llv /
```

# nopasswd on sudo

`%sudo ALL=(ALL) NOPASSWD: ALL`
# creating new filesystem
```bash
lsblk
fdisk /dev/vdb # n => p => w
lsblk
mkfs.ext4 /dev/vdb1
blkid | grep vdb1 # note UUID
vi /etc/fstab
```
# jq

Print file structure ([src](https://stackoverflow.com/questions/78181026/how-to-recursively-print-the-path-of-all-keys-in-jq)):
```bash
cat server.json |  jq '[paths|(map(if type == "number" then "[]" else ".\(.)" end)|join(""))]|unique'
```

# benchmark
### CPU
```bash
sudo apt-get install sysbench
sysbench cpu run
sysbench --threads="$(nproc)" cpu run
```

# I/O
([ref](https://www.binarytides.com/benchmark-disk-io-speed-with-sysbench-in-linux/))
```bash
sysbench fileio --file-test-mode=seqwr --time=600 run
```

# I/O / disk / ssd system information
```bash
cat /proc/mdstat
vmstat 1 10
sudo apt install smartmontools
lsblk
smartctl -a /dev/...
```

## fantastic load monitor
`atop -B`

## Install SpeedTest CLI
```bash
curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | sudo bash
sudo apt-get install speedtest
```

## Remove snap
```bash
snap list
snap remove --purge pkg_name
systemctl disable snapd
systemctl mask snapd
sudo apt-mark hold snapd
```

## Let shared disk work on VirtualBox
```bash
sudo adduser $USER vboxsf
sudo shutdown -r now
```

## crontab for reboot
```
30 4 * * MON-THU /bin/sh -c '[ -f /var/run/reboot-required ] && sudo shutdown -r now'
```
## check IP address
```bash
curl checkip.amazonaws.com
```
## pro subscription


### Java & Maven:
```bash
wget https://download.java.net/java/GA/jdk20.0.2/6e380f22cbe7469fa75fb448bd903d8e/9/GPL/openjdk-20.0.2_linux-x64_bin.tar.gz https://dlcdn.apache.org/maven/maven-3/3.9.4/binaries/apache-maven-3.9.4-bin.tar.gz
tar -xvf openjdk*.tar.gz
tar -xvf apache-maven-*-bin.tar.gz
mv jdk-* /opt/
mv apache-maven-* /opt/
vi .profile
```

Add the following lines there:
```bash
JAVA_HOME='/opt/jdk-20.0.2'
PATH="$JAVA_HOME/bin:$PATH"
M2_HOME='/opt/apache-maven-3.9.4'
PATH="$M2_HOME/bin:$PATH"
export PATH
```

and execute:
```bash
source .profile
java -version
mvn -version
```

Ref: [JDK](https://jdk.java.net/20/), [Maven](https://maven.apache.org/download.cgi), [doc](https://www.digitalocean.com/community/tutorials/install-maven-linux-ubuntu).

### disable service autostart
```bash
systemctl disable <service>
```

### enable journald size limit

as per [this article](https://askubuntu.com/questions/1012912/systemd-logs-journalctl-are-too-large-and-slow)

```bash
journalctl --disk-usage # to check the usage

journalctl --vacuum-size=200M #to clean things up

grep SystemMaxUse /etc/systemd/journald.conf  #parameter to support logs
SystemMaxUse=50M
```

### alternative for cron - systemd

from [here](https://linuxconfig.org/how-to-schedule-tasks-with-systemd-timers-in-linux)

```bash
systemctl list-timers
```

### Disable IPv6 in Ubuntu

```bash
cat <<EOF >> /etc/sysctl.d/99-no_ipv6.conf
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1
EOF
service procps force-reload
```

**AND** disable it in `netplan` config: add `link-local: [ ipv4 ]` at the same level, as dhcp instruction 

### Laptop battery status

```bash
upower -e
upower -i <battery_path>

cd /sys/class/power_supply/BAT0
ls #enjoy the choice
cat cycle_count
```

### Adding Swap file

Adding swap file to the system (on the root filesystem), as per [this article](https://www.digitalocean.com/community/tutorials/how-to-add-swap-space-on-ubuntu-20-04).

```bash
sudo swapon --show #shows if swap is available and used
free --giga -h #shows the RAM
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
sudo swapon --show
echo "/swapfile    none    swap    sw    0   0" >> /etc/fstab
```



## Shell constructs

```bash
$(output=($(host $(hostname)));echo ${output[3]}) #give external IP address of the machine configured hostname

$ echo $(output=($(host $(hostname)));echo ${output[3]}) 
IP

$ hostname
domain.com

$ host domain.com
domain.com has address IP

$ echo $(output=($(host $(hostname)));echo ${output[3]})
IP
```

### Lifehacks

How to download `dpkg` files for the computer, that doesn't have internet connection (as per this [article](https://stackoverflow.com/a/26239050/2188026)) - on the 'victim' machine do:

```bash
apt-get --print-uris --yes install <my_package_name> | grep ^\' | cut -d\' -f2 >downloads.list
```

Then on the machine having internet access:

```bash
wget --input-file myurilist
```

`fdisk -l` and `mount /dev/sda1 /mnt` are other useful commands in command line interface without GUI.

Search for the file in all of the packages (you have the file and don't know which one you need):

```bash
apt-file search file -> search for the package where this file is in
```

### One liners

```bash
ls -l /var/run/reboot-required #check if reboot is required, after the apt upgrade
```

```bash
sudo update-alternatives --config editor #change default editor
```

OR
```
echo 'SELECTED_EDITOR="/usr/bin/vim"' > .selected_editor
```

```bash
sudo dpkg-reconfigure tzdata #change timezone
```

```bash
sudo netstat -tulpn #show open ports
```

```bash
systemd-resolve --status #show DNS configuration
```

```bash
#fixing GPG “NO_PUBKEY” error
sudo apt-key adv --keyserver keyserver.ubuntu.com --recv-keys MISSING_KEY
```
```bash
ubuntu-distro-info --supported | grep `lsb_release -a 2>/dev/null | grep -i codename | awk '{print $2}'` | wc -l # checking if Ubuntu is supported (1 - if yes; 0 - if not)
```


**Creating users**

```bash
NEWUSER='alex'
sudo adduser $NEWUSER
sudo usermod -aG sudo $NEWUSER #add user to sudo group, to enable passwordless sudo
rsync --archive --chown=$NEWUSER:$NEWUSER ~/.ssh /home/$NEWUSER #copy SSH keys
# OR
sudo su - $UserName
mkdir .ssh && cd .ssh
touch authorized_keys && vi authorized_keys && chmod 600 authorized_keys
```

```bash
lsof -nP -iTCP -sTCP:LISTEN #MacOS X - find which apps listen which port
```

## NTP
```bash
systemctl status systemd-timesyncd # get the servers list
cat /etc/systemd/timesyncd.conf # config
timedatectl
timedatectl timesync-status
timedatectl show-timesync
systemctl restart systemd-timesyncd # to restart
```
### Hostname change (Ubuntu)

```bash
sudo hostnamectl set-hostname $NewHostname
sudo vi /etc/hosts
hostnamectl # to verify
```

**Mount another disk on Ubuntu (useful for recovery)**

```bash
sudo lsblk -o NAME,FSTYPE,SIZE,MOUNTPOINT,LABEL
sudo mount /dev/... /mnt
```


## Recover encrypted disk

```bash
sudo cryptsetup luksOpen /dev/nvme0n1p3 ssd
sudo vgchange -ya
sudo mount /dev/vgmint/root /mnt
...
sudo umount /dev/mapper/cryptdev
sudo vgchange -a n
sudo cryptsetup close cryptdev
```

## Recover grub
```
sudo mkdir /mnt/efi
sudo mount /dev/nvme0n1p1 /mnt/efi
sudo grub-install --root-directory=/mnt/efi /dev/nvme0n1p1 # not sure about the destination
```


# Networking on Ubuntu

## unbound troubleshooting

[docs](https://unbound.docs.nlnetlabs.nl/en/latest/getting-started/configuration.html)

```bash
systemctl stop unbound
unbound -dd -vvvvv
```

### DNS
DNS is failing for some reason on Ubuntu behind firewall:
```
# sudo systemctl status systemd-resolved # to see if it's failing
# sudo systemctl start systemd-resolved # to start it up
sudo resolvectl status # shows DNS servers in use
```

The content below is only for Ubuntu 18.04 and higher (the network has been changed dramatically in 18.04).

### iptables port forward
```bash
iptables -t nat -A PREROUTING -p tcp --dport 443 -j DNAT --to-destination <destination-ip>:27619
iptables -t nat -A POSTROUTING -j MASQUERADE
```
AND - make it persistent!
### iptables perstistency

[Ubuntu ref](https://help.ubuntu.com/community/IptablesHowTo)

`vi /etc/network/if-pre-up.d/iptablesload && chmod +x /etc/network/if-pre-up.d/iptablesload`

```bash
#!/bin/sh
iptables-restore < /etc/iptables.rules
exit 0
```

To save, do:
```bash
iptables-save > /etc/iptables.rules
```

### UFW on top of Docker (as per [the doc](https://github.com/chaifeng/ufw-docker))
``` bash
sudo ufw default allow incoming
sudo ufw default allow outgoing
sudo ufw enable

sudo wget -O /usr/local/bin/ufw-docker \
  https://github.com/chaifeng/ufw-docker/raw/master/ufw-docker
sudo chmod +x /usr/local/bin/ufw-docker
sudo ufw-docker install
sudo systemctl restart ufw
sudo ufw-docker check
```

### **Firewall check**

```bash
ufw status verbose
iptables -S
iptables -nvL
iptables -L -n -t nat # NAT
```

### iptables cleanup
as [per](https://serverfault.com/a/200658) 
```bash
iptables -P INPUT ACCEPT
iptables -P FORWARD ACCEPT
iptables -P OUTPUT ACCEPT
iptables -t nat -F
iptables -t mangle -F
iptables -F
iptables -X
```

### Basic firewall rules** ([ref](https://www.digitalocean.com/community/tutorials/how-to-set-up-a-firewall-with-ufw-on-ubuntu-18-04#step-2-%E2%80%94-setting-up-default-policies))

```bash
sudo ufw allow ssh
sudo ufw allow proto tcp from any to any port 80,443 #HTTP & HTTPS
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw show added #shows rules, without enabling firewall
sudo ufw status numbered #shows rules, numbered
sudo ufw delete 2 #remove the rule
sudo ufw enable
sudo ufw disable
```

## Enabling NAT (as per [article](https://askubuntu.com/questions/1050816/ubuntu-18-04-as-a-router))

as per [ref](https://gist.github.com/kimus/9315140), [[2025-02-22]]:

```bash
sudo apt -y install ufw
sudo sed -i 's/DEFAULT_FORWARD_POLICY="DROP"/DEFAULT_FORWARD_POLICY="ACCEPT"/' /etc/default/ufw
sudo sed -i 's/DEFAULT_INPUT_POLICY="DROP"/DEFAULT_INPUT_POLICY="ACCEPT"/' /etc/default/ufw
grep FORWARD_POLICY /etc/default/ufw
grep INPUT_POLICY /etc/default/ufw
sudo sed -i 's|#net/ipv4/ip_forward=1|net/ipv4/ip_forward=1|' /etc/ufw/sysctl.conf
grep ip_forward /etc/ufw/sysctl.conf

echo '
# NAT table rules
*nat
:POSTROUTING ACCEPT [0:0]

# CHANGE ME: IP address of LAN and interface of WAN
-A POSTROUTING -s 172.17.1.2/30 -o eth0 -j MASQUERADE

COMMIT
' | cat - /etc/ufw/before.rules > /tmp/before_rules.full && cp /tmp/before_rules.full /etc/ufw/before.rules

sudo ufw show added #check status

sudo ufw disable && sudo ufw enable
```

**Limiting an access for a specific network interface** ([ref](https://serverfault.com/questions/270715/ubuntu-ufw-set-a-rule-on-a-per-interface-basis))

> By default, ufw will apply rules to all available interfaces. To
limit  this,  specify DIRECTION on INTERFACE, where DIRECTION is
one of in or out (interface aliases  are  not  supported).   For
example,  to  allow  all  new incoming http connections on eth0,
use:

ufw allow in on eth0 to any port 80 proto tcp
> 

```bash
ufw allow in on eth1 to [eth1 ip addr] port 80 proto tcp
```

So, denying everything on public port and only enabling specific things would looks like the following:

```bash
sudo ufw default deny incoming on ens3 #default to public deny
sudo ufw allow in on ens4 from any to any #allow everything on LAN
sudo ufw allow out on ens4 from any to any #allow everything on LAN
sudo ufw enable #do disk snapshot first!

sudo ufw allow proto tcp on ens3 from any to any port 22
sudo ufw allow proto tcp from 10.66.66.0/24 to any port 80,443 #allow traffic via LAN

sudo ufw allow from 192.168.168.0/24 #allow from internal network
 
```

**Basic security features**

Move SSHd to another port

```bash
sudo vi /etc/sshd/sshd_config #change Port's 22 to anything you like
sudo service sshd restart #it shall be available on a new port

```

### Troubleshooting connections (good [doc here](https://help.mulesoft.com/s/article/How-to-capture-network-traffic-between-two-systems))

```bash
sudo tcpdump -vvv -n host IP
sudo tcpdump -vvv -i ens3 host IP port 22
sudo tcpdump -n -vvv -i ens3 'host IP and port 22'

```

pwru as well:
```
/pwru 'src host <source-ip>'
```

### Configuring second network interface

<aside>
❗ DO NOT SPECIFY gateway4 - it's a [default gateway for all traffic](https://askubuntu.com/questions/1062902/ubuntu-18-04-netplan-static-routes), on all interfaces - unless you really know what to do.
It overrides the DHCP settings and you will lose access to your server.

</aside>

<aside>
❗ DO NOT USE TABS in YML files. Not on Ubuntu 18.04 at least. That break netplan ⇒ loosing network access to the server.

</aside>

<aside>
💡 It's safe to make configuration change in a separate file, then try out things with `sudo netplan --debug try --config-file ~/50-cloud-init.yaml`

</aside>

**Ubuntu 18.04 ([ref](https://serverspace.io/support/help/how-to-configure-static-ip-address-on-ubuntu-18-04/))**

```bash
cd /etc/netplan && ls
sudo vi 50-cloud-init.yaml

#file name starts with 50 something; it won't be overridden, as it's generated during the first init
```

Here is the resulting example file:

```bash
network:
    ethernets:
        ens3:
            addresses: []
            dhcp4: true
            optional: true
        **ens4:
               addresses: [192.168.168.10/24, ]**

    version: 2
```

```bash
sudo netplan --debug apply
```

**Ubuntu 20.04 ([ref](https://ostechnix.com/how-to-configure-ip-address-in-ubuntu-18-04-lts/))**

```bash
cd /etc/netplan && ls
sudo vi 01-netcfg.yaml
sudo netplan try
sudo netplan --debug apply
```

Here is the resulting example file:

```bash
network:
  ethernets:
    ens4:
      dhcp4: no
      addresses: 
        - 192.168.168.1/24

  version: 2
```

**Setting up routing for the second interface** (18.04; [ref](https://askubuntu.com/questions/1062902/ubuntu-18-04-netplan-static-routes/1062931#1062931?newreg=e938644cf7284879aa6c41b97ddad51c))

***Temporary* one:**

```bash
sudo route add -net 10.0.0.0/8 gw 192.168.1.1 eth0
sudo route del -host IP gw 192.168.168.1 ens4
sudo route add -host IP gw 192.168.168.10 ens4
sudo route add default gw 192.168.168.1 ens4
```

**Permanent one:**

```bash
sudo vi /etc/netplan/50-cloud-init.yaml
```

And add routes directive:

```bash
ens4:
               addresses: [192.168.168.10/24, ]
               routes:
                       - to: 10.0.0.0/8
                         via: 192.168.168.1
```

Check kernel level packets forward:

```bash
cat /proc/sys/net/ipv4/ip_forward
```

### Single interface configuration netplan:

```bash
network:
    ethernets:
        ens3:
               addresses: [192.168.168.22/24, ]
               gateway4: 192.168.168.1 
               routes:
                       - to: 10.0.0.0/8
                         via: 192.168.168.1
    version: 2
```

### One liners

Extract external IP address and add `1` at the end - which is usually a gateway.

```bash
ip addr show ens3 | awk '/inet/ {print $2}' | cut -d/ -f1 | head -1 | awk -F '.' '{ print $1"."$2"."$3"."1;}
```

or use 

```bash
sudo apt-get install sipcalc
sipcalc -I ens3
```

that gives first server in the network (which is usually a gateway)

```bash
sipcalc -I ens3 -i | grep "Usable range" | cut -d "-" -f 2 | xargs
```

Temporary setup default router

```bash

sudo route add default gw `sipcalc -I ens3 -i | grep "Usable range" | cut -d "-" -f 2 | xargs` ens3

```

Revoke routing back

```bash
sudo route del default gw `sipcalc -I ens3 -i | grep "Usable range" | cut -d "-" -f 2 | xargs` ens3
```



# Ubuntu - Remap your mouse button(s)

Used it to map third button for 'Expose' like.

sudo apt install git python3-setuptools gettext
git clone [https://github.com/sezanzeb/key-mapper.git](https://github.com/sezanzeb/key-mapper.git)
cd key-mapper && ./scripts/build.sh
sudo apt install ./dist/key-mapper-1.2.1.deb

keyboard → shortcuts → show the window selection screen → map some key (F7 in my case), then add desired button (middle mouse button in my case) to F7 - enjoy!