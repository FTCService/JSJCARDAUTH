from rest_framework import serializers

from app_common.models import Member, Business
from .models import LeadFollowUp
# class LeadFollowUpSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = LeadFollowUp
#         fields = '__all__'
        
        


class MemberBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['mbrcardno', 'full_name', 'mobile_number']

class BusinessBriefSerializer(serializers.ModelSerializer):
    class Meta:
        model = Business
        fields = ['business_id', 'business_name', 'mobile_number']

class LeadFollowUpSerializer(serializers.ModelSerializer):
    member = MemberBriefSerializer(read_only=True)
    business = BusinessBriefSerializer(read_only=True)

    class Meta:
        model = LeadFollowUp
        fields = [
            'id', 'lead_type', 'member', 'business', 'status',
            'comments', 'created_by', 'created_at'
        ]
