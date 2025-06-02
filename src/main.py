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

from jellyfinclient import scan_jellyfin_library


# Constants
DEEZER_BASE_URL = "https://deezer.com/us"
CONFIG_FILE = os.environ.get("CONFIG_FILE")

# Config Manager
cm = None


def check_constants():
    if not CONFIG_FILE:
        print("Env var CONFIG_FILE not defined! Exiting.")
        exit(1)


def check_for_new_download_requests(dc):
    global cm

    download_path = cm.get_value("downloads", "music_download_path")
    jellyfin_url = cm.get_value("jellyfin", "server_url")
    jellyfin_api_key = cm.get_value("jellyfin", "api_key")

    # Get the list of Unread notifications of the Bot account
    notifications = list(
            filter(
            lambda n: n["read"] == False,
            dc.get_user_notifications()
        )
    )

    print("[DOWNLOAD] Bot account unread notifications :")

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

        print(f"[DOWNLOAD] Starting {url_type} download...")

        # Download item
        match url_type:
            case "track":
                download_track(download_path, notif_shared_url)
            
            case "album":
                download_album(download_path, notif_shared_url)
            
            case "playlist":
                download_playlist(download_path, notif_shared_url)

            case _:
                print("Error: unknown url type")
                continue
        
        print(f"[DOWNLOAD] {url_type} downloaded.\n".capitalize())

        # Mark Deezer notification as Read
        dc.mark_notification_as_read(notif_id)

        # Scan Jellyfin library for new songs
        jellyfin_scan_result = scan_jellyfin_library(jellyfin_url, jellyfin_api_key)
        print(jellyfin_scan_result["message"])


def check_download_requests_thread(dc):
    """
    Check for new download request every hour
    """
    import time

    while True:
        print("[DOWNLOAD] Checking for new download requests")
        check_for_new_download_requests(dc)
        print("[DOWNLOAD] Checked for new download requests. Checking back in an hour.")
        time.sleep(60 * 60)


def check_for_new_friend_requests(dc):
    followers = dc.get_users_page_profile("followers")
    followers = [ user["USER_ID"] for user in followers ]

    following = dc.get_users_page_profile("following")
    following = [ user["USER_ID"] for user in following ]

    users_not_followed = [ user_id for user_id in followers if user_id not in following ]

    for user in users_not_followed:
        print(f"[FRIENDS] User {user} not followed, following user...")
        dc.follow_user(user)
    

def check_friend_request_thread(dc):
    """
    Check for new followers every minute
    """
    import time

    while True:
        print("[FRIENDS] Checking for new followers")
        check_for_new_friend_requests(dc)
        print("[FRIENDS] New followers checked. Checking back in a minute.")
        time.sleep(60)


def main():
    import threading
    from config import ConfigManager

    # Check for undefined constants
    check_constants()

    # Load config
    global cm
    cm = ConfigManager(CONFIG_FILE)

    # Init Deezer
    dc = DeezerClient(cm.get_value("deezer", "bot_arl_cookie"))

    # Only hardlinks are supported by Jellyfin
    set_should_use_links_for_duplicates(True)
    set_duplicates_links_type("HARDLINK")

    # Check for new followers and follow back thread
    friend_requests_thread = threading.Thread(target=check_friend_request_thread, args=(dc,))
    friend_requests_thread.start()

    # Check for download requests via notifications thread
    download_requests_thread = threading.Thread(target=check_download_requests_thread, args=(dc,))
    download_requests_thread.start()


if __name__ == "__main__":
    main()
