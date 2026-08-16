## Initial config

Increase rate limit from 10 to 75 to avoid 429 http error and slow / stupid initial launch of the app.

### Change channel to public

```bash
sudo -u cloudron /app/code/bin/mattermost --config=/app/data/config.json channel modify $teamid:$channelname --username $username --public
```

Other command line arguments: [https://docs.mattermost.com/administration/command-line-tools.html#mattermost-channel-modify](https://docs.mattermost.com/administration/command-line-tools.html#mattermost-channel-modify)


# MatterMost tips and tricks

To add repository to the channel (after all of the preparations has been made).

```bash
/github subscriptions add Potemkin-Co/repo_name pulls,pushes,creates,deletes,pull_reviews
```


Disable github reminders:
```
/github settings reminders off 
```