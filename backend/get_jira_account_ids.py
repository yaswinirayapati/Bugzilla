import os
import requests
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

JIRA_EMAIL = os.getenv("JIRA_EMAIL")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN")
JIRA_URL = os.getenv("JIRA_URL")

# List of developer emails to look up
DEVELOPER_EMAILS = [
    "yaswinirayapati@gmail.com",
    "harshithabade91@gmail.com",
    "lathach783@gmail.com",
    "2100030129cse@gmail.com",
    "veenagona123@gmail.com",
]

auth_str = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
b64_auth = base64.b64encode(auth_str.encode()).decode()
headers = {
    "Authorization": f"Basic {b64_auth}",
    "Accept": "application/json"
}

for email in DEVELOPER_EMAILS:
    url = f"{JIRA_URL}/rest/api/3/user/search?query={email}"
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        users = response.json()
        if users:
            user = users[0]
            print(f"Email: {email}")
            print(f"  accountId: {user['accountId']}")
            print(f"  displayName: {user.get('displayName', 'N/A')}")
            print()
        else:
            print(f"Email: {email} - No user found.")
    else:
        print(f"Failed to fetch user for {email}: {response.status_code} {response.text}")