# Reverting on Pixel Tab

`sudo systemctl stop fwupd.service` then boot into bootloader:
> You need to boot your device into the bootloader interface. To do this, you need to hold the volume down button while the device boots.
> The easiest approach is to reboot the device and begin holding the volume down button until it boots up into the bootloader interface.

Open https://flash.android.com/back-to-public, on Brave disable shields and the device must appear and flash with latest public OS release.

Ref: https://grapheneos.org/install/web#prerequisites

Ещё есть тул для ремонта: https://pixelrepair.withgoogle.com/

Инструкция по `adb sideload`: https://android.stackexchange.com/questions/230999/enable-usb-debugging-through-recovery-mode-and-adb-sideload

"No command" screen to menu: https://www.reddit.com/r/AndroidQuestions/comments/uujah0/trying_to_use_recovery_mode_and_shows_no_command/

Flash with command line flashboot tool: https://source.android.com/docs/setup/test/running

