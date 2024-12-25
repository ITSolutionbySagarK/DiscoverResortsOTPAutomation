import json
import os
import requests
import logging
from urllib.parse import quote_plus


def send_whatsapp_notification(body):
    try:
        # Parse the input JSON body
        data = json.loads(body)
        # Ensure required fields are present in the input
        required_fields = ["phoneNumber", "bodyValues"]
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Get environment variables
        api_key = os.getenv("WHATSAPP_API_KEY")
        endpoint = os.getenv("WHATSAPP_ENDPOINT")
        
        if not api_key or not endpoint:
            raise EnvironmentError("Missing required environment variables: WHATSAPP_API_KEY or WHATSAPP_ENDPOINT")
        
        # Construct the payload
        payload = json.dumps({
            "countryCode": "+91",
            "phoneNumber": data["phoneNumber"],  # Extract phone number from the body
            "type": "Template",
            "template": {
                "name": "ezee_reservation_room_details",  # Constant
                "languageCode": "en",  # Constant
                "bodyValues": data["bodyValues"]  # Extract body values dynamically
            }
        })

        # Headers for the API request
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json'
        }

        # Send the request
        response = requests.post(endpoint, headers=headers, data=payload)

        # Log and handle the response
        if response.status_code == 201:
            logging.info("WhatsApp message sent successfully.")
            return {"status": "success", "message": "WhatsApp message sent successfully."}
        else:
            logging.error(
                f"Failed to send WhatsApp message. Status Code: {response.status_code}, Response: {response.text}"
            )
            return {
                "status": "error",
                "status_code": response.status_code,
                "response": response.text
            }
    
    except json.JSONDecodeError:
        logging.error("Invalid JSON input")
        return {"status": "error", "message": "Invalid JSON input"}
    except EnvironmentError as env_err:
        logging.error(f"Environment configuration error: {str(env_err)}")
        return {"status": "error", "message": str(env_err)}
    except ValueError as val_err:
        logging.error(f"Validation error: {str(val_err)}")
        return {"status": "error", "message": str(val_err)}
    except Exception as e:
        logging.error(f"An unexpected error occurred: {str(e)}")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
def send_sms_notification(body):
    data = json.loads(body)
    url = "https://www.fast2sms.com/dev/bulkV2"

    # Extract the phone number and body values from the supplied data
    phone_number = data.get('phoneNumber', '9768927169')  # Default phone number if not provided
    body_values = data.get('bodyValues', [])

    # Ensure that the body values contain the required data
    if len(body_values) < 6:
        print("Error: Missing body values")
        return

    # Extract dynamic values from the bodyValues array
    guest_name, reservation_number, room_number, otp, otp_start_date_time, otp_end_date_time = body_values

    # Construct the message content with dynamic values
    message = f"""
Room Lock Details
Hello {guest_name},

We are excited to welcome you!
Here are the details for your stay:

- Reservation Number: {reservation_number}
- Room Number: {room_number}
- OTP to Unlock: {otp}
- OTP Validity: From {otp_start_date_time} to {otp_end_date_time}

Feel free to reach out if you need any assistance. Have a pleasant stay.

*Best regards,
Discover Resorts*
"""

    # URL encode the message content to ensure proper formatting in the URL
    encoded_message = quote_plus(message)

    # Prepare the payload with dynamic values
    payload = f"message={encoded_message}&language=english&route=q&numbers={phone_number}"

    headers = {
        'authorization': os.getenv("SMS_API_KEY"),
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache",
    }

    # Send the POST request
    response = requests.post(url, data=payload, headers=headers)

    # Print response text for debugging
    print(response.text)
    url = "https://www.fast2sms.com/dev/bulkV2"

    # Extract dynamic values from the data dictionary
    guest_name = data.get('guest_name', 'guest_name')
    reservation_number = data.get('reservation_number', 'N/A')
    room_number = data.get('room_number', 'N/A')
    otp = data.get('otp', '000000')
    otp_validity_start = data.get('otp_validity_start', 'N/A')
    otp_validity_end = data.get('otp_validity_end', 'N/A')
    contact_number = data.get('contact_number', '9768927169')

    # Construct the message content with dynamic values
    message = f"""
Room Lock Details
Hello {guest_name},

We are excited to welcome you!
Here are the details for your stay:

- Reservation Number: {reservation_number}
- Room Number: {room_number}
- OTP to Unlock: {otp}
- OTP Validity: From {otp_validity_start} to {otp_validity_end}

Feel free to reach out if you need any assistance. Have a pleasant stay.

*Best regards,
Discover Resorts*
"""

    # URL encode the message content to ensure proper formatting in the URL
    encoded_message = quote_plus(message)

    # Prepare the payload with dynamic values
    payload = f"message={encoded_message}&language=english&route=q&numbers={contact_number}"

    headers = {
        'authorization': os.getenv("SMS_API_KEY"),
        'Content-Type': "application/x-www-form-urlencoded",
        'Cache-Control': "no-cache",
    }

    # Send the POST request
    response = requests.post(url, data=payload, headers=headers)

    # Print response text for debugging
    print(response.text)