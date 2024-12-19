import azure.functions as func
import json
import os
import requests

def send_whatsapp_notification(body):
    try:
        # Parse the input JSON body
        data = json.loads(body)

        # Ensure required fields are present in the input
        required_fields = ["phoneNumber", "bodyValues"]
        for field in required_fields:
            if field not in data:
                return func.HttpResponse(
                    f"Missing required field: {field}",
                    status_code=400
                )
        
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
            'Authorization': f'Basic {os.getenv("WHATSAPP_API_KEY")}',
            'Content-Type': 'application/json'
        }

        # Send the request
        response = requests.post(os.getenv("WHATSAPP_ENDPOINT"), headers=headers, data=payload)

        # Return response or status
        if response.status_code == 200:
            return func.HttpResponse("WhatsApp OTP Triggered", status_code=200)
        else:
            return func.HttpResponse(
                f"Failed to send WhatsApp message. Status Code: {response.status_code}, Response: {response.text}",
                status_code=500
            )

    except Exception as e:
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)
