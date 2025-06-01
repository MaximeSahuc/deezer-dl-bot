#!/usr/bin/env python3

import os

from deezerclient import DeezerClient
from deezer.download import (
    download_playlist,
    download_album,
    download_track,
    set_should_use_links_for_duplicates,
    set_duplicates_links_type
)

from jellyfinutils import scan_jellyfin_library


# Deezer constants
DEEZER_BASE_URL = "https://deezer.com/us"
DEEZER_COOKIE_ARL = os.environ.get("DEEZER_COOKIE_ARL")
MUSIC_DOWNLOAD_DIR = os.environ.get("MUSIC_DOWNLOAD_DIR")

# Jellyfin constants
JELLYFIN_SERVER_URL = os.environ.get("JELLYFIN_SERVER_URL")
JELLYFIN_API_KEY = os.environ.get("JELLYFIN_API_KEY")


def check_constants():
    if not DEEZER_COOKIE_ARL:
        print("Env var DEEZER_COOKIE_ARL not defined! Exiting.")
        exit(1)

    if not MUSIC_DOWNLOAD_DIR:
        print("Env var MUSIC_DOWNLOAD_DIR not defined! Exiting.")
        exit(1)
    
    if not JELLYFIN_SERVER_URL:
        print("Env var JELLYFIN_SERVER_URL not defined! Exiting.")
        exit(1)
    
    if not JELLYFIN_API_KEY:
        print("Env var JELLYFIN_API_KEY not defined! Exiting.")
        exit(1)


def main() -> int:
    # Check for undefined constants
    check_constants()

    # Init Deezer
    dc = DeezerClient(DEEZER_COOKIE_ARL)

    # Only hardlinks are supported by Jellyfin
    set_should_use_links_for_duplicates(True)
    set_duplicates_links_type("HARDLINK")

    # Get the list of Unread notifications of the Bot account
    notifications = list(
            filter(
            lambda n: n["read"] == False,
            dc.get_user_notifications()
        )
    )

    print("\n\n\n")
    print("Bot account unread notifications :")

    if len(notifications) == 0:
        print("No notifications")
        return 0
    
    print()
    
    for notif in notifications:
        notif_title = notif["title"]
        notif_id = notif["id"]
        notif_shared_url = f"{DEEZER_BASE_URL}{notif['url']}"
        url_type = notif['url'].split("/")[1]

        print("-" * 30)
        print(f"Title: {notif_title}")
        print(f"Id: {notif_id}")
        print(f"Type: {url_type}")
        print(f"Url: {notif_shared_url}")
        print("-" * 30)
        print("\n")

        print(f"Starting {url_type} download...")

        # Download item
        match url_type:
            case "track":
                download_track(MUSIC_DOWNLOAD_DIR, notif_shared_url)
            
            case "album":
                download_album(MUSIC_DOWNLOAD_DIR, notif_shared_url)
            
            case "playlist":
                download_playlist(MUSIC_DOWNLOAD_DIR, notif_shared_url)

            case _:
                print("Error: unknown url type")
                continue
        
        print(f"{url_type} downloaded.\n\n".capitalize())

        # Mark Deezer notification as Read
        dc.mark_notification_as_read(notif_id)

        # Scan Jellyfin library for new songs
        jellyfin_scan_result = scan_jellyfin_library(JELLYFIN_SERVER_URL, JELLYFIN_API_KEY)
        print(jellyfin_scan_result["message"])

    return 0

if __name__ == "__main__":
    raise SystemExit(main())