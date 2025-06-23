from django.db import models
from app_common.models import Member 

# Create your models here.

class JobProfile(models.Model):
    MbrCardNo = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='JobProfile', to_field="mbrcardno")
    BasicInformation = models.JSONField(default=dict)  
    CareerObjectivesPreferences = models.JSONField(default=dict)  
    EducationDetails = models.JSONField(default=dict)  
    WorkExperience = models.JSONField(default=dict)  
    SkillsCompetencies = models.JSONField(default=dict)  
    AchievementsExtracurricular = models.JSONField(default=dict)  
    OtherDetails = models.JSONField(default=dict)  

    # Timestamp fields
    CreatedAt = models.DateTimeField(auto_now_add=True)
    UpdatedAt = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Job Profile of {self.MbrCardNo.full_name}"  