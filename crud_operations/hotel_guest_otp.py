import logging
import azure.functions as func
from datetime import datetime,timedelta
import pytz
import json
from crud_operations.db_connection import get_db_connection
from atomberg_locks.lock_functions import generate_otp_lock
from otp_notifications.sendnotifications import send_whatsapp_notification, send_sms_notification


def formatdatetime(datetime_str):
    """Formats a datetime string to the desired format."""
    return datetime.strptime(datetime_str[:19], "%Y-%m-%dT%H:%M:%S")\
        .replace(tzinfo=pytz.UTC)\
        .astimezone(pytz.timezone("Asia/Kolkata"))\
        .strftime("%d %b %Y, %I:%M %p")\
        .replace("pm", "p.m.").replace("am", "a.m.")


def call_send_notifications(data):
    """Send notifications via WhatsApp and SMS."""
    for item in data:
        send_whatsapp_notification(json.dumps(item))
        send_sms_notification(json.dumps(item))

def time_to_epoch(date_str, time_str, operation="default"):
    """
    Converts a date and time string to an epoch timestamp with an optional operation to add or subtract 1 hour.
    
    Parameters:
        date_str (str): The input date as a string in the format 'YYYY-MM-DD'.
        time_str (str): The input time as a string in the format 'HH:MM:SS'.
        operation (str): The operation to perform - 'add', 'subtract', or 'default'. Default is 'default'.
    
    Returns:
        int: The epoch timestamp of the modified (or unmodified) date and time.
    """
    try:
        # Combine the date and time strings into a single datetime object
        combined_datetime = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
        logging.info(f"Combined datetime string: {combined_datetime}")

        # Add or subtract 1 hour based on the operation
        if operation == "checkout":
            combined_datetime -= timedelta(hours=5)
        elif operation == "checkin":
            combined_datetime -= timedelta(hours=6)
        elif operation != "default":
            raise ValueError("Invalid operation. Use 'add', 'subtract', or 'default'.")

        # Convert to epoch timestamp
        epoch_time = int(combined_datetime.timestamp())
        return epoch_time
    except Exception as e:
        logging.error(f"Error in time_to_epoch: {e}")
        raise

def extract_columns(data):
    """Extracts columns from the provided data."""
    logging.info("Extracting columns from payload.")
    try:
        extracted_data = []
        hotel_code = data.get("hotel_code")
        reservations = data.get("data", {}).get("Reservations", {}).get("Reservation", [])

        for reservation in reservations:
            for booking_tran in reservation.get("BookingTran", []):
                guest_name = " ".join(filter(None, [reservation.get("Salutation"), reservation.get("FirstName"), reservation.get("LastName")]))
                guest_mobile_number = reservation.get("Mobile")

                # Validate and trim mobile number if necessary
                if guest_mobile_number and len(guest_mobile_number) > 10:
                    guest_mobile_number = guest_mobile_number[-10:]  # Keep only the last 10 digits
                    logging.warning(f"Trimmed mobile number to: {guest_mobile_number}")

                guest_email = reservation.get("Email")
                reservation_number = booking_tran.get("SubBookingId")

                check_in_date = booking_tran.get("Start")
                arrival_time = booking_tran.get("ArrivalTime", "00:00:00")
                check_out_date = booking_tran.get("End")
                departure_time = booking_tran.get("DepartureTime", "00:00:00")

                check_in_date_time = time_to_epoch(check_in_date, arrival_time,"checkin")
                check_out_date_time = time_to_epoch(check_out_date, departure_time,"checkout") 
                for rental in booking_tran.get("RentalInfo", []):
                    room_no = rental.get("RoomName")
                    room_name = rental.get("RoomName")

                    extracted_data.append({
                        "hotel_code": hotel_code,
                        "guest_name": guest_name,
                        "room_no": room_no,
                        "room_name": room_name,
                        "reservation_number": reservation_number,
                        "guest_mobile_number": guest_mobile_number,
                        "guest_email": guest_email,
                        "check_in_date_time": check_in_date_time,
                        "check_out_date_time": check_out_date_time
                    })
        logging.info(f"Extracted data: {extracted_data}")
        return extracted_data
    except Exception as e:
        logging.error(f"Error extracting columns: {str(e)}", exc_info=True)
        raise


