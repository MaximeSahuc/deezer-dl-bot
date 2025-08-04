#!/usr/bin/env python3

import os
import threading

from deezer.client import DeezerClient
from jellyfinclient import JellyfinClient


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
        filter(lambda n: n["read"] == False, dc.api.get_user_notifications())  # noqa E712
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

        # Mark Deezer notification as Read
        dc.api.mark_notification_as_read([notif_id])

        # Download item
        download_result = dc.get_downloader().download_from_url(
            url=notif_shared_url,
            download_path=download_path,
            playlists_create_m3u=False,  # disable creation of M3U playlist files as we create dynamic playlists in Jellyfin
        )

        if "error" in download_result:
            print("Error:")
            print(download_result["error"]["message"])
            return

        print(f"[DOWNLOAD] {url_type} downloaded.\n".capitalize())

        try:
            jc = JellyfinClient(
                jellyfin_url=cm.get_value("jellyfin", "server_url"),
                jellyfin_api_key=cm.get_value("jellyfin", "api_key"),
            )
            # Scan Jellyfin library for new songs
            # jc.trigger_library_scan()
            # time.sleep(15)  # leave time for Jellyfin to scan the libraries

            # If a playlist was downloaded, create it in Jellyfin
            if download_result["result"]["download_type"] == "playlist":
                result = download_result["result"]["download_result"]
                playlist_name = result["download_name"]
                songs_paths = result["songs_absolute_paths"]
                jellyfin_username = sender_name

                # Create or get playlist
                print("Create or get playlist")
                playlist_id = jc.get_or_create_playlist(
                    playlist_name, jellyfin_username
                )

                if not playlist_id:
                    print("Failed to get or create playlist.")
                    return

                # Add cover to playlist
                print("Add cover to playlist")
                cover_path = result["cover_path"]
                print(cover_path)
                jc.update_playlist_image(
                    playlist_id=playlist_id,
                    image_path=cover_path,
                )

                # Get Jellyfin item IDs for songs
                song_item_ids_to_add = []
                print("\nResolving song paths to Jellyfin Item IDs:")
                for file_path in songs_paths:
                    item_id = jc.get_jellyfin_item_id_by_path(
                        file_path, jellyfin_username
                    )
                    if item_id:
                        song_item_ids_to_add.append(item_id)
                    else:
                        print(
                            f"Warning: Could not find Jellyfin item for path: {file_path}. Skipping."
                        )

                # Add songs to the playlist
                if song_item_ids_to_add:
                    jc.add_songs_to_playlist(
                        playlist_id, song_item_ids_to_add, jellyfin_username
                    )
                else:
                    print("No valid Jellyfin songs found to add to the playlist.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")


def check_download_requests_thread(dc):
    """
    Check for new download request every minute
    """
    import time

    while True:
        print("[DOWNLOAD] Checking for new download requests")
        new_download_thread = threading.Thread(
            target=check_for_new_download_requests, args=(dc,)
        )
        new_download_thread.start()
        print(
            "[DOWNLOAD] Checked for new download requests. Checking back in a minute."
        )
        time.sleep(60)


def check_for_new_friend_requests(dc):
    followers = dc.api.get_users_page_profile("followers")
    print(f"Followers: {', '.join([user['BLOG_NAME'] for user in followers])}")
    followers = [user["USER_ID"] for user in followers]

    following = dc.api.get_users_page_profile("following")
    following = [user["USER_ID"] for user in following]

    users_not_followed = [user_id for user_id in followers if user_id not in following]

    for user in users_not_followed:
        print(f"[FRIENDS] User {user} not followed, following user...")
        dc.api.follow_user(user)


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
    from config import ConfigManager

    print("Deezer-DL: v0.1.5")

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
