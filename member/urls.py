from django.urls import path

from . import views

app_name = "member"


urlpatterns = [
    
    path('job-profile/', views.JobProfileAPI.as_view(), name='job-profile-list-create'),
    path("jobprofile-fields/", views.CategoryFieldsFormattedApi.as_view(), name="jobprofile-fields"),
    path('job/profile/', views.RemoteJobprofileOfMember.as_view(), name='jobprofile-details'),
  
     

]