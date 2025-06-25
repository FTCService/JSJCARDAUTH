from django.urls import path
from . import views, business_api, goverment_api


app_name = "app_common"

urlpatterns = [
    
 
    
    path("admin/add-staff/", views.AddStaffApi.as_view(), name="add-staff"),
    path("upload-members/", views.BulkMemberUploadView.as_view(), name="upload-members"),
    path("upload-business/", business_api.BulkBusinessUploadView.as_view(), name="upload-business"),
    
    path("upload-business/kyc/", business_api.BulkBusinessKycUpload.as_view(), name="upload-business-kyc"),
    
    
    
    path("member/signup/", views.MemberSignupApi.as_view(), name="member-signup"),
    path("member/verify/otp/", views.MemberVerifyOtpApi.as_view(), name="member-verify-otp"),
    path("member/resend/otp/", views.MemberResendOtpApi.as_view(), name="member-resend-otp"),
    
    # 🔹 Login
    path("member/login/", views.MemberLoginApi.as_view(), name="member-login"),
    # 🔹 Registration (Complete Profile/Details Update)
    path("member/registration/", views.MemberRegistrationApi.as_view(), name="member-registration"),
    path("member/logout/", views.MemberLogoutApi.as_view(), name="logout"),
    path("member/forgot-pin/", views.MemberForgotPinAPI.as_view(), name="member-forgot-pin"),
    path("member/reset-pin/", views.MemberResetPinAPI.as_view(), name="member-reset-pin"),
    path("member/change-pin/", views.MemberChangePinAPI.as_view(), name="change-pin"),
    
    path('member/verify-token/', views.VerifyMemberTokenApi.as_view(), name='member-verify-token'),

    path("business/signup/", business_api.BusinessSignupApi.as_view(), name="business-signup"),
    path("business/verify/otp/", business_api.BusinessVerifyOtpApi.as_view(), name="business-verify-otp"),
    path("business/login/", business_api.BusinessLoginApi.as_view(), name="business-login"),
    path("business/forgot-pin/", business_api.BusinessForgotPinAPI.as_view(), name="business-forgot-pin"),
    path("business/reset-pin/", business_api.BusinessResetPinAPI.as_view(), name="business-reset-pin"),
    path("business/registration/", business_api.BusinessRegistrationApi.as_view(), name="business-registration"),
    path("business/kyc/", business_api.BusinessKycApi.as_view(), name="business-kyc"),
    path("busienss/logout/", business_api.BusinessLogoutApi.as_view(), name="business-logout"),
    
    path('business/details/', business_api.BusinessDetailsByIdAPI.as_view(), name='business-details'),
    
    
    # these three api send data to reward and event
    path('verify-token/', business_api.VerifyBusinessTokenApi.as_view(), name='verify-token'),
    path('member-details/', views.MemberDetailsByMobileAPI.as_view(), name='member-details'),
    path('cardno/member-details/', views.MemberDetailsByCardNoAPI.as_view(), name='by-cardno-member-details'),
    
    path('initiate-card-assignment/', business_api.InitiateCardAssignmentView.as_view(), name="initiate-card-assignment"),
    path('card-mappings/list/', business_api.AllCardMappingsByBusiness.as_view(), name='business-card-mappings'),
    
    path('physical-cards/list/', business_api.PhysicalCardsByBusinessID.as_view(), name='business-physical-cards'),
    
    # 🔹 admin and staf Login
    path("admin-staff-login/", views.AdminStaffLoginApi.as_view(), name="admin-staff-login"),
    
    path("user/verify-token/", views.VerifyAdminStaffTokenApi.as_view(), name="user-verify-token"),
    
    
    path("goverment/login/", goverment_api.GovermentLoginApi.as_view(), name="goverment-login"),
    path("goverment/logout/", goverment_api.GovernmentLogoutApi.as_view(), name="goverment-logout"),
]
