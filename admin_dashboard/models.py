from django.db import models

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



    