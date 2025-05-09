from django.urls import path
from . import views, business_api


app_name = "app_common"

urlpatterns = [
    
    path("admin/add-staff/", views.AddStaffApi.as_view(), name="add-staff"),
    
    
    path("member/signup/", views.MemberSignupApi.as_view(), name="member-signup"),
    path("member/verify/otp/", views.MemberVerifyOtpApi.as_view(), name="verify-otp"),
    path("member/resend/otp/", views.MemberResendOtpApi.as_view(), name="member-resend-otp"),
    
    # 🔹 Login
    path("member/login/", views.MemberLoginApi.as_view(), name="member-login"),
    path("member/logout/", views.MemberLogoutApi.as_view(), name="logout"),
    path("member/forgot-pin/", views.MemberForgotPinAPI.as_view(), name="member-forgot-pin"),
    path("member/reset-pin/", views.MemberResetPinAPI.as_view(), name="member-reset-pin"),
    
    
    path("business/signup/", business_api.BusinessSignupApi.as_view(), name="business-signup"),
    path("business/verify/otp/", business_api.BusinessVerifyOtpApi.as_view(), name="verify-otp"),
    path("business/login/", business_api.BusinessLoginApi.as_view(), name="business-login"),
]
