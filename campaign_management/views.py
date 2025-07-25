from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_common.authentication import UserTokenAuthentication
from .models import Template, Group, Campaign, MessageStatus
from .serializers import TemplateSerializer, GroupSerializer, CampaignSerializer, MessageStatusSerializer
from django.shortcuts import get_object_or_404
from app_common.models import Member, Business
import time
from app_common.email import send_template_email

class TemplateAPIView(APIView):
    
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve all templates (Email, SMS, WhatsApp)",
        responses={200: TemplateSerializer(many=True)},
        tags=["campaign_management"]
    )
    def get(self, request):
        try:
            templates = Template.objects.all().order_by('-created_at')
            serializer = TemplateSerializer(templates, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Create a new template",
        request_body=TemplateSerializer,
        responses={
            201: openapi.Response("Template created successfully", TemplateSerializer),
            400: "Bad Request",
        },
        tags=["campaign_management"]
    )
    def post(self, request):
        serializer = TemplateSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    
class GroupAPIView(APIView):
    """
    Handles creation and listing of groups with combined business & member contacts.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get all groups",
        responses={200: GroupSerializer(many=True)},
        tags=["campaign_management"]
    )
    def get(self, request):
        try:
            groups = Group.objects.all().order_by("-created_at")
            serializer = GroupSerializer(groups, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Create a new group with all member and business contacts.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING),
                "description": openapi.Schema(type=openapi.TYPE_STRING),
                "tags": openapi.Schema(type=openapi.TYPE_STRING),
                "company": openapi.Schema(type=openapi.TYPE_STRING),
                "email": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of email addresses"),
                "mobile_number": openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description="List of mobile numbers"),
            },
        ),
        responses={201: openapi.Response("Created", GroupSerializer)},
        tags=["campaign_management"]
    )
    def post(self, request):
        data = request.data.copy()
        
        # --- 1. Handle optional manual emails/mobiles ---
        input_emails = data.get("email", [])
        input_mobiles = data.get("mobile_number", [])

        # If single string provided, convert to list
        if isinstance(input_emails, str):
            input_emails = [input_emails]
        if isinstance(input_mobiles, str):
            input_mobiles = [input_mobiles]

        business_emails = list(Business.objects.exclude(email__isnull=True).exclude(email__exact='').values_list('email', flat=True))
        business_mobiles = list(Business.objects.exclude(mobile_number__isnull=True).exclude(mobile_number__exact='').values_list('mobile_number', flat=True))

        member_emails = list(Member.objects.exclude(email__isnull=True).exclude(email__exact='').values_list('email', flat=True))
        member_mobiles = list(Member.objects.exclude(mobile_number__isnull=True).exclude(mobile_number__exact='').values_list('mobile_number', flat=True))

        all_emails = list(set(business_emails + member_emails))
        all_mobiles = list(set(business_mobiles + member_mobiles))

        data["email"] = all_emails
        data["mobile_number"] = all_mobiles

        serializer = GroupSerializer(data=data)
        if serializer.is_valid():
            group = serializer.save()
            return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)





class CampaignAPIView(APIView):
    """
    Handles listing and creation of campaigns (Email, SMS, WhatsApp).
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get all campaigns",
        responses={200: CampaignSerializer(many=True)},
        tags=["campaign_management"]
    )
    def get(self, request):
        try:
            campaigns = Campaign.objects.all().order_by('-created_at')
            serializer = CampaignSerializer(campaigns, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Create a new campaign",
        request_body=CampaignSerializer,
        responses={
            201: openapi.Response("Campaign created", CampaignSerializer),
            400: "Bad Request"
        },
        tags=["campaign_management"]
    )
    def post(self, request):
        serializer = CampaignSerializer(data=request.data)
        if serializer.is_valid():
            try:
                campaign = serializer.save()

                if campaign.type == "Email" and campaign.delivery_option == "Send Now":
                    for group in campaign.groups.all():
                        for email in group.email:
                            context = {
                                "full_name": "",  # Add dynamic values if available
                                "email": email,
                                "mobile_number": "",  # Add dynamic values if needed
                            }
                            try:
                                send_template_email(
                                    subject=campaign.subject or "JSJ Card Campaign",
                                    template_name="email_template/email_campaign.html",
                                    context=context,
                                    recipient_list=[email]
                                )
                                print(f"✅ Email sent successfully to: {email}")
                            except Exception as e:
                                print(f"❌ Failed to send email to {email}: {str(e)}")

                            time.sleep(1)  # Optional: Prevent AWS SES rate limit errors

                return Response(CampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class CampaignStatusAPIView(APIView):
    """
    Get all message delivery statuses for a specific campaign.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Get all message delivery statuses for a campaign",
        responses={200: MessageStatusSerializer(many=True)},
        tags=["campaign_management"]
    )
    def get(self, request, campaign_id):
        try:
            campaign = get_object_or_404(Campaign, id=campaign_id)
            statuses = MessageStatus.objects.filter(campaign=campaign).order_by('-timestamp')
            serializer = MessageStatusSerializer(statuses, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": f"Internal Server Error: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


