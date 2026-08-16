First of all - cockpit and not virt-manager, because cockpit is in [active development](https://github.com/cockpit-project/cockpit/releases), not like virt-manager, with the latest stable release - [2 years ago](https://github.com/virt-manager/virt-manager/releases).
[Discussion on virt-manager vs cockpit](https://arstechnica.com/civis/threads/good-gui-for-kvm.1492293/). I tried to search for 'virt-manager dead 2024' and quite many search results appeared. Guess that could mean it's stable..  

# troubleshooting

```bash
journalctl _SYSTEMD_UNIT=libvirtd.service
	auvirt --all-events # but it was empty for me at 2024-10-26
```

# libkvm resume
`virsh resume win2022-vm` - can also put it on cron, which I did

# libkvm backups

```bash
virsh dumpxml vm_name > /etc/libvirt/qemu/vm_name_backup.xml
virsh domblklist vm_name
virsh backup-begin vm1
virsh event vm1 --event block-job
virsh domjobinfo vm1 --completed
```

script to do backups:
```bash
for vm in $(virsh list --all --name) ; do
  echo "$vm:"
  virsh dumpxml "$vm" | xmlstarlet sel -t -m '/domain/devices/disk' -m 'source/@*' -v '.' -n
  echo
done
```

reference: [1](https://libvirt.org/kbase/live_full_disk_backup.html), [2](https://unix.stackexchange.com/questions/684167/how-to-export-all-vms-from-kvm-host), [3](https://www.reddit.com/r/qemu_kvm/comments/16azwdv/knowing_when_backupbegin_finishes/).

External snapshots are currently half-baked, as per [RedHat manual](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/7/html/virtualization_deployment_and_administration_guide/sect-Troubleshooting-Workaround_for_creating_external_snapshots_with_libvirt#sect-Troubleshooting-Workaround_for_creating_external_snapshots_with_libvirt).
Internal snapshots are not recommended.
# Virt-manager

Quite a [useful article on Ubuntu](https://ubuntu.com/server/docs/libvirt).
```bash
sudo apt install virt-manager # on client / admin
```
On server:
```bash
sudo apt install qemu-kvm libvirt-daemon-system
virsh list # ready to use command line interface to libkvm
```

> [!NOTE] VM won't auto-start by default!
> That has to be [configured manually](https://serverfault.com/questions/144460/how-to-automatically-start-vm-created-by-virt-manager) in VM settings.


To enable copy-paste, Spice tools has to be installed on Windows ([ref](https://gist.github.com/hakonhagland/cd6af762705d98f40b3a8db40d36a64f)): [https://www.spice-space.org/download/windows/spice-guest-tools/spice-guest-tools-latest.exe](https://www.spice-space.org/download/windows/spice-guest-tools/spice-guest-tools-latest.exe)

## Increase disk size

-1. Shutdown machine
-2. `sudo qemu-img resize  /var/lib/libvirt/images/debian11.qcow2 +20G`
That's it!

## CPU topology

RedHat [doc](https://docs.redhat.com/en/documentation/red_hat_enterprise_linux/6/html/virtualization_tuning_and_optimization_guide/sec-virt-manager-tuning-cpu-topology#sec-virt-manager-tuning-CPU-topology)

# Cockpit

Installation (as per [ref](https://cockpit-project.org/running.html#ubuntu)):
```bash
. /etc/os-release
sudo apt install -t ${VERSION_CODENAME}-backports cockpit
systemctl stop cockpit # to stop web service
```

The remains happens via web console, that is pretty much integrated in / with RedHat's one. I gave up as of 2024-08-24 - as I need something simple and fast.