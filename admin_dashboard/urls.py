from django.urls import path
from . import views, staff_api


app_name= "admin_dashboard"

urlpatterns = [
  
  path("member/list/", views.MemberListApi.as_view(), name="member-list"),
  path('members/<int:pk>/', views.MemberDetailApi.as_view(), name='member-detail'),
  
  path("business/list/", views.BusinessListApi.as_view(), name="business-list"),
  path('business/<int:id>/', views.BusinessDetailsApi.as_view(), name='business-details'),
  path("admin/dashboard/", views.AdminDashboard.as_view(), name="admin-dashboard"),
  path("business/kyc/verify/<int:business_id>/", views.VerifyBusinessKycApi.as_view(), name="verify-business-kyc"),
  
  path("staff/dashboard/", staff_api.StaffDashboard.as_view(), name="staff-dashboard"),
  path("staff/add-institute/", staff_api.InstituteSignupApi.as_view(), name="staff-add-institute"),
  

  
  path("card-purpose/", views.CardPurposeListApi.as_view(), name="card-purpose-list"),
  path("card-purpose/create/", views.CardPurposeCreateApi.as_view(), name="card-purpose-create"),
  path("card-purpose/<int:pk>/", views.CardPurposeDetailApi.as_view(), name="card-purpose-detail"),
  
  path('generate-physical-cards/', views.GeneratePhysicalCardsView.as_view(), name='generate_physical_cards'),
  path('physical-cards/of-business/<int:business_id>/', views.PhysicalCardsListByBusiness.as_view(), name='physical_cards_of_business'),
    
  path("add/job_mitra/", staff_api.AddJobMitraApi.as_view(), name="staff-job_mitra"),
  
]

  
