from django.db import models
from app_common.models import Business, GovernmentUser, User
class CardPurpose(models.Model):
    PURPOSE_CHOICES = [
        ('consumer', 'Consumer Card'),
        ('job_apply', 'Job Application Card'),
        ('loyalty', 'Loyalty Card'),
        ('membership', 'Membership Card'),
        ('discount', 'Discount Card'),
    ]

    purpose_name = models.CharField(max_length=50, choices=PURPOSE_CHOICES, default='consumer', unique=True)  # ✅ Default: Consumer Card

    features = models.JSONField(default=list)  

    def __str__(self):
        return f"{self.purpose_name} - {self.features}"


class FieldCategory(models.Model):
    """Model to store field categories"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
    

class JobProfileField(models.Model):
    FIELD_TYPES = [
        ("text", "Text"),
        ("number", "Number"),
        ("email", "Email"),
        ("date", "Date"),
        ("select", "Select"),
        ("checkbox", "Checkbox"),
        ("url", "URL"),
        ("textarea", "Textarea"),
    ]
    category = models.ForeignKey(FieldCategory, on_delete=models.CASCADE, related_name="fields", null=True)
    label = models.CharField(max_length=100)
    field_id = models.CharField(max_length=50, unique=True)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    is_required = models.BooleanField(default=False)
    placeholder = models.CharField(max_length=255, blank=True, null=True)
    value = models.CharField(blank=True, null=True, help_text="Default value (can be empty or null)")
    
    option = models.JSONField(blank=True, null=True, help_text="Options for select or checkbox type fields")

    def __str__(self):
        return self.label

    def to_dict(self):
        """Return field data as dictionary"""
        return {
            "label": self.label,
            "id": self.field_id,
            "type": self.field_type,
            "is_required": self.is_required,
            "placeholder": self.placeholder,
            "value": self.value,
            "option": self.option,
        }
    
    

# models.py
class GovernmentInstituteAccess(models.Model):
    government_user = models.ForeignKey(GovernmentUser,on_delete=models.CASCADE,related_name="assigned_institutes")
    institute = models.ForeignKey(Business,on_delete=models.CASCADE,related_name="assigned_governments")
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.government_user.full_name} -> {self.institute.business_name}"
