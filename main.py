import os
import requests
import json
import time
import random

# Register the azure app first and make sure the app has the following permissions:
# files: Files.Read.All、Files.ReadWrite.All、Sites.Read.All、Sites.ReadWrite.All
# user: User.Read.All、User.ReadWrite.All、Directory.Read.All、Directory.ReadWrite.All
# mail: Mail.Read、Mail.ReadWrite、MailboxSettings.Read、MailboxSettings.ReadWrite
# After registration, you must click on behalf of xxx to grant administrator consent, otherwise outlook api cannot be called






calls = [
    'https://graph.microsoft.com/v1.0/me/drive/root',
    'https://graph.microsoft.com/v1.0/me/drive',
    'https://graph.microsoft.com/v1.0/drive/root',
    'https://graph.microsoft.com/v1.0/users',
    'https://graph.microsoft.com/v1.0/me/messages',
    'https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messageRules',
    'https://graph.microsoft.com/v1.0/me/drive/root/children',
    'https://api.powerbi.com/v1.0/myorg/apps',
    'https://graph.microsoft.com/v1.0/me/mailFolders',
    'https://graph.microsoft.com/v1.0/me/outlook/masterCategories',
    'https://graph.microsoft.com/v1.0/applications?$count=true',
    'https://graph.microsoft.com/v1.0/me/?$select=displayName,skills',
    'https://graph.microsoft.com/v1.0/me/mailFolders/Inbox/messages/delta',
    'https://graph.microsoft.com/beta/me/outlook/masterCategories',
    'https://graph.microsoft.com/beta/me/messages?$select=internetMessageHeaders&$top=1',
    'https://graph.microsoft.com/v1.0/sites/root/lists',
    'https://graph.microsoft.com/v1.0/sites/root',
    'https://graph.microsoft.com/v1.0/sites/root/drives'
]

# Obtener valores de los secrets de GitHub (variables de entorno)
refresh_token = os.getenv("REFRESH_TOKEN")
client_id = os.getenv("CONFIG_ID")
client_secret = os.getenv("CONFIG_KEY")

if not refresh_token or not client_id or not client_secret:
    print("❌ ERROR: Faltan variables de entorno. Verifica los secrets en GitHub.")
    exit(1)

def get_access_token(refresh_token, client_id, client_secret):
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': client_id,
        'client_secret': client_secret,
        'redirect_uri': 'http://localhost:53682/'
    }
    response = requests.post('https://login.microsoftonline.com/common/oauth2/v2.0/token', data=data, headers=headers)
    jsontxt = response.json()

    if 'error' in jsontxt:
        print("❌ ERROR obteniendo token:", jsontxt)
        return None, None

    new_refresh_token = jsontxt['refresh_token']
    access_token = jsontxt['access_token']

    # Guardar el nuevo refresh token en un archivo
    with open("new_token.txt", "w") as f:
        f.write(new_refresh_token)

    return access_token

def main():
    random.shuffle(calls)
    access_token = get_access_token(refresh_token, client_id, client_secret)
    if not access_token:
        return

    session = requests.Session()
    session.headers.update({'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'})

    for num, endpoint in enumerate(calls[:5], start=1):
        try:
            response = session.get(endpoint)
            if response.status_code == 200:
                print(f'{num} - ✅ Call successful: {endpoint}')
        except requests.exceptions.RequestException as e:
            print("❌ Request failed:", e)

if __name__ == "__main__":
    main()
