from datetime import datetime
import azure.functions as func
from crud_operations.db_connection import get_db_connection
from atomberg_locks.lock_functions import generate_otp_lock
from datetime import datetime

def time_to_epoch(date_str, time_str):
    # Round the time to the nearest hour
    time_obj = datetime.strptime(time_str, "%H:%M:%S")
    rounded_hour = time_obj.replace(minute=0, second=0)
    combined = f"{date_str} {rounded_hour.strftime('%H:%M:%S')}"
    return int(datetime.strptime(combined, "%Y-%m-%d %H:%M:%S").timestamp())

def extract_columns(data):
    extracted_data = []
    hotel_code = data.get("hotel_code")
    reservations = data.get("data", {}).get("Reservations", {}).get("Reservation", [])
    
    for reservation in reservations:
        for booking_tran in reservation.get("BookingTran", []):
            guest_name = " ".join(filter(None, [reservation.get("Salutation"), reservation.get("FirstName"), reservation.get("LastName")]))
            guest_mobile_number = reservation.get("Mobile")
            guest_email = reservation.get("Email")
            reservation_number = booking_tran.get("SubBookingId")
            
            check_in_date = booking_tran.get("Start")
            arrival_time = booking_tran.get("ArrivalTime", "00:00:00")
            check_out_date = booking_tran.get("End")
            departure_time = booking_tran.get("DepartureTime", "00:00:00")
            
            check_in_date_time = time_to_epoch(check_in_date, arrival_time)
            check_out_date_time = time_to_epoch(check_out_date, departure_time)
            
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
    return extracted_data

def handle_hotel_guest_otp_crud(method, params, body):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        if method == "GET":
            # Get filtering criteria from query parameters
            created = params.get("created")  # specific day (YYYY-MM-DD)
            start_date = params.get("start_date")  # date range start (YYYY-MM-DD)
            end_date = params.get("end_date")  # date range end (YYYY-MM-DD)
            current_day = params.get("current_day")  # flag to fetch today's records
            
            query = "SELECT * FROM hotel_guest_otp_record WHERE 1=1"
            params_list = []

            # Check if 'current_day' flag is passed to get today's records
            if current_day and current_day.lower() == "true":
                today = datetime.today().strftime('%Y-%m-%d')  # Get today's date in 'YYYY-MM-DD' format
                query += " AND CAST(check_in_date_time AS DATE) = ?"
                params_list.append(today)
            
            # If 'created' is passed to fetch records for a specific day
            elif created:
                query += " AND CAST(check_in_date_time AS DATE) = ?"
                params_list.append(created)
            
            # If 'start_date' and 'end_date' are passed for a date range filter
            elif start_date and end_date:
                query += " AND CAST(check_in_date_time AS DATE) BETWEEN ? AND ?"
                params_list.extend([start_date, end_date])

            # Execute the query to get the total count of records (without pagination)
            cursor.execute(query, params_list)
            total_records = len(cursor.fetchall())  # Get total count of matching records

            # Add pagination to the query
            page = int(params.get("page", 1))  # Default to page 1 if not provided
            page_size = int(params.get("page_size", 2))  # Default to 2 records per page
            offset = (page - 1) * page_size  # Calculate the offset
            query += " ORDER BY check_in_date_time OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params_list.extend([offset, page_size])

            # Execute the query to fetch the paginated records
            cursor.execute(query, params_list)
            result = cursor.fetchall()

            # Format the result as JSON or any other format using column names from cursor.description
            columns = [desc[0] for desc in cursor.description]  # Extract column names
            response_data = []
            for row in result:
                row_dict = {columns[i]: row[i] for i in range(len(columns))}  # Create a dictionary with column names as keys
                
                # Convert datetime fields to string in 'YYYY-MM-DD HH:MM:SS' format
                for key, value in row_dict.items():
                    if isinstance(value, datetime):
                        row_dict[key] = value.strftime('%Y-%m-%d %H:%M:%S')  # Format datetime

                response_data.append(row_dict)

            # Format the result as JSON with pagination details
            return func.HttpResponse(
                str({
                    "data": response_data,
                    "page": page,
                    "page_size": page_size,
                    "total_records": total_records,  # Total records before pagination
                    "total_pages": (total_records + page_size - 1) // page_size  # Total pages based on the total records
                }),
                mimetype="application/json"
            )
        
        elif method == "POST":
            # Insert a new record (same as before)
            paramdata=extract_columns(body)
            for item in paramdata:  
                hotel_code = item.get("hotel_code")
                guest_name = item.get("guest_name")
                room_no=item.get("room_no")
                room_name=item.get("room_name")
                reservation_number=item.get("reservation_number")
                otp_status="OTP Generated"
                guest_mobile_number = item.get("guest_mobile_number")
                guest_email = item.get("guest_email")
                check_in_date_time = item.get("check_in_date_time")
                check_out_date_time = item.get("check_out_date_time")
                if room_no!=None:
                    generated_otp_object = generate_otp_lock(room_no,check_in_date_time,check_out_date_time)
                    print(generated_otp_object)
                    if generated_otp_object!=None:
                        generated_otp=int(generated_otp_object['otp'])
                        otp_start_date_time = str(datetime.fromtimestamp(int(generated_otp_object['validStartTime'])).strftime("%Y-%m-%dT%H:%M:%S"))
                        otp_end_date_time = str(datetime.fromtimestamp(int(generated_otp_object['validEndTime'])).strftime("%Y-%m-%dT%H:%M:%S"))
                        check_in_date_time=str(datetime.fromtimestamp(int(check_in_date_time)).strftime("%Y-%m-%dT%H:%M:%S"))
                        check_out_date_time=str(datetime.fromtimestamp(int(check_out_date_time)).strftime("%Y-%m-%dT%H:%M:%S"))
                        print(check_in_date_time,check_out_date_time)
                        cursor.execute("""INSERT INTO dbo.hotel_guest_otp_record (
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
                        (hotel_code,
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
                         ))
            conn.commit()
                
            return func.HttpResponse(f"OTP record added successfully.") 
        
        else:
            return func.HttpResponse("Unsupported HTTP method.", status_code=405)
