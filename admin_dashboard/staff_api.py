from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_common.models import Member,Business,User, BusinessKyc
from . import serializers
from admin_dashboard.models import CardPurpose
from helpers.utils import send_otp_to_mobile
from django.shortcuts import get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from app_common.authentication import UserTokenAuthentication
from app_common.models import PhysicalCard
from collections import defaultdict
import random



class StaffDashboard(APIView):
    """
    API to get the total count of registered businesses.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve the total count of registered businesses.",
        responses={200: openapi.Response("Total number of businesses", schema=openapi.Schema(type=openapi.TYPE_INTEGER))}
    )
    def get(self, request):
        total_businesses = Business.objects.count()  # Get the total count of businesses
        total_members = Member.objects.count() # Get the total count of

        return Response(
            {
                "success": True,
                "total_businesses": total_businesses,
                "total_members": total_members
            },
            status=status.HTTP_200_OK
        )