---
title: "Hetzner"
---

# Adding HW

List: https://docs.hetzner.com/robot/dedicated-server/dedicated-server-hardware/price-server-addons/

41EUR is to install drives in mint condition 

## Storage box

[Docs ref](https://docs.hetzner.com/robot/storage-box/access/access-ssh-rsync-borg/#rclone).
```bash
ssh-keygen -f hetzner
cat hetzner_box.pub | ssh -p23 uXXXXX-sub1@uXXXXX.your-storagebox.de install-ssh-key

vi ~/.config/rclone/rclone.conf
```
```ini
[storagebox]
type = sftp
host = uXXXXX.your-storagebox.de
user = uXXXXX
port = 23
pass = <obscured-password>
```
`rclone obscure <clear-text-password>` is to generate obsured password
and `rclone ls storagebox:` to verify.

`rclone configure` to configure encryption.

### Troubleshooting
From the server:
- `nc -vv uXXXXX.your-storagebox.de 23`
- `sshfs -p23 uXXXXX@uXXXXX.your-storagebox.de:/home ./tmp_test -o IdentityFile=~/.ssh/hetzner_storage_box`


## iGPU processors on Intel CPUs

### Enabling
Enabling for iGPU processors on Hetzner servers, as per [article](https://community.hetzner.com/tutorials/howto-enable-igpu).
i7 processor [is](https://ark.intel.com/content/www/us/en/ark/products/88196/intel-core-i7-6700-processor-8m-cache-up-to-4-00-ghz.html) of 6th generation and it [does have](https://ark.intel.com/content/www/us/en/ark/products/88196/intel-core-i7-6700-processor-8m-cache-up-to-4-00-ghz.html) iGPU.
```bash
ls -la /dev/dri # expected to fail -> iGPU is disabled
vi /etc/modprobe.d/blacklist-hetzner.conf # comment out (disabled) i915 & i915_bdw
vi /etc/default/grub.d/hetzner.cfg # at GRUB_CMDLINE_LINUX_DEFAULT, 'nomodeset' to be removed
sudo grub-mkconfig -o /boot/grub/grub.cfg
sudo shutdown -r now
ls -la /dev/dri # shall give devices list
sudo lspci -v -s $(lspci | grep VGA | cut -d" " -f 1) # shall contain 'Kernel driver in use: i915'
sudo apt install intel-gpu-tools
sudo intel_gpu_top
```

### Getting VRAM size
[ref](https://askubuntu.com/a/475405)
```bash
LC_ALL=C lspci -v | grep -EA10 "3D|VGA" | grep 'prefetchable'
```

### llama.cpp & whisper.cpp backends
- Vulkan - can run solely on iGPU
- SYCL -supports iGPU of Intel starting with Intel 11th generation
- Blis - seems to be CPU only
- OpenVINO - supports many cards, including iGPU

`nvtop` could be used on a newer systems (>5.19 kernel; `snap install nvtop` to get the latest).

But on Intel it seems like it could get increase, as required.

Intel(R) Core(TM) i7-7700 CPU @ 3.60GHz
It's Intel Corporation HD Graphics 630 @ Intel Kabylake (Gen9)
Memory at ee000000 (64-bit, non-prefetchable) [size=16M]
	Memory at d0000000 (64-bit, prefetchable) [size=256M]
Supported by Vulkan ([ref](https://en.wikichip.org/wiki/intel/microarchitectures/gen9.5)).
It has 24 execution units but [no embedded DRAM](https://en.wikichip.org/wiki/intel/hd_graphics_630) 
SYSCL backend [supports Intel 11 gen and above](https://github.com/ggerganov/llama.cpp/blob/master/docs/backend/SYCL.md#hardware). Probably, Vulkan might work, but I can't see Linux references.
- And yeah - whisper [won't work via SYCL framework](https://github.com/openai/whisper/pull/1362#issuecomment-1554305455).
- StableDiffusion - [probably](https://www.reddit.com/r/StableDiffusion/comments/xfivq3/running_stable_diffusion_on_windows_10_with_intel/) (needs [research](https://www.google.com/search?q=intel+hd+graphics+630+stable+diffusion&newwindow=1&client=safari&sca_esv=00358603c58a2193&rls=en&sxsrf=ADLYWIIKlpbU5345Lau_YMllRpsQqW2fHA%3A1723999163979&ei=uyPCZri-O9Gdi-gPzqK4mAY&oq=intel+HD+Graphics+630+stabl&gs_lp=Egxnd3Mtd2l6LXNlcnAiG2ludGVsIEhEIEdyYXBoaWNzIDYzMCBzdGFibCoCCAAyBhAAGBYYHjILEAAYgAQYhgMYigUyCxAAGIAEGIYDGIoFMggQABiiBBiJBUjvD1CHAlj8CHABeAGQAQCYAXqgAYkFqgEDMi40uAEDyAEA-AEBmAIHoAKvBcICBxAjGLADGCfCAgoQABiwAxjWBBhHwgIEECMYJ8ICCxAAGIAEGJECGIoFwgIFEAAYgATCAggQABiABBiiBJgDAIgGAZAGBpIHAzIuNaAH3yU&sclient=gws-wiz-serp)); wonder if I can run [FLUX](https://github.com/black-forest-labs/flux) on it
- Llama interference - needs [research](https://www.google.com/search?newwindow=1&client=safari&sca_esv=00358603c58a2193&rls=en&sxsrf=ADLYWIIGu3z3R8aXViTl_eBy95FecSSv7Q:1723999295013&q=intel+hd+graphics+%22630%22+llama.cpp&sa=X&ved=2ahUKEwjX1Mns_f6HAxVWzgIHHUmxKGYQ5t4CegQIHBAB&biw=1343&bih=752&dpr=2), but seems like blis is an option to try.
- might work for ffmpeg, if I have it

Intel's 11th generation CPUs [seems](https://en.wikipedia.org/wiki/Rocket_Lake) to start with 11400 and above.

Blis framework seems to be very interesting to run on CPU and GPU ([ref](https://www.bell-labs.com/research-innovation/projects-and-initiatives/software-and-data-systems-research/aiml-systems/our-research-projects/blis/)), HW compatibility: https://github.com/flame/blis/blob/master/docs/HardwareSupport.md
```bash
git clone https://github.com/flame/blis
cd blis
./configure --enable-cblas -t openmp,pthreads auto
make -j
sudo make install
cd ..
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp
make GGML_BLIS=1 -j
LD_LIBRARY_PATH=/usr/local/lib ./llama-cli -m your_model.gguf -p "I believe the meaning of life is" -n 128
```
That works, not sure how fast, but it doesn't pick up my iGPU.

- [x] Try Vulkan on Linux as per [ref](https://github.com/ggerganov/llama.cpp/blob/master/docs/build.md#vulkan)  [completion:: 2024-08-18]
```bash
sudo su -
wget -qO - https://packages.lunarg.com/lunarg-signing-key-pub.asc | apt-key add -
# it's for Ubuntu 22.04! 24.04 shall be picked up from https://vulkan.lunarg.com/doc/view/latest/linux/getting_started_ubuntu.html
wget -qO /etc/apt/sources.list.d/lunarg-vulkan-jammy.list https://packages.lunarg.com/vulkan/lunarg-vulkan-jammy.list
apt update -y
apt-get install -y vulkan-sdk
# To verify the installation, use the command below:
vulkaninfo
vkvia # needs X11

git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

sudo apt install cmake libvulkan-dev
cmake -B build -DGGML_VULKAN=1
cmake --build build --config Release
# Test the output binary (with "-ngl 33" to offload all layers to GPU)
./build/bin/llama-cli -m "PATH_TO_MODEL" -p "Hi you how are you" -n 50 -e -ngl 33 -t 4

# You should see in the output, ggml_vulkan detected your GPU. For example:
# ggml_vulkan: Using Intel(R) Graphics (ADL GT2) | uma: 1 | fp16: 1 | warp size: 32
```

Yep - that works! First launch is slow, but then it's much faster! Running via CPU seems to be faster, which is mostly due to low VRAM, I believe. But there is no load on CPU, which is good.

[Whisper supports OpenVINO](https://github.com/ggerganov/whisper.cpp?tab=readme-ov-file#openvino-support) and [OpenVINO seems to support 630's card](https://stackoverflow.com/questions/54423407/openvino-for-intel-hd-graphic). The question remains is how to allocate more memory in there.

- Compile and try to run Whisper with OpenVINO as per [ref](https://github.com/ggerganov/whisper.cpp?tab=readme-ov-file#openvino-support)
```bash
git clone https://github.com/ggerganov/whisper.cpp.git
cd whisper
bash ./models/download-ggml-model.sh large-v3
cd models
python3.11 -m venv openvino_conv_env # 3.12 requires numpy woodoo: https://stackoverflow.com/questions/77364550/attributeerror-module-pkgutil-has-no-attribute-impimporter-did-you-mean/77364602#77364602
source openvino_conv_env/bin/activate
# python -m pip install --upgrade pip
# pip install setuptools
# pip install numpy==1.26.4 # for Python 3.12+
pip install -r requirements-openvino.txt
pip install openai-whisper
python convert-whisper-to-openvino.py --model large-v3
# This will produce ggml-base.en-encoder-openvino.xml/.bin IR model files. It's recommended to relocate these to the same folder as ggml models, as that is the default location that the OpenVINO extension will search at runtime.
ls ggml-base.en-encoder-openvino.*
# download https://github.com/openvinotoolkit/openvino/releases/tag/2023.0.0
sudo mkdir /opt/intel
# 24.04 instructions!
curl -L https://storage.openvinotoolkit.org/repositories/openvino/packages/2024.3/linux/l_openvino_toolkit_ubuntu24_2024.3.0.16041.1e3b88e4e3f_x86_64.tgz --output openvino_2024.3.0.tgz
tar -xf openvino_2024.3.0.tgz
sudo mv l_openvino_toolkit_ubuntu24_2024.3.0.16041.1e3b88e4e3f_x86_64 /opt/intel/openvino_2024.3.0
cd /opt/intel/openvino_2024.3.0
sudo -E ./install_dependencies/install_openvino_dependencies.sh
cd /opt/intel
sudo ln -s openvino_2024.3.0 openvino_2024
source /opt/intel/openvino_2024/setupvars.sh


# python -c "from openvino import Core; print(Core().available_devices)"
cd ..
cmake -B build -DWHISPER_OPENVINO=1
cmake --build build -j --config Release
 ./main -m models/ggml-base.en.bin -f samples/jfk.wav
 # The first time run on an OpenVINO device is slow, since the OpenVINO framework will compile the IR (Intermediate Representation) model to a device-specific 'blob'. This device-specific blob will get cached for the next run.

mkdir neo
cd neo
wget https://github.com/intel/intel-graphics-compiler/releases/download/igc-1.0.17193.4/intel-igc-core_1.0.17193.4_amd64.deb
wget https://github.com/intel/intel-graphics-compiler/releases/download/igc-1.0.17193.4/intel-igc-opencl_1.0.17193.4_amd64.deb
wget https://github.com/intel/compute-runtime/releases/download/24.26.30049.6/intel-level-zero-gpu-dbgsym_1.3.30049.6_amd64.ddeb
wget https://github.com/intel/compute-runtime/releases/download/24.26.30049.6/intel-level-zero-gpu_1.3.30049.6_amd64.deb
wget https://github.com/intel/compute-runtime/releases/download/24.26.30049.6/intel-opencl-icd-dbgsym_24.26.30049.6_amd64.ddeb
wget https://github.com/intel/compute-runtime/releases/download/24.26.30049.6/intel-opencl-icd_24.26.30049.6_amd64.deb
wget https://github.com/intel/compute-runtime/releases/download/24.26.30049.6/libigdgmm12_22.3.20_amd64.deb
sudo dpkg -i *.deb

./main -m ../../models/ggml-large-v3.bin -f ../../samples/jfk.wav -oved GPU # that works
```

It's a bit faster, when with GPU (76 seconds vs 105-120), but loads CPU all the same. But yeah - it works and it's faster. Experiment finished 2024-08-23.

## Adding second IP address

[ref](https://docs.hetzner.com/robot/dedicated-server/network/net-config-debian-ubuntu/#additional-ip-addresses-virtualization)

Add the ip address with /32 mask to netplan configuration.
Check with `ip address list` command. This way an interface will have two IP addresses.

For virtualization purposes, routing and bridge interface has to be configured. As of 2024-07-29, I don't fucking know how.

Seems like configuring a bridge and configuring multipass is an option: [ref](https://multipass.run/docs/configure-static-ips). But it feels so much complicated for me... 

iptables are in use at Multipass.

And it seems like packets forward might just work. Probably, [smth like that](https://superuser.com/questions/1287771/iptables-how-to-keep-source-ip-after-forwarding). ufw doesn't offer ip masquerading. Ok.

btw, probably, a simple socat might work. Or, manually rolled out Synapse server. I will leave it here, as is, for now. Verified - now, I don't want to manually re-roll-out Synapse server only - I will need to re-setup mail, database, updates, etc - doable, but why?

## Firewall

Robot Firewall - can have 10 rules only; up to 3 ports can be specified via comma.

# IPv6 addresses info

Basically all dedicated root servers at Hetzner from our AX-, DX-, EX-, RX-, SX- lines, all servers from the server auction and all cloud (virtual) servers are fully unmanaged with full „root“ access. That means, you have to administer the management of configuration and software (including OS and software installation, backup, monitoring, etc.) of the server yourself. For dedicated root and virtual servers, we only provide the hardware, network access and necessary infrastructure; and of course, we support our customers in case there are any failures or disruptions. Unfortunately, we don't offer software support in general.

Our clients sometimes engage experts as consultants or a partner to handle adminstrative tasks,  if they feel overwhelmed by the efforts involved.

> May I ask you for some documents / guide / smth on how I do connect 
> extra IPv6 address to my server?

Feel free to explore a wealth of information in our Hetzner Docs:
[https://docs.hetzner.com/](https://docs.hetzner.com/)

Please go to our site and ask the AI Bot: "how to configure IPv6 addresses with a Hetzner dedicated root server?"
[https://www.hetzner.com/dedicated-rootserver/](https://www.hetzner.com/dedicated-rootserver/)

It will point you to these two Hetzner Docs pages:
[https://docs.hetzner.com/robot/dedicated-server/network/net-config-debian-ubuntu/#ipv6](https://docs.hetzner.com/robot/dedicated-server/network/net-config-debian-ubuntu/#ipv6)
[https://docs.hetzner.com/robot/dedicated-server/general-information/system-adjustments-after-server-replacement/#content-of-the-network-config-4](https://docs.hetzner.com/robot/dedicated-server/general-information/system-adjustments-after-server-replacement/#content-of-the-network-config-4)

There is a costfee IPv6 /64 subnet inclued with Server Auction #2439185 so you have over 18 quintillion IPv6 addresses available.

We can deliver an additional /56 IPv6 subnet at the once-off cost of € 15.00 (excl. VAT). If you would like this additional subnet, please confirm the costs.
[https://docs.hetzner.com/general/others/ipv4-pricing/#additional-56-ipv6-net-dedicated-root-servers](https://docs.hetzner.com/general/others/ipv4-pricing/#additional-56-ipv6-net-dedicated-root-servers)
