# webp to png

```
for x in ls *.webp; do ffmpeg -i $x ${x%.webp}.png; done
```

# Installation
```
brew install ffmpeg
```