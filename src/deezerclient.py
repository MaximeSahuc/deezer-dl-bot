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
                    response = self.session.post(url, json=post_data)
                else:
                    response = self.session.post(url)

                if response.status_code != 200:
                    print(f"Error: received status {response.status_code} for {method} method")
                    
                    return None

                if response.json() and response.json()["error"]:
                    if len(response.json()["error"]):
                        print(f"Error: {response.json()['error']}")
                
                    return None
                
                return response.json()

            case _:
                print("Invalid request type")
                return None

    
    def get_user_notifications(self):
        json_response = self.request_api("POST", "deezer.userMenu")

        if len(json_response["error"]) > 0:
            print(f"Error: {json_response['error']}")
            return

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