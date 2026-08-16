---
title: "NextCloud"
---

# Remove login page, when OIDC enabled

`occ config:app:set --value=0 user_oidc allow_multiple_user_backends` in terminal
Ref: https://github.com/nextcloud/user_oidc/?tab=readme-ov-file#disable-other-login-methods
Discussion: https://forum.cloudron.io/post/100636

> [!NOTE] Admin's can still override that...
> ... by adding the `?direct=1` parameter to the login URL.
