import random
import requests
import threading
from django.core.cache import cache
import urllib.parse
import pytz
from datetime import datetime
from django.conf import settings


def send_fast2sms(mobile_number, otp_code):
    def send_sms():
        try:
            url = "https://www.fast2sms.com/dev/bulkV2"
            payload = {
                "route": "dlt",
                "sender_id": "JSJCRD",  # Your approved sender ID
                "message": "188963",    # Template ID created in Fast2SMS
                "variables_values": f"{otp_code}|",  # Ensure this matches your template variables
                "flash": 0,
                "numbers": mobile_number
            }
            headers = {
                "authorization": "Ba7thi9AQFlaAo80KrODiv5bgUT9BD97vRXqlSfL7atLqC3jXXF2ysL0V2Ya",
                "Content-Type": "application/json"
            }

            response = requests.post(url, json=payload, headers=headers)
            print("📨 SMS API Response:", response.status_code, response.text)

        except Exception as e:
            print(f"❌ Exception while sending SMS: {e}")

    threading.Thread(target=send_sms).start()





def send_otp_to_mobile(payload):
  
    mobile_number = payload.get("mobile_number")
    otp = payload.get("otp")
    print(mobile_number, otp,"--------------------------------")

    if not mobile_number:
        return {"error": "Mobile number is required"}

    # Store OTP in cache (valid for 5 minutes)
    cache.set(f"otp_{mobile_number}", otp, timeout=300)

    # Send OTP via SMS API
    message = f" hi from jsj Your OTP is {otp}. It is valid for 5 minutes."
    encoded_message = requests.utils.quote(message)  # URL encode the message

    sms_api_url = f"https://7l7dy2zq63.execute-api.ap-south-1.amazonaws.com/default/smsapi/?option=publishMessage&passKey=IamJiseniorJi@374&phoneNumber={mobile_number}&customMessage={encoded_message}"

    try:
        response = requests.get(sms_api_url)
        if response.status_code == 200:
            return {"message": "OTP sent successfully"}
        else:
            return {"error": "Failed to send OTP"}
    except Exception as e:
        return {"error": str(e)}
    
    

def get_member_active_in_marchant(card_number, business_id):
    try:
        response = requests.get(
            settings.REWARD_SERVER_URL + "/member/active_in_clube/",
            params={"card_number": card_number, "business_id": business_id}
        )
        print(response, "response")
        if response.status_code == 200:
            return response.json()
        return None
    except requests.RequestException as e:
        print(f"Error contacting auth service: {e}")
        return None

