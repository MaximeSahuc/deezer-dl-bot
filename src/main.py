#!/usr/bin/env python3

import os

from deezer.client import DeezerClient
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

    # Get the list of Unread notifications of the Bot account
    notifications = list(
        filter(lambda n: n["read"] == False, dc.api.get_user_notifications())
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
        url_type = notif["url"].split("/")[1]
        sender_name = notif["quotation"]["title"].split()[0].strip()

        print("-" * 30)
        print(f"Title: {notif_title}")
        print(f"Id: {notif_id}")
        print(f"Type: {url_type}")
        print(f"Sender: {sender_name}")
        print(f"Url: {notif_shared_url}")
        print("-" * 30)
        print("\n")

        print(f"[DOWNLOAD] Starting {url_type} download...")

        # Determine download path
        download_path = cm.get_value("downloads", "music_download_path")
        per_user_download_directory = cm.get_value("downloads", "per_user_directory")
        if per_user_download_directory:
            download_path = os.path.join(download_path, sender_name)

        # Download item
        quality = cm.get_value("deezer", "prefered_audio_quality")
        dc.get_downloader().download_from_url(
            quality,
            notif_shared_url,
            download_path,
        )

        print(f"[DOWNLOAD] {url_type} downloaded.\n".capitalize())

        # Mark Deezer notification as Read
        dc.api.mark_notification_as_read([notif_id])

        # Scan Jellyfin library for new songs
        jellyfin_url = cm.get_value("jellyfin", "server_url")
        jellyfin_api_key = cm.get_value("jellyfin", "api_key")
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
    followers = dc.api.get_users_page_profile("followers")
    print(f"Followers: {', '.join([user['BLOG_NAME'] for user in followers])}")
    followers = [user["USER_ID"] for user in followers]

    following = dc.api.get_users_page_profile("following")
    following = [user["USER_ID"] for user in following]

    users_not_followed = [user_id for user_id in followers if user_id not in following]

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

    # Init Deezer session
    dc = DeezerClient(config_manager=cm)

    # Only hardlinks are supported by Jellyfin
    cm.set_value("downloads", "duplicates_link_type", "hardlink")

    # Check for new followers and follow back thread
    friend_requests_thread = threading.Thread(
        target=check_friend_request_thread, args=(dc,)
    )
    friend_requests_thread.start()

    # Check for download requests via notifications thread
    download_requests_thread = threading.Thread(
        target=check_download_requests_thread, args=(dc,)
    )
    download_requests_thread.start()


if __name__ == "__main__":
    main()
