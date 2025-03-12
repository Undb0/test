import os
import requests
import json
import time
import random
from base64 import b64decode, b64encode
from nacl import encoding, public
import json

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
GITHUB_PAT = os.getenv("GH_PAT")
repo_name = os.getenv("REPO")


if not refresh_token or not client_id or not client_secret:
    print("❌ ERROR: Faltan variables de entorno. Verifica los secrets en GitHub.")
    exit(1)

def encrypt_secret(public_key: str, secret_value: str) -> str:
    public_key = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(public_key)
    encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
    return b64encode(encrypted).decode("utf-8")

def update_github_secret(repo, secret_name, secret_value):
    headers = {'Authorization': f'token {GITHUB_PAT}', 'Accept': 'application/vnd.github.v3+json'}
    repo_name = repo.replace('https://github.com/', '')

    # Obtener la clave pública del repositorio
    pubkey_url = f'https://api.github.com/repos/{repo_name}/actions/secrets/public-key'
    response = requests.get(pubkey_url, headers=headers)

    if response.status_code != 200:
        print(f"Error obteniendo la clave pública para {repo}: {response.text}")
        return

    public_key_info = response.json()
    encrypted_value = encrypt_secret(public_key_info['key'], secret_value)

    # Actualizar el secreto
    secret_url = f'https://api.github.com/repos/{repo_name}/actions/secrets/{secret_name}'
    data = {'encrypted_value': encrypted_value, 'key_id': public_key_info['key_id']}

    put_response = requests.put(secret_url, headers=headers, json=data)
    if put_response.status_code in [201, 204]:
        print(f"Secreto actualizado correctamente en {repo}")
    else:
        print(f"Error actualizando secreto en {repo}: {put_response.text}")

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
    update_github_secret(repo, 'REFRESH_TOKEN', new_refresh_token)

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
