

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
from member.models import JobProfile
from admin_dashboard.models import CardPurpose, FieldCategory
from django.shortcuts import get_object_or_404
from member.serializers import JobProfileSerializer
from .email import send_template_email
import secrets
from . import models
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
                # ✅ Handle multiple purpose entries
            purposes_data = request.data.get("card_purposes", [
                {"purpose": "consumer", "features": ["Reward"]}
            ])

            final_purpose_list = []

            for entry in purposes_data:
                purpose_name = entry.get("purpose", "consumer")
                features = entry.get("features", [])

                purpose_obj = CardPurpose.objects.filter(purpose_name=purpose_name).first()
                if purpose_obj:
                    final_purpose_list.append({
                        "id": purpose_obj.id,
                        "purpose": purpose_obj.purpose_name,
                        "features": features or purpose_obj.features  # fallback to default
                    })

            user.card_purposes = final_purpose_list
            user.save()
            
            JobProfile.objects.create(
                MbrCardNo=user,
                BasicInformation={
                    "full_name": user.full_name,
                    "mobile_number": user.mobile_number,
                    "email": user.email or ""
                }
            )
            return Response({"message": "member added successfully","member": {
                "mbrcardno": user.mbrcardno,
                "full_name": user.full_name,
                "email": user.email,
                "mobile_number": user.mobile_number,
                "address": user.address
            }}, status=status.HTTP_201_CREATED)
           
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    @swagger_auto_schema(
        responses={200: serializers.JobMitraMemberListSerializer(many=True)},
        tags=["Institute"]
    )
    def get(self, request):
        """Retrieve all referred members and return total count."""

        referal_id = request.user.business_id
        staff_users = Member.objects.filter(MbrReferalId=referal_id)
        total_students = staff_users.count()
        serializer = serializers.JobMitraMemberListSerializer(staff_users, many=True)

        return Response({
            "success": True,
            "total_students": total_students,
            "members": serializer.data
        }, status=status.HTTP_200_OK)
        
        
        


