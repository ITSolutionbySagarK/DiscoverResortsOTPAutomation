import json
import os
import requests
import logging
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(level=logging.INFO)

def send_whatsapp_notification(body):
    """Sends a WhatsApp notification using a predefined template."""
    try:
        logging.info("Starting WhatsApp notification process.")
        # Parse the input JSON body
        data = json.loads(body)
        logging.debug(f"Parsed input body: {data}")

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
            "phoneNumber": data["phoneNumber"],
            "type": "Template",
            "template": {
                "name": "ezee_reservation_room_details",
                "languageCode": "en",
                "bodyValues": data["bodyValues"]
            }
        })
        logging.debug(f"Constructed payload: {payload}")

        # Headers for the API request
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json'
        }

        # Send the request
        response = requests.post(endpoint, headers=headers, data=payload)
        logging.info(f"WhatsApp API response: {response.status_code}, {response.text}")

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
        logging.error("Invalid JSON input.")
        return {"status": "error", "message": "Invalid JSON input"}
    except EnvironmentError as env_err:
        logging.error(f"Environment configuration error: {str(env_err)}")
        return {"status": "error", "message": str(env_err)}
    except ValueError as val_err:
        logging.error(f"Validation error: {str(val_err)}")
        return {"status": "error", "message": str(val_err)}
    except Exception as e:
        logging.exception("An unexpected error occurred.")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

def send_sms_notification(body):
    """Sends an SMS notification with dynamic content."""
    try:
        logging.info("Starting SMS notification process.")
        # Parse the input JSON body
        data = json.loads(body)
        logging.debug(f"Parsed input body: {data}")

        # Extract dynamic values from the body
        phone_number = data.get('phoneNumber', '9768927169')
        body_values = data.get('bodyValues', [])
        if len(body_values) < 6:
            raise ValueError("Insufficient body values provided for SMS content.")

        # Extract values for message construction
        guest_name, reservation_number, room_number, otp, otp_start_date_time, otp_end_date_time = body_values

        # Construct the message content
        message = f"""
Room Lock Details
Hello {guest_name},

We are excited to welcome you!
Here are the details for your stay:

- Reservation Number - {reservation_number}
- Room Number - {room_number}
- OTP to Unlock - {otp}
- OTP Validity - From {otp_start_date_time} to {otp_end_date_time}

Feel free to reach out if you need any assistance. Have a pleasant stay.

*Best regards,
Discover Resorts*
"""
        logging.debug(f"Constructed SMS message: {message}")

        # URL encode the message
        encoded_message = quote_plus(message)
        payload = f"message={encoded_message}&language=english&route=q&numbers={phone_number}"

        headers = {
            'authorization': os.getenv("SMS_API_KEY"),
            'Content-Type': "application/x-www-form-urlencoded",
            'Cache-Control': "no-cache",
        }

        # Send the POST request
        url = "https://www.fast2sms.com/dev/bulkV2"
        response = requests.post(url, data=payload, headers=headers)
        logging.info(f"SMS API response: {response.status_code}, {response.text}")

        if response.status_code == 200:
            logging.info("SMS sent successfully.")
            return {"status": "success", "message": "SMS sent successfully."}
        else:
            logging.error(
                f"Failed to send SMS. Status Code: {response.status_code}, Response: {response.text}"
            )
            return {
                "status": "error",
                "status_code": response.status_code,
                "response": response.text
            }

    except json.JSONDecodeError:
        logging.error("Invalid JSON input.")
        return {"status": "error", "message": "Invalid JSON input"}
    except ValueError as val_err:
        logging.error(f"Validation error: {str(val_err)}")
        return {"status": "error", "message": str(val_err)}
    except Exception as e:
        logging.exception("An unexpected error occurred.")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}
