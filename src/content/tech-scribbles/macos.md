---
title: "MacOS"
---

# MacOS


## Flatten PDF file
```bash
brew install imagemagick
convert -density 150 document_original.pdf document_flat.pdf
```

## Disable closing apps automatically

```bash
defaults write -g NSDisableAutomaticTermination -bool yes
```

## Remove exif info from photo or video
```bash
brew install exiftool
exiftool -overwrite_original -All= FILENAME
```

## iCloud sync
```bash
fileproviderctl domain list
fileproviderctl check -f
fileproviderctl check -v # show details
fileproviderctl repair -v # risky
```

The following command could be used to remove empty files - with confirmation:
```bash
find ./ -type f -size 0 -exec rm -i {} \;
```

## Screen resolution
[https://www.walvisions.com/PattPages/1-complex_test.html](https://www.walvisions.com/PattPages/1-complex_test.html)

## High Quality Bluetooth Settings
To enable high quality Bluetooth settings for the headset as per [https://www.macrumors.com/how-to/enable-aptx-aac-bluetooth-audio-codecs-macos/](https://www.macrumors.com/how-to/enable-aptx-aac-bluetooth-audio-codecs-macos/):

```bash
sudo defaults write bluetoothaudiod "Enable AptX codec" -bool true
sudo defaults write bluetoothaudiod "Enable AAC codec" -bool true
```

## Hibernate

[https://www.jinx.de/SmartSleep.html](https://www.jinx.de/SmartSleep.html)

as per this [wonderful article](https://apple.stackexchange.com/a/161799/366515).

```bash
sudo pmset -a acwake 0
sudo pmset -a lidwake 0
sudo pmset -a ttyskeepawake 0
sudo pmset -a darkwakes 0
sudo pmset -a sleep 0
sudo pmset -a standby 0
sudo pmset -a standbydelay 5
sudo pmset -a hibernatemode 25
sudo pmset -a proximitywake 0
```

Checks, as per [that page](https://mackeeper.com/blog/post/366-do-you-know-what-sleep-mode-is-the-best-for-your-mac/)

```bash
pmset -g | grep hibernatemode #check current mode
pmset -g | grep sleep #shows services, that prevents hibernation
pmset -g assertions #shows triggers to wake up
pmset -g log
```

> -   **hibernatemode 0** (standard sleep)
> -   **hibernatemode 1** (hibernate mode, for pre-2005 portable MacBooks)
> -   **hibernatemode 3** (safe sleep)
> -   **hibernatemode 25** (hibernate mode for post-2005 MacBooks)

***3** - sleep by default
**25** - hibernate on my macbook*

As per [that page](https://nathansnelgrove.com/how-to-force-your-macbook-pro-to-use-its-discrete-graphics-card-when-its-plugged-in/):

```bash
# Always use the integrated graphics card while running on battery power
sudo pmset -b gpuswitch 0

# Always use the discrete graphics card while running on battery power
sudo pmset -b gpuswitch 1

# Switch between discrete and integrated graphics cards automatically while running on battery power
sudo pmset -b gpuswitch 2
```

And if you want to control this setting globally, whether your laptop is plugged in or not, you just need to change `pmset -b` to `pmset -c`.

```bash
# Always use the integrated graphics card
sudo pmset -a gpuswitch 0

# Always use the discrete graphics card
sudo pmset -a gpuswitch 1

# Automatically switch between discrete and integrated graphics card (this is your laptop's default setting)
sudo pmset -a gpuswitch 2
```

# Reset SMC & NVRAM

SMC

1. Shut down your Mac.
2. Press and hold **Shift**, **Control**, and **Option** on the **left side** of the keyboard. Now press and hold the **Power button** (or **Touch ID button**) as well.
3. Hold all the keys down for **10 seconds**.
4. Release all the keys and turn on your MacBook.

NVRAM

1. Shut down your Mac.
2. Press the **power button**.
3. Before the grey screen appears, press the **Command**, **Option**, **P**, and **R** keys at the same time.
4. Hold the keys until your computer restarts and you **hear the startup sound** a second time.
    1. On Macs with the T2 Security Chip, hold the keys until **the Apple logo appears and disappears** for the second time.
5. Release the keys

# zshrc

> .zshrc for ssh autocompletion (on MacOS)

```bash
# quickly check latest commands
alias h="history -10"

# ~/.ssh/config based ssh autocomplete
# Highlight the current autocomplete option
zstyle ':completion:*' list-colors "${(s.:.)LS_COLORS}"

# Better SSH/Rsync/SCP Autocomplete
zstyle ':completion:*:(scp|rsync):*' tag-order ' hosts:-ipaddr:ip\ address hosts:-host:host files'
zstyle ':completion:*:(ssh|scp|rsync):*:hosts-host' ignored-patterns '*(.|:)*' loopback ip6-loopback localhost ip6-localhost broadcasthost
zstyle ':completion:*:(ssh|scp|rsync):*:hosts-ipaddr' ignored-patterns '^(<->.<->.<->.<->|(|::)([[:xdigit:].]##:(#c,2))##(|%*))' '127.0.0.<->' '255.255.255.255' '::1' 'fe80::*'

# Allow for autocomplete to be case insensitive
zstyle ':completion:*' matcher-list '' 'm:{[:lower:][:upper:]}={[:upper:][:lower:]}' \
  '+l:|?=** r:|?=**'

# Initialize the autocompletion
autoload -Uz compinit && compinit -i

# iTerm2 integration
test -e "${HOME}/.iterm2_shell_integration.zsh" && source "${HOME}/.iterm2_shell_integration.zsh"
precmd() { print "" }
```

zsh ssh autocomplete integration is a courtesy of [Cody Hiar](https://www.codyhiar.com/blog/zsh-autocomplete-with-ssh-config-file/).

# Other
- install zsh autocomplete:
`brew install zsh-autocomplete`
