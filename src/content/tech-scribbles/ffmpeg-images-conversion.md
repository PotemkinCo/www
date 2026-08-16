---
title: "ffmpeg (images conversion)"
---

# webp to png

```bash
for x in ls *.webp; do ffmpeg -i $x ${x%.webp}.png; done
```

# Installation
```bash
brew install ffmpeg
```
