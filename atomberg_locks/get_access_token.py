import os
import requests
import azure.functions as func
import json

def get_atomberg_connection():
    """Establishes a connection to ATOMBERG."""
    atomberg_key = os.getenv("ATOMBERG_KEY")
    atomberg_token = os.getenv("ATOMBERG_TOKEN")
    atomberg_url=f"{os.getenv("ATOMBERG_ENDPOINT")}/get_access_token"
    try:
        headers={
            "x-api-key":atomberg_key,
            "Authorization":"Bearer "+atomberg_token
        }
        response = requests.request("GET", atomberg_url, headers=headers)
        if response.status_code==200:
            access_token=json.loads(response.text)['message']['access_token']
            return access_token
    except Exception as e:
        return None

