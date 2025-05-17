import requests

url = "https://prod-api.lolz.live/oauth/token"
payload = {
    "grant_type": "password",
    "username": "your_username",
    "password": "your_password",
    "client_id": "your_client_id",
    "client_secret": "your_client_secret",
    "scope": "basic read post conversate"
}
headers = {"Content-Type": "application/json"}

response = requests.post(url, json=payload, headers=headers)
print(response.status_code)
print(response.json())