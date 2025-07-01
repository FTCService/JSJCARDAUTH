

from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_common.models import Member
from admin_dashboard import serializers
from helpers.utils import send_otp_to_mobile
from app_common.authentication import BusinessTokenAuthentication
from django.db.models import Q
from app_common.serializers import MemberRegistrationSerializer
from django.contrib.auth.hashers import make_password



class AddMemberByInstituteApi(APIView):
    """
    API to add a new member user (Institute Only).
    """
    authentication_classes = [BusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.JobMitraAddMemberSerializer,
        tags=["Institute"]  # ✅ Grouping under "Job Mitra"
    )
   
    def post(self, request):
        referal_id = request.user.business_id
        serializer = serializers.JobMitraAddMemberSerializer(data=request.data)
        if serializer.is_valid():
            full_name = serializer.validated_data["full_name"]
            email = serializer.validated_data["email"]
            pin = serializer.validated_data["pin"]
            mobile_number = serializer.validated_data["mobile_number"]
            state = serializer.validated_data.get("state")
            district = serializer.validated_data.get("district")
            block = serializer.validated_data.get("block")
            village = serializer.validated_data.get("village")
            pincode = serializer.validated_data.get("pincode")
            # Check if the email is already used
            if Member.objects.filter(email=email, mobile_number=mobile_number).exists():
                return Response({"error": "User with this email already exists"}, status=status.HTTP_400_BAD_REQUEST)

            # Build meta_data dict
            address = {
                "state": state,
                "district": district,
                "block": block,
                "village": village,
                "pincode": pincode
            }
            # Create staff user
            user = Member.objects.create(
                email=email,
                pin=make_password(pin),
                full_name=full_name,
                mobile_number=mobile_number,
                MbrReferalId=referal_id,
                address=address
            )
            user.save()
            return Response({"message": "member added successfully"}, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        responses={200: serializers.JobMitraMemberListSerializer(many=True)},
        tags=["Institute"]
    )
    def get(self, request):
        """Retrieve all  member."""
   
        referal_id = request.user.business_id
        staff_users = Member.objects.filter(MbrReferalId=referal_id)
        serializer = serializers.JobMitraMemberListSerializer(staff_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)