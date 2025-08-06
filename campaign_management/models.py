from django.db import models


class Template(models.Model):
    TEMPLATE_TYPES = [
        ('Email', 'Email'),
        ('SMS', 'SMS'),
        ('WhatsApp', 'WhatsApp'),
    ]

    CATEGORY_CHOICES = [
        ('Onboarding', 'Onboarding'),
        ('Newsletter', 'Newsletter'),
        ('Promotional', 'Promotional'),
        ('Transactional', 'Transactional'),
        ('Reminder', 'Reminder'),
        ('Announcement', 'Announcement'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TEMPLATE_TYPES)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)  # For Email only
    content = models.TextField()
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

class Group(models.Model):
    GROUP_TYPE_CHOICES = [
        ('business', 'Business'),
        ('member', 'Member'),
        ('staff', 'Staff'),
        ('all', 'All'),
    ]

    name = models.CharField(max_length=255)
    group_type = models.CharField(
        max_length=20,
        choices=GROUP_TYPE_CHOICES,
        default='member'  # You can change 'member' to any default you prefer
    )
    description = models.TextField(blank=True, null=True)
    email = models.JSONField(default=list, blank=True)
    mobile_number = models.JSONField(default=list, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name





class Campaign(models.Model):
    CAMPAIGN_TYPES = [
        ('Email', 'Email'),
        ('SMS', 'SMS'),
        ('WhatsApp', 'WhatsApp'),
    ]

    DELIVERY_OPTIONS = [
        ('Send Now', 'Send Now'),
        ('Schedule', 'Schedule'),
    ]

    name = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=CAMPAIGN_TYPES)
    subject = models.CharField(max_length=255, blank=True, null=True)  # For email subject
    content = models.TextField(blank=True, null=True)  # Custom content or template content
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True, blank=True)
    groups = models.ManyToManyField(Group, related_name='campaigns', blank=True)
    delivery_option = models.CharField(max_length=20, choices=DELIVERY_OPTIONS, default='Send Now')
    scheduled_time = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.type})"

