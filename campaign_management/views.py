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
from .models import CustomerHelpTicket
from .serializers import CustomerSupportRequestSerializer

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
        operation_description="List all groups",
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
        operation_description="Create a group by selecting a group_type (business, member, staff, all).",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["name", "group_type"],
            properties={
                "name": openapi.Schema(type=openapi.TYPE_STRING),
                "group_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["business", "member", "staff", "all"]
                ),
                "description": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={201: openapi.Response("Created", GroupSerializer)},
        tags=["campaign_management"]
    )
    def post(self, request):
        data = request.data.copy()
        group_type = data.get("group_type")

        if group_type not in ["business", "member", "staff", "all"]:
            return Response(
                {"error": "Invalid group_type. Must be one of: business, member, staff, all."},
                status=status.HTTP_400_BAD_REQUEST
            )

        emails = []
        mobiles = []

        if group_type in ["business", "all"]:
            emails += list(Business.objects.exclude(email__isnull=True).exclude(email__exact='').values_list('email', flat=True))
            mobiles += list(Business.objects.exclude(mobile_number__isnull=True).exclude(mobile_number__exact='').values_list('mobile_number', flat=True))

        if group_type in ["member", "all"]:
            emails += list(Member.objects.exclude(email__isnull=True).exclude(email__exact='').values_list('email', flat=True))
            mobiles += list(Member.objects.exclude(mobile_number__isnull=True).exclude(mobile_number__exact='').values_list('mobile_number', flat=True))

        if group_type in ["staff", "all"]:
            emails += list(User.objects.exclude(email__isnull=True).exclude(email__exact='').values_list('email', flat=True))
            # Remove this line if User doesn't have mobile_number
            if hasattr(User, 'mobile_number'):
                mobiles += list(User.objects.exclude(mobile_number__isnull=True).exclude(mobile_number__exact='').values_list('mobile_number', flat=True))

        data["email"] = list(set(emails))
        data["mobile_number"] = list(set(mobiles))

        serializer = GroupSerializer(data=data)
        if serializer.is_valid():
            group = serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
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
                content = campaign.content or (campaign.template.content if campaign.template else "")
                
                if campaign.delivery_option == "Send Now":
                    for group in campaign.groups.all():
                        contacts = getattr(group, "contacts", None)
                        if not contacts:
                            continue

                        for contact in contacts.all():
                            if campaign.type == "Email":
                                context = {
                                    "full_name": contact.name or "",
                                    "email": contact.email,
                                    "mobile_number": contact.phone or "",
                                }
                                try:
                                    send_template_email(
                                        subject=campaign.subject or "JSJ Card Campaign",
                                        template_name="email_template/email_campaign.html",
                                        context=context,
                                        recipient_list=[contact.email]
                                    )
                                    print(f"✅ Email sent to {contact.email}")
                                except Exception as e:
                                    print(f"❌ Email failed to {contact.email}: {e}")
                                time.sleep(1)

                            elif campaign.type == "SMS":
                                try:
                                    send_fast2sms(contact.phone, content)
                                    print(f"✅ SMS sent to {contact.phone}")
                                except Exception as e:
                                    print(f"❌ SMS failed to {contact.phone}: {e}")
                                time.sleep(1)

                elif campaign.delivery_option == "Schedule":
                    if campaign.scheduled_time and campaign.scheduled_time > timezone.now():
                        schedule_campaign_send.apply_async(args=[campaign.id], eta=campaign.scheduled_time)

                return Response(CampaignSerializer(campaign).data, status=status.HTTP_201_CREATED)

            except Exception as e:
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class CustomerSupportRequestAPIView(APIView):
    """
    API to list all customer support requests or submit a new one.
    """
    

    @swagger_auto_schema(
        operation_description="Retrieve a list of all customer support requests.",
        responses={200: CustomerSupportRequestSerializer(many=True)},
        tags=["Customer Support"]
    )
    def get(self, request):
        try:
            requests = CustomerHelpTicket.objects.all().order_by('-created_at')
            serializer = CustomerSupportRequestSerializer(requests, many=True)
            return Response({
                "success": True,
                "message": "Support requests retrieved successfully.",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @swagger_auto_schema(
        operation_description="Submit a new customer support request.",
        request_body=CustomerSupportRequestSerializer,
        responses={201: CustomerSupportRequestSerializer},
        tags=["Customer Support"]
    )
    def post(self, request):
        try:
            serializer = CustomerSupportRequestSerializer(data=request.data)
            if serializer.is_valid():
                support_request = serializer.save()

                # Prepare email context
                context = {
                    "full_name": support_request.full_name,
                    "email": support_request.email,
                    "phone_number": support_request.phone_number,
                    "message": support_request.message
                }

                # Send email to support team
                send_template_email(
                    subject="New Customer Support Request",
                    template_name="email_template/from.html",
                    context=context,
                    recipient_list=["support_team@example.com"]  # update with your email
                )

                return Response({
                    "success": True,
                    "message": "Support request submitted successfully.",
                    "data": serializer.data
                }, status=status.HTTP_201_CREATED)
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
