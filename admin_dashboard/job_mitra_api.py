

from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_common.models import Member
from . import serializers
from helpers.utils import send_otp_to_mobile
from app_common.authentication import UserTokenAuthentication
from django.db.models import Q
from app_common.serializers import MemberRegistrationSerializer
from django.contrib.auth.hashers import make_password



class FilteredMemberListApi(APIView):
    """
    API to retrieve members filtered by village, pincode, or block from meta_data.
    """

    authentication_classes = [UserTokenAuthentication]  # optional
    permission_classes = [IsAuthenticated]  # optional

    @swagger_auto_schema(
        operation_description="Get members by village, pincode, or block (searches in meta_data).",
        manual_parameters=[
            openapi.Parameter('village', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('pincode', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
            openapi.Parameter('block', openapi.IN_QUERY, type=openapi.TYPE_STRING, required=False),
        ],
        responses={200: openapi.Response(description="List of matching members")},
        tags=["Job Mitra"]
    )
    def get(self, request):
        village = request.GET.get("village")
        pincode = request.GET.get("pincode")
        block = request.GET.get("block")

        filters = Q()

        if village:
            filters |= Q(meta_data__village__iexact=village)
        if pincode:
            filters |= Q(meta_data__pincode__iexact=pincode)
        if block:
            filters |= Q(meta_data__block__iexact=block)

        if not filters:
            return Response({
                "success": False,
                "message": "At least one filter (village, pincode, block) is required."
            }, status=status.HTTP_400_BAD_REQUEST)

        members = Member.objects.filter(filters)

        serializer = MemberRegistrationSerializer(members, many=True)
        return Response({
            "success": True,
            "count": len(serializer.data),
            "data": serializer.data
        }, status=status.HTTP_200_OK)




class MemberListByJobMitraLocationApi(APIView):
    """
    API to retrieve members whose location (village/block/pincode)
    matches the logged-in Job Mitra user's location.
    """

    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get members matching Job Mitra's location (village, block, or pincode).",
        responses={
            200: openapi.Response(
                description="List of matched members",
                schema=openapi.Schema(
                    type=openapi.TYPE_OBJECT,
                    properties={
                        "success": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                        "count": openapi.Schema(type=openapi.TYPE_INTEGER, example=1),
                        "data": openapi.Schema(
                            type=openapi.TYPE_ARRAY,
                            items=openapi.Schema(
                                type=openapi.TYPE_OBJECT,
                                properties={
                                    "full_name": openapi.Schema(type=openapi.TYPE_STRING, example="nitish kumar jha"),
                                    "first_name": openapi.Schema(type=openapi.TYPE_STRING, example="nitish"),
                                    "last_name": openapi.Schema(type=openapi.TYPE_STRING, example="jha"),
                                    "mbraddress": openapi.Schema(type=openapi.TYPE_STRING, example="bhubaneswar"),
                                    "MbrPincode": openapi.Schema(type=openapi.TYPE_STRING, example="847301"),
                                    "mbrcardno": openapi.Schema(type=openapi.TYPE_INTEGER, example=3109607606164910),
                                    "email": openapi.Schema(type=openapi.TYPE_STRING, example="mer1@jsj.com"),
                                    "contact_with_country": openapi.Schema(type=openapi.TYPE_STRING, example="91 7462982798"),
                                    "MbrStatus": openapi.Schema(type=openapi.TYPE_BOOLEAN, example=True),
                                    "state": openapi.Schema(type=openapi.TYPE_STRING, example="Odisha"),
                                    "district": openapi.Schema(type=openapi.TYPE_STRING, example="Khurda"),
                                    "block": openapi.Schema(type=openapi.TYPE_STRING, example="Bhubaneswar"),
                                    "village": openapi.Schema(type=openapi.TYPE_STRING, example="Patia"),
                                    "pincode": openapi.Schema(type=openapi.TYPE_STRING, example="751024"),
                                }
                            )
                        )
                    }
                )
            )
        },
        tags=["Job Mitra"]
    )
    def get(self, request):
        jobmitra = request.user

        village = jobmitra.address.get("village")
        pincode = jobmitra.address.get("pincode")
        block = jobmitra.address.get("block")

        if not any([village, pincode, block]):
            return Response({
                "success": False,
                "message": "No location data (village, block, pincode) found in Job Mitra profile."
            }, status=status.HTTP_400_BAD_REQUEST)

        filters = Q()
        if village:
            filters |= Q(address__village__iexact=village)
        if pincode:
            filters |= Q(address__pincode__iexact=pincode)
        if block:
            filters |= Q(address__block__iexact=block)

        matched_members = Member.objects.filter(filters).distinct()

        serializer = MemberRegistrationSerializer(matched_members, many=True)
        return Response({
            "success": True,
            "count": len(serializer.data),
            "data": serializer.data
        }, status=status.HTTP_200_OK)





class AddMemberByJobMitraApi(APIView):
    """
    API to add a new member user (job mitra Only).
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.JobMitraAddMemberSerializer,
        tags=["Job Mitra"]  # ✅ Grouping under "Job Mitra"
    )
   
    def post(self, request):
        referal_id = request.user.employee_id
        data = request.data

        # ✅ Check for existing mobile/email BEFORE serializer validation
        email = data.get("email")
        mobile_number = data.get("mobile_number")

        if Member.objects.filter(email=email).exists():
            return Response({
                "success": False,
                "message": "Member with this email already exists."
            }, status=status.HTTP_200_OK)

        if Member.objects.filter(mobile_number=mobile_number).exists():
            return Response({
                "success": False,
                "message": "Member with this mobile number already exists."
            }, status=status.HTTP_200_OK)

        # Now validate the rest
        serializer = serializers.JobMitraAddMemberSerializer(data=data)
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
        tags=["Job Mitra"]
    )
    def get(self, request):
        """Retrieve all job mitra member."""
   
        referal_id = request.user.employee_id
        staff_users = Member.objects.filter(MbrReferalId=referal_id)
        serializer = serializers.JobMitraMemberListSerializer(staff_users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)