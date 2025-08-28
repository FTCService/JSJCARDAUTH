from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_common.authentication import UserTokenAuthentication
from .models import Template, Group, Campaign
from .serializers import TemplateSerializer, GroupSerializer, CampaignSerializer
from django.shortcuts import get_object_or_404
from app_common.models import Member, Business, User
from django.utils import timezone
#from .tasks import schedule_campaign_send  # ✅ Required for scheduling
from app_common.email import send_template_email
from helpers.utils import send_fast2sms

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
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all groups with summary statistics",
        responses={200: GroupSerializer(many=True)},
        tags=["campaign_management"]
    )
    def get(self, request):
        try:
            groups = Group.objects.all().order_by("-created_at")
            serializer = GroupSerializer(groups, many=True)

            # 📌 Total contacts = sum of all mobile_number lists
            total_contacts = sum(len(group.mobile_number) for group in groups)

            # 📌 Active groups = groups that have at least 1 contact
            active_groups = sum(1 for group in groups if len(group.mobile_number) > 0)

            # 📌 Total groups
            total_groups = groups.count()

            # 📌 Growth rate (Example: Active groups / Total groups * 100)
            growth_rate = 0
            if total_groups > 0:
                growth_rate = round((active_groups / total_groups) * 100, 2)

            response_data = {
                "summary": {
                    "total_contacts": total_contacts,
                    "active_groups": active_groups,
                    "total_groups": total_groups,
                    "growth_rate": f"{growth_rate}%",
                },
                "data": serializer.data
            }

            return Response(response_data, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Create a new group",
        request_body=GroupSerializer,
        responses={201: GroupSerializer()},
        tags=["campaign_management"]
    )
    def post(self, request):
        serializer = GroupSerializer(data=request.data)
        if serializer.is_valid():
            group = serializer.save()   # saves name, group_type, description, etc.
            
            # overwrite email and mobile_number explicitly
            data = request.data
            if "email" in data:
                group.email = data["email"]
            if "mobile_number" in data:
                group.mobile_number = data["mobile_number"]

            group.save(update_fields=["email", "mobile_number"])
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
        operation_description="Create a new campaign and send/schedule it",
        request_body=CampaignSerializer,
        responses={201: CampaignSerializer()},
        tags=["campaign_management"]
    )
    def post(self, request):
        serializer = CampaignSerializer(data=request.data)
        if serializer.is_valid():
            try:
                campaign = serializer.save()

                # Collect recipients (from attached groups)
                recipients_emails = []
                recipients_mobiles = []
                for group in campaign.groups.all():
                    recipients_emails.extend(group.email)
                    recipients_mobiles.extend(group.mobile_number)

                # Remove duplicates
                recipients_emails = list(set(recipients_emails))
                recipients_mobiles = list(set(recipients_mobiles))

                # If delivery_option = Send Now, trigger immediately
                if campaign.delivery_option == "Send Now":
                    if campaign.type == "Email":
                        subject = campaign.subject or (campaign.template.subject if campaign.template else "")
                        content = campaign.content or (campaign.template.content if campaign.template else "")

                        for email in recipients_emails:
                            send_template_email(
                                subject=subject,
                                template_name="email_template/member_welcome.html",  # or dynamic if you support multiple
                                context={
                                    "full_name": "User",   # update with real data if needed
                                    "email": email,
                                },
                                recipient_list=[email]
                            )

                    elif campaign.type == "SMS":
                        message = campaign.content or (campaign.template.content if campaign.template else "")
                        for mobile in recipients_mobiles:
                            send_fast2sms(mobile, message)

                    elif campaign.type == "WhatsApp":
                        # 👉 Placeholder: integrate WhatsApp provider API
                        pass

                # If Schedule, you’d push to Celery or cron job
                # else:
                #     schedule_campaign_send.apply_async((campaign.id,), eta=campaign.scheduled_time)

                return Response(CampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
