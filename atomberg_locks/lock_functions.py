import os
import requests
import json
import azure.functions as func
import logging
# Global variables for caching access token and lock list
global atombergaccess_token
global lock_lists
atombergaccess_token = None
lock_lists = None

def get_atomberg_connection():
    """Establishes a connection to ATOMBERG and retrieves the access token."""
    logging.info("Attempting to establish ATOMBERG connection.")
    atomberg_key = os.getenv("ATOMBERG_KEY")
    atomberg_token = os.getenv("ATOMBERG_TOKEN")
    atomberg_url_base = os.getenv("ATOMBERG_ENDPOINT")
    atomberg_url = f"{atomberg_url_base}/get_access_token"

    try:
        headers = {
            "x-api-key": atomberg_key,
            "Authorization": "Bearer " + atomberg_token
        }
        logging.debug(f"Sending GET request to {atomberg_url} with headers: {headers}")
        response = requests.request("GET", atomberg_url, headers=headers)

        if response.status_code == 200:
            access_token = json.loads(response.text)['message']['access_token']
            global atombergaccess_token
            atombergaccess_token = access_token
            logging.info("Access token successfully retrieved.")
            return access_token
        else:
            logging.error(f"Failed to retrieve access token. Status code: {response.status_code}, Response: {response.text}")
            return None
    except Exception as e:
        logging.exception("An error occurred while retrieving the access token.")
        return None

def get_device_id(room_no, access_token):
    """Retrieves the device ID for a given room number."""
    logging.info(f"Attempting to retrieve device ID for room number: {room_no}")
    try:
        atomberg_key = os.getenv("ATOMBERG_KEY")
        atomberg_url_base = os.getenv("ATOMBERG_ENDPOINT")
        atomberg_url = f"{atomberg_url_base}/get_list_of_locks"

        if access_token:
            headers = {
                "x-api-key": atomberg_key,
                "Authorization": "Bearer " + access_token
            }
            logging.debug(f"Sending GET request to {atomberg_url} with headers: {headers}")
            response = requests.request("GET", atomberg_url, headers=headers)

            if response.status_code == 200:
                lock_list = json.loads(response.text)['message']['locks_list']
                global lock_lists
                lock_lists = {item["name"]: item["device_id"] for item in lock_list}
                logging.info(f"Device list retrieved successfully. Locks: {lock_lists}")
                return lock_lists.get(room_no, "")
            else:
                logging.error(f"Failed to retrieve lock list. Status code: {response.status_code}, Response: {response.text}")
                return None
        else:
            logging.warning("Access token is None. Cannot fetch device ID.")
            return None
    except Exception as e:
        logging.exception(f"An error occurred while retrieving device ID for room number: {room_no}")
        return func.HttpResponse(f"Some Error Occurred: {e}", status_code=500)

def generate_otp_lock(room_no, checkintime, checkouttime):
    """Generates a dynamic OTP for the lock."""
    logging.info(f"Generating OTP for room number: {room_no}")
    try:
        # Retrieve or use cached access token
        global atombergaccess_token
        if not atombergaccess_token:
            logging.info("Access token not cached. Fetching new token.")
            atombergaccess_token = get_atomberg_connection()

        if atombergaccess_token:
            # Retrieve or use cached lock list
            global lock_lists
            if not lock_lists:
                logging.info("Lock list not cached. Fetching new list.")
                device_id = get_device_id(room_no, atombergaccess_token)
            else:
                device_id = lock_lists.get(room_no, "")

            if device_id:
                atomberg_key = os.getenv("ATOMBERG_KEY")
                atomberg_url_base = os.getenv("ATOMBERG_ENDPOINT")
                atomberg_url = f"{atomberg_url_base}/get_lock_dynamic_pin"
                headers = {
                    "x-api-key": atomberg_key,
                    "Authorization": "Bearer " + atombergaccess_token
                }
                payload = {
                    "device_id": device_id,
                    "start_time": checkintime,
                    "end_time": checkouttime
                }
                logging.debug(f"Sending POST request to {atomberg_url} with headers: {headers} and payload: {payload}")
                response = requests.request("POST", atomberg_url, headers=headers, data=json.dumps(payload))

                if response.status_code == 200:
                    otp = json.loads(response.text)['message']['data']
                    logging.info(f"OTP successfully generated for room number: {room_no}. OTP: {otp}")
                    return otp
                else:
                    logging.error(f"Failed to generate OTP. Status code: {response.status_code}, Response: {response.text}")
                    return None
            else:
                logging.warning(f"Device ID not found for room number: {room_no}")
                return None
        else:
            logging.error("Access token retrieval failed. Cannot generate OTP.")
            return None
    except Exception as e:
        logging.exception(f"An error occurred while generating OTP for room number: {room_no}")
        return func.HttpResponse(f"Some Error Occurred: {e}", status_code=500)
