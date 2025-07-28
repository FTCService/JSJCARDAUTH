from rest_framework import serializers
from .models import Template, Group, Campaign
from .models import CustomerHelpTicket
from app_common.models import Business
from django.utils import timezone

class TemplateSerializer(serializers.ModelSerializer):
    type = serializers.ChoiceField(choices=Template.TEMPLATE_TYPES)
    category = serializers.ChoiceField(choices=Template.CATEGORY_CHOICES, required=False, allow_null=True)

    class Meta:
        model = Template
        fields = [
            'id',
            'name',
            'type',
            'category',
            'subject',
            'content',
            'description',
            'created_at',
        ]

    def validate(self, data):
        if data.get("type") == "Email" and not data.get("subject"):
            raise serializers.ValidationError({"subject": "Subject is required for Email templates."})
        return data

class GroupSerializer(serializers.ModelSerializer):
    
    email = serializers.ListField(
        child=serializers.EmailField(),
        read_only=True,
        help_text="List of email addresses (auto-filled based on group_type)"
    )
    mobile_number = serializers.ListField(
        child=serializers.CharField(),
        read_only=True,
        help_text="List of mobile numbers (auto-filled based on group_type)"
    )
    class Meta:
        model = Group
        fields = '__all__'
        read_only_fields = ['email', 'mobile_number', 'created_at']
    
class CampaignSerializer(serializers.ModelSerializer):
    template_id = serializers.PrimaryKeyRelatedField(
        queryset=Template.objects.all(),
        source='template',
        required=False,
        allow_null=True
    )
    group_ids = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        source='groups',
        required=False
    )

    class Meta:
        model = Campaign
        fields = [
            'id',
            'name',
            'type',
            'subject',
            'content',
            'template_id',
            'group_ids',
            'delivery_option',
            'scheduled_time',
            'created_at',
            'updated_at',
        ]

    def validate(self, data):
        delivery_option = data.get('delivery_option')
        scheduled_time = data.get('scheduled_time')
        content = data.get('content')
        template = data.get('template')

        # Enforce content or template
        if not content and not template:
            raise serializers.ValidationError("Either 'content' or 'template_id' must be provided.")

        # Validate scheduling
        if delivery_option == 'Schedule':
            if not scheduled_time:
                raise serializers.ValidationError("'scheduled_time' is required when delivery_option is 'Schedule'.")
            if scheduled_time <= timezone.now():
                raise serializers.ValidationError("'scheduled_time' must be in the future.")

        return data

    def create(self, validated_data):
        groups = validated_data.pop('groups', [])
        campaign = super().create(validated_data)
        campaign.groups.set(groups)
        
        # Optional: Automatically send or schedule here if desired
        # campaign.schedule_if_needed()

        return campaign
    
class CustomerSupportRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomerHelpTicket
        fields = '__all__'