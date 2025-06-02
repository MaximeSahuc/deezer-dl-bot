import json
import requests

from deezer.deezer import (
    get_session,
    get_user_data,
    fetch_csrf_token_and_user_data,
    init_deezer_session
)


class DeezerClient():

    def __init__(self, arl_cookie):
        init_deezer_session(arl_cookie)
        fetch_csrf_token_and_user_data()
        self.session = get_session()
        self.user_data = get_user_data()
        

    def request_api(self, request_type, method, post_data=None):
        csrf_token = self.user_data["csrfToken"]

        match request_type:
            case "GET":
                print("GET api requests are not implemented yet")
                pass
            
            case "POST":
                url = f"https://www.deezer.com/ajax/gw-light.php?method={method}&input=3&api_version=1.0&api_token={csrf_token}"
                
                if post_data:
                    response = self.session.post(url, data=post_data)
                else:
                    response = self.session.post(url)

                if response.status_code != 200:
                    print(f"Error: received status {response.status_code} for {method} method")
                    
                    return None

                if response.json() and response.json()["error"]:
                    if len(response.json()["error"]):
                        if "NEED_USER_AUTH_REQUIRED" in response.json()['error']:
                            print("\nError: Invalid credentials. Please check your config file.")
                            exit(1)

                        print(f"Error: {response.json()['error']}")
                
                    return None
                
                return response.json()

            case _:
                print("Invalid request type")
                return None

    
    def get_user_notifications(self):
        json_response = self.request_api("POST", "deezer.userMenu")
        if not json_response: raise

        if json_response["results"] and json_response["results"]["NOTIFICATIONS"]:
            return json_response["results"]["NOTIFICATIONS"]["data"]
        else:
            print(f"Error: no notifications found")
            return


    def mark_notification_as_read(self, notification_id):
        self.request_api(
            "POST",
            "notification.markAsRead",
            post_data={
                "notif_ids": [
                    notification_id
                ]
            }
        )
    
    def get_users_page_profile(self, tab):
        payload = {
            "USER_ID": self.user_data["userId"],
            "tab": tab,
            "nb": 10000
        }

        json_response = self.request_api("POST", "deezer.pageProfile", post_data=json.dumps(payload))
        if not json_response: raise

        if json_response["results"]["TAB"][tab]:
            if len(json_response["results"]["TAB"][tab]["data"]) > 0:
                return json_response["results"]["TAB"][tab]["data"]
            else:
                return []
        else:
            print(f"Error: no {tab} found")
            return []


    def follow_user(self, user_id):
        payload = {
            "friend_id": user_id,
            "ctxt": {
                "id": user_id,
                "t": "profile_page"
                }
            }

        json_response = self.request_api("POST", "friend.follow", post_data=json.dumps(payload))
        if not json_response: raise

        if json_response["results"]:
            return json_response["results"]
        else:
            print(f"Error: cannot follow user {user_id} found")
            raise
