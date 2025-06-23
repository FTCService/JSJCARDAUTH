from rest_framework import serializers
from app_common.models import Member
from member import models


class JobProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.JobProfile
        fields = '__all__'