from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail

from app_common.models import Business, User, Member
from member.models import JobProfile
from .serializers import  JobProfileSerializer
from app_common.authentication import MemberTokenAuthentication
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from admin_dashboard.models import FieldCategory

from django.utils import timezone
from django.db.models import Q


# class RemoteJobprofileOfMember(APIView):
#     """API to get all categories with their fields formatted as key-value pairs."""
#     # authentication_classes = [MemberTokenAuthentication]
#     # permission_classes = [IsAuthenticated]
#     @swagger_auto_schema(
#         responses={200: JobProfileSerializer()},
#         tags=["Job Profile Management"]
#     )
#     def get(self, request):
#         """Retrieve the logged-in user's job profile"""
#         card_number = request.query_params.get('card_number', None)
        
#         try:
           
           
#             job_profile = JobProfile.objects.get(MbrCardNo=card_number)
           
#             serializer = JobProfileSerializer(job_profile)
#             response_data = serializer.data
#             # response_data["full_name"] = request.user.full_name
#             # response_data["mbrcardno"] = request.user.mbrcardno
#             # response_data["mobile_no"] = request.user.mobile_number
#             # response_data["email"] = request.user.email

#             return Response(response_data, status=status.HTTP_200_OK)

#         except Member.DoesNotExist:
#             return Response({"error": "Member not found."}, status=status.HTTP_400_BAD_REQUEST)

#         except JobProfile.DoesNotExist:
#             return Response({"error": "Job Profile Not Found"}, status=status.HTTP_404_NOT_FOUND)




class JobProfileAPI(APIView):
    authentication_classes = [MemberTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        responses={200: JobProfileSerializer()},
        tags=["Job Profile Management"]
    )
    def get(self, request):
        """Retrieve the logged-in user's job profile"""
        try:
           
            member = Member.objects.get(mbrcardno=getattr(request.user, 'mbrcardno', None))
            job_profile = JobProfile.objects.get(MbrCardNo=member)
           
            serializer = JobProfileSerializer(job_profile)
            response_data = serializer.data
            response_data["full_name"] = request.user.full_name
            response_data["MbrCardNo"] = request.user.mbrcardno
            response_data["mobile_no"] = request.user.mobile_number
            response_data["email"] = request.user.email

            return Response(response_data, status=status.HTTP_200_OK)

        except Member.DoesNotExist:
            return Response({"error": "Member not found."}, status=status.HTTP_400_BAD_REQUEST)

        except JobProfile.DoesNotExist:
            return Response({"error": "Job Profile Not Found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=JobProfileSerializer,
        tags=["Job Profile Management"]
    )
    def post(self, request):
        """Create or update the job profile for the logged-in user"""
        try:
            member = Member.objects.get(mbrcardno=getattr(request.user, 'mbrcardno', None))
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
        
        
        


class CategoryFieldsFormattedApi(APIView):
    """API to get all categories with their fields formatted as key-value pairs."""
    authentication_classes = [MemberTokenAuthentication]
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
        tags=["Job Profile Management"]
    )
    def get(self, request):
        if not hasattr(request.user, 'mbrcardno'):
            return Response({"error": "User MbrCardNo not found"}, status=status.HTTP_400_BAD_REQUEST)

        job_profile = get_object_or_404(JobProfile, MbrCardNo=request.user.mbrcardno)

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

        # Add EventRegistered field (True/False)
        response_data["EventRegistered"] = job_profile.EventRegistered if hasattr(job_profile, 'EventRegistered') else False

        return Response(response_data, status=status.HTTP_200_OK)