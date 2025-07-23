from django.urls import path
from . import views



urlpatterns = [
    path("template/", views.TemplateAPIView.as_view(), name="template-api"),
    path("groups/", views.GroupAPIView.as_view(), name="group-list-create"),
    path("campaigns/", views.CampaignAPIView.as_view(), name="campaign-api"),
    # ✅ Add this line to fetch campaign status
    path("campaigns/<int:campaign_id>/status/", views.CampaignStatusAPIView.as_view(), name="campaign-status"),
]