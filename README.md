# Deezer-DL BOT

Deezer DL bot for Jellyfin. The bot will periodically check for new follows and will follow back to allow sharing playlists/albums or tracks to the bot. Every hour, the bot will check for new share notifications and will download the music, and then update the Jellyfin library.

## Requirements
- pipx
- Deezer __Bot account__ ARL cookie
- Jellyfin API token

## Install
`pipx install git+ssh://git@github.com/MaximeSahuc/deezer-dl-bot.git --force`

## Setup
```bash
DEEZER_COOKIE_ARL="01234...56789" \
MUSIC_DOWNLOAD_DIR="/path/to/jellyfin/data/media/Music/" \
JELLYFIN_SERVER_URL="https://jellyfin.foo.bar" \
JELLYFIN_API_KEY="11de10c9368627286f0377f69f42c7d4" \
deezer-dl-bot
```