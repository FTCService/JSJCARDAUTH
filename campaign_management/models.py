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
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    tags = models.CharField(max_length=255, help_text="Comma-separated tags", blank=True)
    company = models.CharField(max_length=255, blank=True, null=True)
    
    email = models.JSONField(default=list, blank=True, null=True)  # ✅ Should be JSONField
    mobile_number = models.JSONField(default=list, blank=True, null=True)  # ✅ Should be JSONField
    
    created_at = models.DateTimeField(auto_now_add=True)



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


class MessageStatus(models.Model):
    campaign = models.ForeignKey('Campaign', on_delete=models.CASCADE, related_name='statuses')  # ✅ Add this
    channel = models.CharField(max_length=20)  # Email, SMS, WhatsApp
    message_id = models.CharField(max_length=255, blank=True, null=True)
    recipient = models.CharField(max_length=255)
    status = models.CharField(max_length=20)  # sent, delivered, seen, failed
    event_type = models.CharField(max_length=50, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    raw_payload = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"{self.channel} | {self.recipient} | {self.status}"