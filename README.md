# Deezer-DL BOT

Deezer DL bot for Jellyfin. The bot will periodically check for new follows and will follow back to allow sharing playlists/albums or tracks to the bot. Every hour, the bot will check for new share notifications and will download the music, and then update the Jellyfin library.


## Requirements

- pipx
- Deezer __Bot account__ ARL cookie
- Jellyfin API token


## Install

`pipx install git+ssh://git@github.com/MaximeSahuc/deezer-dl-bot.git --force`


## Launch

The program needs a `CONFIG_FILE` environment variable to specify where to store the configuration file. On the first start, the program will create a template configuration file and prompt you to configure it.

```bash
CONFIG_FILE="/path/to/your/config.yml" \
deezer-dl-bot
```