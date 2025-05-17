from django.urls import path
from . import views


app_name= "admin_dashboard"

urlpatterns = [
  
  path("member/list/", views.MemberListApi.as_view(), name="member-list"),
  path('members/<int:pk>/', views.MemberDetailApi.as_view(), name='member-detail'),
  
  path("business/list/", views.BusinessListApi.as_view(), name="business-list"),
  path('business/<int:id>/', views.BusinessDetailsApi.as_view(), name='business-details'),
  path("admin/dashboard/", views.AdminDashboard.as_view(), name="admin-dashboard"),
  path("business/kyc/verify/<int:business_id>/", views.VerifyBusinessKycApi.as_view(), name="verify-business-kyc"),
  
  
  path("card-purpose/", views.CardPurposeListApi.as_view(), name="card-purpose-list"),
  path("card-purpose/create/", views.CardPurposeCreateApi.as_view(), name="card-purpose-create"),
  path("card-purpose/<int:pk>/", views.CardPurposeDetailApi.as_view(), name="card-purpose-detail"),
  
  path("category/", views.CategoryListCreateApi.as_view(), name="category_list_create"),
  path("category/<int:category_id>/", views.CategoryDetailApi.as_view(), name="category_detail"),
  path('category/profile-fields/', views.JobProfileFieldListByCategory.as_view(), name='job-profile-fields'),
  
  
  path("fields/", views.JobProfileFieldListApi.as_view(), name="list-fields"),
  path("fields/create/", views.JobProfileFieldCreateApi.as_view(), name="create-field"),
  path("fields/<int:id>/", views.JobProfileFieldDetailApi.as_view(), name="field-detail"),
  
  
]

  
