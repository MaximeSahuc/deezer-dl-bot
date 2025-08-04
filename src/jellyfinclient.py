from urllib.parse import urljoin
import requests
import base64
import uuid
import os


class JellyfinClient:
    def __init__(
        self,
        jellyfin_url,
        jellyfin_api_key,
        client_name="Deezer-DL",
        device_name="Deezer-DL",
        device_id=None,
        client_version="1.0.0",
    ):
        self.jellyfin_url = jellyfin_url
        self.api_key = jellyfin_api_key
        self.user_id = None

        self.music_items = None

        if device_id is None:
            self.device_id = str(uuid.uuid4())
        else:
            self.device_id = device_id

        self.client_name = client_name
        self.device_name = device_name
        self.client_version = client_version

        self.headers = {
            "X-MediaBrowser-Token": self.api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-MediaBrowser-Client": self.client_name,
            "X-MediaBrowser-Device-Name": self.device_name,
            "X-MediaBrowser-Device-Id": self.device_id,
            "X-MediaBrowser-Version": self.client_version,
        }

    def _jellyfin_api_get(self, endpoint, params=None):
        """Internal helper for GET requests."""
        url = urljoin(self.jellyfin_url, endpoint)
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

    def _jellyfin_api_post(self, endpoint, json_data=None, params=None):
        """Internal helper for POST requests."""

        url = urljoin(self.jellyfin_url, endpoint)
        response = requests.post(
            url, headers=self.headers, json=json_data, params=params
        )

        response.raise_for_status()
        if (
            response.content != b""
        ):  # Handle cases where response body might be empty (e.g., 204 No Content)
            return response.json()

        return None

    def get_user_id(self, username):
        """
        Retrieves the User ID for a given username.
        Caches the user_id for subsequent calls within the instance.
        """

        if self.user_id:  # If already retrieved, return cached ID
            return self.user_id

        print(f"Attempting to find User ID for: {username}")
        users = self._jellyfin_api_get("Users")

        for user in users:
            if user["Name"].lower() == username.lower():
                self.user_id = user["Id"]
                print(f"Found User ID for '{username}': {self.user_id}")
                return self.user_id

        print(f"Error: User '{username}' not found on Jellyfin server.")
        return None

    def get_or_create_playlist(self, playlist_name, username):
        """
        Gets the ID of an existing playlist or creates a new one.
        """
        user_id = self.get_user_id(username)
        if not user_id:
            return None

        print(f"Checking for playlist '{playlist_name}' for user '{username}'...")
        params = {
            "Recursive": "true",
            "IncludeItemTypes": "Playlist",
            "UserId": user_id,
        }
        items = self._jellyfin_api_get(f"Users/{user_id}/Items", params=params)

        for item in items.get("Items", []):
            if item.get("Type") == "Playlist" and item.get("Name") == playlist_name:
                print(f"Found existing playlist: {playlist_name} ({item['Id']})")
                return item["Id"]

        # If not found, create it
        print(f"Playlist '{playlist_name}' not found. Creating...")
        create_playlist_payload = {
            "Name": playlist_name,
            "UserId": user_id,
            "MediaType": "Audio",  # Assuming audio playlists
        }

        try:
            created_playlist = self._jellyfin_api_post(
                "Playlists", json_data=create_playlist_payload
            )

            if created_playlist:
                print(
                    f"Created new playlist: {playlist_name} ({created_playlist['Id']})"
                )
                return created_playlist["Id"]
            else:
                print(
                    f"Failed to create playlist '{playlist_name}'. API returned no content."
                )

                return None
        except requests.exceptions.HTTPError as e:
            print(f"Error creating playlist '{playlist_name}': {e}")
            return None

    def _fetch_music_library_items(self):
        print(
            "Fetching Jellyfin music library items..."
        )

        # First, get music library IDs
        media_folders = self._jellyfin_api_get("Library/MediaFolders").get("Items", [])
        music_library_ids = [
            folder["Id"]
            for folder in media_folders
            if folder.get("CollectionType") == "music"
        ]

        if not music_library_ids:
            print("No music libraries found in Jellyfin.")
            return []

        all_music_items = None
        for lib_id in music_library_ids:
            # Fetch items with 'Path' field included. Use pagination for very large libraries.
            limit = 50000
            params = {
                "Recursive": "true",
                "ParentId": lib_id,
                "IncludeItemTypes": "Audio",
                "Fields": "Path",
                "UserId": self.user_id,
                "Limit": limit,
            }
            response_data = self._jellyfin_api_get("Items", params=params)
            items_page = response_data.get("Items", [])
            all_music_items = items_page

        print(f"Finished fetching {len(all_music_items)} music items from library.")

        return all_music_items

    def get_jellyfin_item_id_by_path(self, file_path, username):
        """
        Attempts to find a Jellyfin item ID given its absolute file path.
        """
        user_id = self.get_user_id(username)
        if not user_id:
            return None

        if self.user_id is None:
            self.user_id = user_id  # Store it for consistency

        if not self.music_items:
            self.music_items = self._fetch_music_library_items()

        for item in self.music_items:
            jellyfin_path = item.get("Path")
            if jellyfin_path and jellyfin_path.lower() == file_path.lower():
                return item["Id"]

        return None

    def add_songs_to_playlist(self, playlist_id, song_ids, username):
        """
        Adds a list of song Item IDs to a specified playlist.
        """

        user_id = self.get_user_id(username)
        if not user_id:
            print("Error: User ID not found, cannot add songs to playlist.")
            return

        if not song_ids:
            print("No songs to add to playlist.")
            return

        json_payload = {
            "Ids": song_ids
        }

        try:
            self._jellyfin_api_post(
                f"Playlists/{playlist_id}", json_data=json_payload
            )
            print(
                f"Successfully added {len(song_ids)} songs to playlist {playlist_id}."
            )
        except requests.exceptions.HTTPError as e:
            print(f"Error adding songs to playlist {playlist_id}: {e}")
            print(f"Response content: {e.response.text if e.response else 'N/A'}")

    def trigger_library_scan(self):
        """Triggers a full library scan on Jellyfin."""

        print("Triggering Jellyfin library scan...")
        try:
            self._jellyfin_api_post("Library/Refresh")
            print("Library scan initiated.")
        except requests.exceptions.HTTPError as e:
            print(f"Error triggering library scan: {e}")
            print(f"Response content: {e.response.text if e.response else 'N/A'}")

    def update_playlist_image(self, playlist_id, image_path):
        """
        Updates the primary image for a given playlist.
        """
        if not os.path.exists(image_path):
            print(f"Error: Image file not found at path: {image_path}")
            return False

        try:
            image_index = 0
            url = urljoin(
                self.jellyfin_url, f"Items/{playlist_id}/Images/Primary/{image_index}"
            )

            with open(image_path, "rb") as f:
                raw_image_data = f.read()

            image_data_b64 = base64.b64encode(raw_image_data).decode("utf-8")

            authorization_header_value = (
                f'MediaBrowser Client="{self.client_name}", '
                f'Device="{self.device_name}", '
                f'DeviceId="{self.device_id}", '
                f'Version="{self.client_version}", '
                f'Token="{self.api_key}"'
            )

            # Determine content type based on file extension
            extension = os.path.splitext(image_path)[1].lower()
            if extension == ".jpg" or extension == ".jpeg":
                content_type = "image/jpeg"
            elif extension == ".png":
                content_type = "image/png"
            else:
                print(
                    f"Error: Unsupported image format '{extension}'. Only JPG/PNG are supported for direct upload."
                )
                return False

            image_upload_headers = {
                "Authorization": authorization_header_value,
                "Content-Type": content_type,
                "Accept": "*/*",
                "X-MediaBrowser-Client": self.client_name,
                "X-MediaBrowser-Device-Name": self.device_name,
                "X-MediaBrowser-Device-Id": self.device_id,
                "X-MediaBrowser-Version": self.client_version,
                "User-Agent": self.headers.get("User-Agent", "Python requests"),
                "Origin": self.jellyfin_url,
            }

            response = requests.post(
                url,
                headers=image_upload_headers,
                data=image_data_b64,  # Send the Base64 encoded string as data
            )
            response.raise_for_status()

            print(
                f"Successfully updated image for playlist {playlist_id} from {image_path}"
            )
            return True

        except requests.exceptions.HTTPError as e:
            print(f"Error updating playlist image (HTTP {e.response.status_code}): {e}")
            print(f"Response content: {e.response.text if e.response else 'N/A'}")
            if e.response and e.response.text:
                print(f"Server response for error: {e.response.text}")
            return False
        except requests.exceptions.ConnectionError as e:
            print(f"Connection error while updating playlist image: {e}")
            return False
        except Exception as e:
            print(f"An unexpected error occurred while updating playlist image: {e}")
            return False
