from rest_framework import serializers
from .models import Template, Group, Campaign, MessageStatus
from app_common.models import Business

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
    
    
    class Meta:
        model = Group
        fields = '__all__'
    
class CampaignSerializer(serializers.ModelSerializer):
    template_id = serializers.PrimaryKeyRelatedField(queryset=Template.objects.all(), source='template')
    group_ids = serializers.PrimaryKeyRelatedField(queryset=Group.objects.all(), many=True, source='groups')

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


class MessageStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageStatus
        fields = [
            'id',
            'type',  # renamed from 'channel'
            'message_id',
            'recipient',
            'status',
            'event_type',
            'timestamp',
            'raw_payload'
        ]