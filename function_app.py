import logging
import azure.functions as func
from crud_operations.hotel_guest_otp import handle_hotel_guest_otp_crud
from atomberg_locks.lock_functions import generate_otp_lock
from otp_notifications.sendnotifications import send_whatsapp_notification,send_sms_notification

# Initialize the FunctionApp
app = func.FunctionApp()

@app.route(route="hotel_guest_otp")  # Defining route
def hotel_guest_otp(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('Python HTTP trigger function processed a request.')
        
        # Get method and parameters
        method = req.method
        params = req.params
        body = req.get_json() if method in ["POST", "PUT"] else None
        
        # Call the function that handles the logic for hotel_guest_otp
        return handle_hotel_guest_otp_crud(method, params, body)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)

@app.route(route="atomberg_generate_otp")  # Defining route
def atomberg_generate_otp(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('Python HTTP trigger function processed a request.')
        
        # Get method and parameters
        method = req.method
        params = req.params
        body = req.get_json() if method in ["POST", "PUT"] else None
        
        # Call the function that handles the logic for hotel_guest_otp
        return generate_otp_lock("AV 303",1731754003,1731757603)
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)
    
@app.route(route="send_otp_notifications")  # Defining route
def send_otp_notifications(req: func.HttpRequest) -> func.HttpResponse:
     try:
        logging.info('Python HTTP trigger function processed a request.')
        
        # Get method and parameters
        method = req.method
        params = req.params
        body = req.get_json() if method in ["POST"] else None
        
        # Call the function that handles the logic for hotel_guest_otp
        return send_sms_notification(body)
     except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)
