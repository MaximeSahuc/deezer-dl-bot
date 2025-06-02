import requests


def scan_jellyfin_library(server_url: str, api_key: str) -> dict:
    # Ensure the server URL does not end with a slash to avoid double slashes
    server_url = server_url.rstrip("/")

    headers = {
        "X-MediaBrowser-Token": api_key,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    scan_url = f"{server_url}/Library/Refresh"
    try:
        response = requests.post(scan_url, headers=headers, timeout=30)
        response.raise_for_status()

        if response.status_code in [200, 204]:
            return {
                "success": True,
                "message": "Jellyfin: Successfully initiated scan for library.",
            }
        else:
            return {
                "success": False,
                "message": f"Jellyfin: Failed to initiate scan. Server responded with status code {response.status_code} and message: {response.text}",
            }

    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "message": f"Jellyfin: Error initiating library scan: {e}",
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Jellyfin: An unexpected error occurred: {e}",
        }