class FieldsFormattedforInstitute(APIView):
    """API to get all categories with their fields formatted as key-value pairs."""
    authentication_classes = [BusinessTokenAuthentication]
    permission_classes = [IsAuthenticated]
    # Define the response schema for Swagger
    @swagger_auto_schema(
        responses={
            200: openapi.Response(
                description="List of all categories with their fields formatted as key-value pairs.",
                examples={
                    "application/json": {
                        "BasicInformation": {
                            "first_name": {
                                "label": "First Name",
                                "field_id": "first_name",
                                "field_type": "text",
                                "is_required": True,
                                "placeholder": "Enter your first name",
                                "value": ""
                            },
                            "last_name": {
                                "label": "Last Name",
                                "field_id": "last_name",
                                "field_type": "text",
                                "is_required": False,
                                "placeholder": "Enter your last name",
                                "value": ""
                            }
                        },
                        "workexperience": {},
                        "skills": {
                            "python": {
                                "label": "Python",
                                "field_id": "python",
                                "field_type": "text",
                                "is_required": True,
                                "placeholder": "Enter your Python skills",
                                "value": ""
                            }
                        }
                    }
                },
            )
        },
        tags=["institute"]
    )
    def get(self, request, card_number):
       
        job_profile = get_object_or_404(JobProfile, MbrCardNo=card_number)

        categories = FieldCategory.objects.prefetch_related("fields").all()
        response_data = {}

        for category in categories:
            category_fields = {}

            # Normalize key from category name (e.g., "Basic Information" -> "BasicInformation")
            category_key = category.name.replace(" ", "")
            job_profile_data = getattr(job_profile, category_key, {})

            for field in category.fields.all():
                # Get raw field value from job profile data
                field_value = job_profile_data.get(field.field_id)

                # Extract only the real value if field_value is a dict
                actual_value = (
                    field_value.get("value")
                    if isinstance(field_value, dict) and "value" in field_value
                    else field_value
                )

                field_data = {
                    "label": field.label,
                    "field_id": field.field_id,
                    "field_type": field.field_type,
                    "is_required": field.is_required,
                    "placeholder": field.placeholder,
                    "option": field.option,
                    "value": actual_value if actual_value is not None else ([] if field.field_type == "checkbox" else None),
                }

                category_fields[field.field_id] = field_data

            response_data[category.name] = category_fields

      
        return Response(response_data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        request_body=JobProfileSerializer,
        tags=["institute"]
    )
    def post(self, request, card_number):
        """Create or update the job profile for the logged-in user"""
        try:
            member = Member.objects.get(mbrcardno=card_number)
        except Member.DoesNotExist:
            return Response({"error": "Invalid member."}, status=status.HTTP_400_BAD_REQUEST)

        data = request.data.copy()
        data["MbrCardNo"] = member.mbrcardno

        try:
            job_profile = JobProfile.objects.get(MbrCardNo=member)
            serializer = JobProfileSerializer(job_profile, data=data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Job Profile Updated Successfully", "data": serializer.data}, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        except JobProfile.DoesNotExist:
            serializer = JobProfileSerializer(data=data)
            if serializer.is_valid():
                serializer.save()
                return Response({"message": "Job Profile Created Successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        

class PublicMemberRegisterAPI(APIView):
    """
    Open API to register a Member using referral ID, accessible via public links.
    """

    @swagger_auto_schema(request_body=serializers.JobMitraAddMemberSerializer, tags=["Public Registration"])
    def post(self, request):
        # refer_id = request.query_params.get("referId")  # from URL like ?referId=BUS123
        
        data = request.data.copy()

       
        # Pre-check for duplicate mobile/email
        if Member.objects.filter(email=data.get("email")).exists():
            return Response({"error": "Member with this email already exists."}, status=status.HTTP_400_BAD_REQUEST)

        if Member.objects.filter(mobile_number=data.get("mobile_number")).exists():
            return Response({"error": "Member with this mobile number already exists."}, status=status.HTTP_400_BAD_REQUEST)

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
            refer_id = serializer.validated_data["MbrReferalId"]
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
                MbrReferalId=refer_id,
                address=address
            )

                # ✅ Handle multiple purpose entries
            purposes_data = request.data.get("card_purposes", [
                {"purpose": "consumer", "features": ["Reward"]}
            ])

            final_purpose_list = []

            for entry in purposes_data:
                purpose_name = entry.get("purpose", "consumer")
                features = entry.get("features", [])

                purpose_obj = CardPurpose.objects.filter(purpose_name=purpose_name).first()
                if purpose_obj:
                    final_purpose_list.append({
                        "id": purpose_obj.id,
                        "purpose": purpose_obj.purpose_name,
                        "features": features or purpose_obj.features  # fallback to default
                    })

            user.card_purposes = final_purpose_list
            user.save()
            
            JobProfile.objects.create(
                MbrCardNo=user,
                BasicInformation={
                    "full_name": user.full_name,
                    "mobile_number": user.mobile_number,
                    "email": user.email or ""
                }
            )
            new_token = secrets.token_hex(32)

            # Create or update token in DB
            token, _ = models.MemberAuthToken.objects.update_or_create(
                user=user,
                defaults={"key": new_token}
            )
            send_template_email(
                subject="Welcome to JSJCard!",
                template_name="email_template/member_welcome.html",
                context={
                    'full_name': user.full_name,
                    'mbrcardno': user.mbrcardno,
                    'email': user.email,
                    'mobile_number': user.mobile_number,
                    'card_purposes': final_purpose_list,
                    'created_at': user.MbrCreatedAt.strftime('%Y-%m-%d %H:%M:%S'),
                },
                recipient_list=[user.email]
            )
            return Response({
                "success": True,
                "message": "Member registered successfully",
                "token": token.key,
                "member": {
                "mbrcardno": user.mbrcardno,
                "full_name": user.full_name,
                "email": user.email,
                "mobile_number": user.mobile_number,
                "address": user.address
            }
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
