from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

from app_common.models import Member, Business
from .models import LeadFollowUp
from .serializers import LeadFollowUpSerializer
from app_common.authentication import UserTokenAuthentication
from rest_framework.permissions import IsAuthenticated


class LeadFollowUpView(APIView):
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get all lead follow-ups",
        manual_parameters=[
            openapi.Parameter(
                'lead_type',
                openapi.IN_QUERY,
                description="Filter by lead type (member, institute, business)",
                type=openapi.TYPE_STRING
            )
        ],
        responses={200: LeadFollowUpSerializer(many=True)}
    )
    def get(self, request):
        """Get all lead follow-ups or filter by lead_type"""
        lead_type = request.query_params.get("lead_type")  # e.g., ?lead_type=business

        followups = LeadFollowUp.objects.all().order_by('-created_at')

        if lead_type:
            followups = followups.filter(lead_type=lead_type)

        serializer = LeadFollowUpSerializer(followups, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Create a new lead follow-up",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["lead_type", "status", "comment"],
            properties={
                'lead_type': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["member", "institute", "business"],
                    description="Type of lead (member, institute, business)"
                ),
                'mbrcardno': openapi.Schema(
                    type=openapi.TYPE_INTEGER,
                    description="Member card number (required if lead_type=member)"
                ),
                'business_id': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Business ID (required if lead_type=business or institute)"
                ),
                'status': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["hot", "cold", "neutral"],
                    description="Lead status"
                ),
                'comment': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description="Initial comment"
                ),
            }
        ),
        responses={
            201: LeadFollowUpSerializer(),
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Create new lead follow-up"""
        lead_type = request.data.get("lead_type")
        mbrcardno = request.data.get("mbrcardno")
        business_id = request.data.get("business_id")
        status_value = request.data.get("status")
        comment_text = request.data.get("comment")

        if not lead_type or not status_value or not comment_text:
            return Response({"error": "lead_type, status, and comment are required"},
                            status=status.HTTP_400_BAD_REQUEST)

        # Validate lead type
        if lead_type not in ["member", "institute", "business"]:
            return Response({"error": "Invalid lead_type"}, status=status.HTTP_400_BAD_REQUEST)

        member = None
        business = None

        if lead_type == "member":
            if not mbrcardno:
                return Response({"error": "mbrcardno is required for member leads"},
                                status=status.HTTP_400_BAD_REQUEST)
            member = get_object_or_404(Member, mbrcardno=mbrcardno)

        elif lead_type in ["business", "institute"]:
            if not business_id:
                return Response({"error": "business_id is required for business or institute leads"},
                                status=status.HTTP_400_BAD_REQUEST)
            business = get_object_or_404(Business, business_id=business_id)

        # Create lead follow-up
        followup = LeadFollowUp.objects.create(
            lead_type=lead_type,
            member=member,
            business=business,
            status=status_value,
            comments=[{
                "text": comment_text,
                "added_by": str(request.user),
                "added_at": timezone.now().isoformat()
            }],
            created_by=request.user
        )

        serializer = LeadFollowUpSerializer(followup)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class LeadFollowUpCommentAppendView(APIView):
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get all comments for a lead follow-up",
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Lead follow-up ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        responses={
            200: openapi.Response(
                description="List of comments",
                examples={
                    "application/json": [
                        {
                            "text": "Followed up with client",
                            "added_by": "staff1",
                            "added_at": "2025-08-06T12:45:32.000Z"
                        }
                    ]
                }
            ),
            404: "Not Found"
        }
    )
    def get(self, request, pk):
        """Get all comments for a specific follow-up"""
        followup = get_object_or_404(LeadFollowUp, pk=pk)
        return Response({
            "lead_id": pk,
            "comments": followup.comments
        }, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_summary="Append a comment to an existing lead follow-up",
        manual_parameters=[
            openapi.Parameter(
                'pk', openapi.IN_PATH,
                description="Lead follow-up ID",
                type=openapi.TYPE_INTEGER
            )
        ],
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=["comment"],
            properties={
                'comment': openapi.Schema(type=openapi.TYPE_STRING, description="Comment text")
            }
        ),
        responses={
            200: openapi.Response(description="Comment added successfully"),
            400: "Bad Request",
            404: "Not Found"
        }
    )
    def post(self, request, pk):
        """Append comment to an existing follow-up"""
        followup = get_object_or_404(LeadFollowUp, pk=pk)
        comment_text = request.data.get("comment")

        if not comment_text:
            return Response({"error": "Comment is required"}, status=status.HTTP_400_BAD_REQUEST)

        followup.append_comment(comment_text, request.user)
        return Response({
            "message": "Comment added successfully",
            "comments": followup.comments
        }, status=status.HTTP_200_OK)
