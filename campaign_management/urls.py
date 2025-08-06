from django.urls import path
from . import views



urlpatterns = [
    path("template/", views.TemplateAPIView.as_view(), name="template-api"),
    path("groups/", views.GroupAPIView.as_view(), name="group-list-create"),
    path("campaigns/", views.CampaignAPIView.as_view(), name="campaign-api"),
   
]