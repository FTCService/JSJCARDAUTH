from django.urls import path
from . import views, business_api


app_name = "app_common"

urlpatterns = [
    
    path("admin/add-staff/", views.AddStaffApi.as_view(), name="add-staff"),
    
    
    path("member/signup/", views.MemberSignupApi.as_view(), name="member-signup"),
    path("member/verify/otp/", views.MemberVerifyOtpApi.as_view(), name="member-verify-otp"),
    path("member/resend/otp/", views.MemberResendOtpApi.as_view(), name="member-resend-otp"),
    
    # 🔹 Login
    path("member/login/", views.MemberLoginApi.as_view(), name="member-login"),
    path("member/logout/", views.MemberLogoutApi.as_view(), name="logout"),
    path("member/forgot-pin/", views.MemberForgotPinAPI.as_view(), name="member-forgot-pin"),
    path("member/reset-pin/", views.MemberResetPinAPI.as_view(), name="member-reset-pin"),
    
    

    
    
    path("business/signup/", business_api.BusinessSignupApi.as_view(), name="business-signup"),
    path("business/verify/otp/", business_api.BusinessVerifyOtpApi.as_view(), name="business-verify-otp"),
    path("business/login/", business_api.BusinessLoginApi.as_view(), name="business-login"),
    path("business/forgot-pin/", business_api.BusinessForgotPinAPI.as_view(), name="business-forgot-pin"),
    path("business/reset-pin/", business_api.BusinessResetPinAPI.as_view(), name="business-reset-pin"),
    path("business/registration/", business_api.BusinessRegistrationApi.as_view(), name="business-registration"),
    path("business/kyc/", business_api.BusinessKycApi.as_view(), name="business-kyc"),
    path("busienss/logout/", business_api.BusinessLogoutApi.as_view(), name="business-logout"),
    path('verify-token/', business_api.VerifyBusinessTokenApi.as_view(), name='verify-token'),
]
