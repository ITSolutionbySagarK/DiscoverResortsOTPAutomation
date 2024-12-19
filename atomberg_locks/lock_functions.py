import os
import requests
import json
import azure.functions as func
global atombergaccess_token
global lock_lists
atombergaccess_token=None
lock_lists=None
def get_atomberg_connection():
    print("Called Connection")
    """Establishes a connection to ATOMBERG."""
    atomberg_key = os.getenv("ATOMBERG_KEY")
    atomberg_token = os.getenv("ATOMBERG_TOKEN")
    atomberg_url_base=os.getenv("ATOMBERG_ENDPOINT")
    atomberg_url=f"{atomberg_url_base}/get_access_token"
    try:
        headers={
            "x-api-key":atomberg_key,
            "Authorization":"Bearer "+atomberg_token
        }
        response = requests.request("GET", atomberg_url, headers=headers)
        if response.status_code==200:
            access_token=json.loads(response.text)['message']['access_token']
            atombergaccess_token=access_token
            return access_token
    except Exception as e:
        return None

def get_device_id(room_no,access_token):
    try:
        print("Called Device")
        atomberg_key = os.getenv("ATOMBERG_KEY")
        atomberg_url_base=os.getenv("ATOMBERG_ENDPOINT")
        atomberg_url=f"{atomberg_url_base}/get_list_of_locks"
        if access_token!=None:
            headers={
            "x-api-key":atomberg_key,
            "Authorization":"Bearer "+access_token
            }
            response = requests.request("GET", atomberg_url, headers=headers)
            if response.status_code==200:
                lock_list=json.loads(response.text)['message']['locks_list']
                name_to_device = {item["name"]: item["device_id"] for item in lock_list}
                lock_lists=name_to_device
                return name_to_device.get(room_no,"")
        else:
            return None
    except Exception as e:
        return func.HttpResponse(f"Some Error Occured.{e}", status_code=405)
    
    
def generate_otp_lock(room_no,checkintime,checkouttime):
    try:
        if atombergaccess_token==None:
            access_token=get_atomberg_connection()
        else:
            access_token=atombergaccess_token
        if access_token!=None:
            if lock_lists==None:
                device_id=get_device_id(room_no,access_token)
            else:
                device_id=lock_lists.get(room_no,"")
            if device_id!=None:  
                atomberg_key = os.getenv("ATOMBERG_KEY")
                atomberg_url_base=os.getenv("ATOMBERG_ENDPOINT")
                atomberg_url=f"{atomberg_url_base}/get_lock_dynamic_pin"
                headers={
                "x-api-key":atomberg_key,
                "Authorization":"Bearer "+access_token
                 }
                payload={
                    "device_id":device_id,
                    "start_time":checkintime,
                    "end_time":checkouttime
                }
                response = requests.request("POST", atomberg_url, headers=headers,data=payload)
                if response.status_code==200:
                    otp=json.loads(response.text)['message']['data']
                    return otp
                else:
                    return None
            else:
                return None
    except Exception as e:
        return func.HttpResponse(f"Some Error Occured.{e}", status_code=405)
    
            
        
        
