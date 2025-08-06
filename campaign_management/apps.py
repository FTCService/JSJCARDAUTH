from django.apps import AppConfig

class CampaignManagementConfig(AppConfig):  # ✅ Correct class name
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'campaign_management'            # ✅ Correct app path
