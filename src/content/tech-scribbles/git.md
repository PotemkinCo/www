---
title: "git"
---

`You have divergent branches and need to specify how to reconcile them.` error on `git pull` to get latest updates.

means there are local changes that will get lost and has to be dealt with:
```bash
git diff # shows local changes - they has to be reverted / commited
git pull --ff-only # one magic step to deal with
git pull origin main --rebase # another magic trick
git reset --hard # reset local changes
```

```bash

git config credential.helper store
git pull # to get password prompt
```
