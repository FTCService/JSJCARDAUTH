import random
import requests
from django.core.cache import cache
import urllib.parse
import pytz
from datetime import datetime


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

    sms_api_url = f"https://8jzm0a9gbk.execute-api.ap-south-1.amazonaws.com/SMS-API/BulkSMS/?option=publishMessage&passKey=IamJiseniorJi@374&phoneNumber={mobile_number}&customMessage={encoded_message}"

    try:
        response = requests.get(sms_api_url)
        if response.status_code == 200:
            return {"message": "OTP sent successfully"}
        else:
            return {"error": "Failed to send OTP"}
    except Exception as e:
        return {"error": str(e)}