from django.urls import path
from . import views 

urlpatterns = [
    path('lead-followups/', views.LeadFollowUpView.as_view(), name='lead-followups'),
    
    path('lead-followups/<int:pk>/comment/', views.LeadFollowUpCommentAppendView.as_view(), name='lead-followup-comment'),

]
