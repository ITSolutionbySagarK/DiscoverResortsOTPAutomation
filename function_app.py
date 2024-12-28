import logging
import azure.functions as func
from crud_operations.hotel_guest_otp import handle_hotel_guest_otp_crud
from atomberg_locks.lock_functions import generate_otp_lock
from otp_notifications.sendnotifications import send_whatsapp_notification, send_sms_notification

# Initialize the FunctionApp
app = func.FunctionApp()

@app.route(route="hotel_guest_otp")  # Defining route
def hotel_guest_otp(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('hotel_guest_otp: Received request.')
        method = req.method
        params = req.params
        logging.info(f'hotel_guest_otp: Method - {method}, Params - {params}')
        
        body = req.get_json() if method in ["POST", "PUT"] else None
        if body:
            logging.info(f'hotel_guest_otp: Request body - {body}')
        
        logging.info('hotel_guest_otp: Calling handle_hotel_guest_otp_crud.')
        response = handle_hotel_guest_otp_crud(method, params, body)
        logging.info('hotel_guest_otp: Response generated successfully.')
        return response
        
    except Exception as e:
        logging.error(f'hotel_guest_otp: Error occurred - {str(e)}', exc_info=True)
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)

@app.route(route="atomberg_generate_otp")  # Defining route
def atomberg_generate_otp(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('atomberg_generate_otp: Received request.')
        method = req.method
        params = req.params
        logging.info(f'atomberg_generate_otp: Method - {method}, Params - {params}')
        
        body = req.get_json() if method in ["POST", "PUT"] else None
        if body:
            logging.info(f'atomberg_generate_otp: Request body - {body}')
        
        logging.info('atomberg_generate_otp: Generating OTP for lock.')
        response = generate_otp_lock("AV 303", 1731754003, 1731757603)
        logging.info('atomberg_generate_otp: OTP generated successfully.')
        return response
        
    except Exception as e:
        logging.error(f'atomberg_generate_otp: Error occurred - {str(e)}', exc_info=True)
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)

@app.route(route="send_otp_notifications")  # Defining route
def send_otp_notifications(req: func.HttpRequest) -> func.HttpResponse:
    try:
        logging.info('send_otp_notifications: Received request.')
        method = req.method
        params = req.params
        logging.info(f'send_otp_notifications: Method - {method}, Params - {params}')
        
        body = req.get_json() if method == "POST" else None
        if body:
            logging.info(f'send_otp_notifications: Request body - {body}')
        
        logging.info('send_otp_notifications: Sending OTP notification.')
        response = send_sms_notification(body)
        logging.info('send_otp_notifications: Notification sent successfully.')
        return response
        
    except Exception as e:
        logging.error(f'send_otp_notifications: Error occurred - {str(e)}', exc_info=True)
        return func.HttpResponse(f"An error occurred: {str(e)}", status_code=500)