def handle_hotel_guest_otp_crud(method, params, body):
    """Handles CRUD operations for hotel guest OTP."""
    logging.info(f"Handling request with method: {method}")

    with get_db_connection() as conn:
        cursor = conn.cursor()

        if method == "GET":
            reservation_number = params.get("reservation_number")
            guest_mobile_number = params.get("guest_mobile_number")
            check_in_date_time = params.get("check_in_date_time")  # Specific date (YYYY-MM-DD)
            hotel_code=params.get("hotel_code")

            query = "SELECT * FROM hotel_guest_otp_record WHERE 1=1"
            params_list = []

            if hotel_code:
                query += " AND hotel_code = ?"
                params_list.append(hotel_code)
            if reservation_number:
                query += " AND reservation_number = ?"
                params_list.append(reservation_number)

            if guest_mobile_number:
                query += " AND guest_mobile_number = ?"
                params_list.append(guest_mobile_number)

            if check_in_date_time:
                query += " AND CAST(check_in_date_time AS DATE) = ?"
                params_list.append(check_in_date_time)

            cursor.execute(query, params_list)
            total_records = len(cursor.fetchall())

            page = int(params.get("page", 1))
            page_size = int(params.get("page_size", 10))
            offset = (page - 1) * page_size
            query += " ORDER BY check_in_date_time OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params_list.extend([offset, page_size])

            cursor.execute(query, params_list)
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            response_data = []
            for row in result:
                row_dict = {columns[i]: row[i] for i in range(len(columns))}
                for key, value in row_dict.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                response_data.append(row_dict)

            return func.HttpResponse(
                json.dumps({
                    "data": response_data,
                    "page": page,
                    "page_size": page_size,
                    "total_records": total_records,
                    "total_pages": (total_records + page_size - 1) // page_size
                }),
                mimetype="application/json"
            )

        elif method == "POST":
            operation = body.get("operation", "").strip().lower()
            if operation != "checkin":
                logging.error(f"Invalid operation: {operation}. Expected 'Checkin'.")
                return func.HttpResponse(
                    "Invalid operation. Only 'Checkin' is supported.", status_code=400
                )

            paramdata = extract_columns(body)
            notification_data = []

            for item in paramdata:
                hotel_code = item.get("hotel_code")
                guest_name = item.get("guest_name", "")
                room_no = item.get("room_no")
                room_name = item.get("room_name")
                reservation_number = item.get("reservation_number", "")
                otp_status = "OTP Generated"
                guest_mobile_number = item.get("guest_mobile_number")
                guest_email = item.get("guest_email")
                check_in_date_time = item.get("check_in_date_time")
                check_out_date_time = item.get("check_out_date_time")

                if room_no:
                    logging.info(f"Generating OTP for room: {room_no}")
                    generated_otp_object = generate_otp_lock(room_no, check_in_date_time, check_out_date_time)
                    if generated_otp_object:
                        generated_otp = str(int(generated_otp_object["otp"]))+"#"
                        otp_start_date_time = datetime.fromtimestamp(int(generated_otp_object["validStartTime"])).strftime("%Y-%m-%dT%H:%M:%S")
                        otp_end_date_time = datetime.fromtimestamp(int(generated_otp_object["validEndTime"])).strftime("%Y-%m-%dT%H:%M:%S")

                        notification_data.append({
                            "phoneNumber": guest_mobile_number,
                            "bodyValues": [
                                guest_name,
                                reservation_number,
                                room_no,
                                generated_otp,
                                formatdatetime(otp_start_date_time),
                                formatdatetime(otp_end_date_time),
                            ],
                        })


                        cursor.execute(
                            """INSERT INTO dbo.hotel_guest_otp_record (
                                hotel_code, 
                                guest_name, 
                                guest_mobile_number,
                                guest_email, 
                                check_in_date_time,
                                check_out_date_time, 
                                generated_otp, 
                                otp_start_date_time, 
                                otp_end_date_time,
                                room_no,
                                room_name,
                                reservation_number,
                                otp_status
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                            (
                                hotel_code,
                                guest_name,
                                guest_mobile_number,
                                guest_email,
                                datetime.fromtimestamp(int(check_in_date_time,)).strftime("%Y-%m-%dT%H:%M:%S"),
                                datetime.fromtimestamp(int(check_out_date_time)).strftime("%Y-%m-%dT%H:%M:%S"),
                                generated_otp,
                                otp_start_date_time,
                                otp_end_date_time,
                                room_no,
                                room_name,
                                reservation_number,
                                otp_status,
                            ),
                        )

            conn.commit()
            logging.info("Database commit successful.")
            call_send_notifications(notification_data)
            return func.HttpResponse("OTP record added successfully.")

        else:
            return func.HttpResponse("Unsupported HTTP method.", status_code=405)
