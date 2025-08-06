from django.db import models
from django.conf import settings
from django.utils import timezone
from app_common.models import Member, Business, User

class LeadFollowUp(models.Model):
    STATUS_CHOICES = [
        ("hot", "Hot"),
        ("cold", "Cold"),
        ("neutral", "Neutral"),
    ]
    
    LEAD_TYPE_CHOICES = [
        ("member", "Member"),
        ("institute", "Institute"),
        ("business", "Business"),
    ]

    lead_type = models.CharField(
        max_length=20,
        choices=LEAD_TYPE_CHOICES,
        verbose_name="Lead Type"
    )
    member = models.ForeignKey(
        'app_common.Member',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lead_followups',
        to_field='mbrcardno',  # This tells Django to use mbrcardno instead of PK
        verbose_name="Member Card Number"
    )

    business = models.ForeignKey(
        'app_common.Business',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lead_followups',
        to_field='business_id',  # This tells Django to use business_id instead of PK
        verbose_name="Business ID"
    )

    status = models.CharField(max_length=10, choices=STATUS_CHOICES)
    comments = models.JSONField(default=list)
    created_by = models.ForeignKey(
        'app_common.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='lead_followups'
    )
    created_at = models.DateTimeField(default=timezone.now)

    def append_comment(self, text, user):
        new_comment = {
            "text": text,
            "added_by": str(user),
            "added_at": timezone.now().isoformat()
        }
        self.comments.append(new_comment)
        self.save()

    def __str__(self):
        return f"{self.get_status_display()} - {self.member or self.business}"
