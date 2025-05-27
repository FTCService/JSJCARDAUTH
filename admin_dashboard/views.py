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




class MemberListApi(APIView):
    """
    API to list all registered members.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all registered members.",
        responses={200: serializers.MemberSerializer(many=True)}
    )
    def get(self, request):
        members = Member.objects.all()
        serializer = serializers.MemberSerializer(members, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
class MemberDetailApi(APIView):
    """
    API to retrieve a specific member by their primary key (ID).
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific member.",
        responses={200: serializers.MemberSerializer()}
    )
    def get(self, request, pk):
       
        """
        Retrieve a member by their primary key (ID).
        """
        try:
            member = Member.objects.get(pk=pk)
            serializer = serializers.MemberSerializer(member)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Member.DoesNotExist:
            return Response({"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND)
        
    @swagger_auto_schema(
        operation_description="Update the details of a specific member.",
        request_body=serializers.MemberSerializer(),
        responses={200: serializers.MemberSerializer(), 400: "Bad request"}
    )
    def put(self, request, pk):
        """
        Update a member by their primary key (ID).
        """
        try:
            member = Member.objects.get(pk=pk)
        except Member.DoesNotExist:
            return Response({"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND)

        # Deserialize the request data into the Member model instance
        serializer = serializers.MemberSerializer(member, data=request.data, partial=False)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a specific member.",
        responses={204: "No content", 404: "Not found"}
    )
    def delete(self, request, pk):
        """
        Delete a member by their primary key (ID).
        """
        try:
            member = Member.objects.get(pk=pk)
            member.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Member.DoesNotExist:
            return Response({"error": "Member not found"}, status=status.HTTP_404_NOT_FOUND)



### ✅ BUSINESS LIST API ###
class BusinessListApi(APIView):
    """
    API to list all registered businesses.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all registered businesses.",
        responses={200: serializers.BusinessSerializer(many=True)}
    )
    def get(self, request):
        businesses = Business.objects.all()
        
        serializer = serializers.BusinessSerializer(businesses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
class AdminDashboard(APIView):
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

    
    
    
    
class BusinessDetailsApi(APIView):
    """
    API to retrieve, update, or delete a specific business.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific business by ID.",
        responses={200: serializers.BusinessSerializer()},
    )
    def get(self, request, id):
        try:
            business = Business.objects.get(id=id)
            serializer = serializers.BusinessSerializer(business)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Business.DoesNotExist:
            return Response({"detail": "Business not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        operation_description="Update details of a specific business by ID.",
        responses={200: serializers.BusinessSerializer()},
        request_body=serializers.BusinessSerializer,
    )
    def put(self, request, id):
        try:
            business = Business.objects.get(id=id)
        except Business.DoesNotExist:
            return Response({"detail": "Business not found"}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.BusinessSerializer(business, data=request.data, partial=True)  # Allow partial updates
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a specific business by ID.",
        responses={204: "Business deleted successfully."}
    )
    def delete(self, request, id):
        try:
            business = Business.objects.get(id=id)
            business.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Business.DoesNotExist:
            return Response({"detail": "Business not found"}, status=status.HTTP_404_NOT_FOUND)
        
        
        
class VerifyBusinessKycApi(APIView):
    """
    API to verify Business KYC (Admin/Staff Only).
    """
    authentication_classes = [UserTokenAuthentication]  
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.VerifyKycSerializer,
        operation_description="Verify Business KYC (Admin & Staff Only).",
        responses={200: "KYC Verified Successfully."}
    )
    def post(self, request, business_id):
        """
        Verify Business KYC.
        """
        user = request.user

        # ✅ Only Admin or Staff can verify KYC
        if not (user.is_staff or user.is_superuser):
            return Response({"error": "Only Admin or Staff can verify KYC."}, status=status.HTTP_403_FORBIDDEN)

        try:
            kyc_instance = BusinessKyc.objects.get(business_id=business_id)
        except BusinessKyc.DoesNotExist:
            return Response({"error": "KYC record not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = serializers.VerifyKycSerializer(kyc_instance, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "KYC Verified Successfully."}, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

        

class CardPurposeListApi(APIView):
    """
    API to list all card purposes.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve a list of all card purposes.",
        responses={200: serializers.CardPurposeSerializer(many=True)}
    )
    def get(self, request):
        card_purposes = CardPurpose.objects.all()
        serializer = serializers.CardPurposeSerializer(card_purposes, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CardPurposeCreateApi(APIView):
    """
    API to create a new card purpose.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.CardPurposeSerializer,
        operation_description="Create a new card purpose.",
        responses={201: serializers.CardPurposeSerializer()}
    )
    def post(self, request):
        serializer = serializers.CardPurposeSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Card purpose created successfully", "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CardPurposeDetailApi(APIView):
    """
    API to retrieve, update, or delete a specific card purpose.
    """
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Retrieve details of a specific card purpose.",
        responses={200: serializers.CardPurposeSerializer()}
    )
    def get(self, request, pk):
        """
        Retrieve a card purpose by its primary key.
        """
        try:
            card_purpose = CardPurpose.objects.get(pk=pk)
            serializer = serializers.CardPurposeSerializer(card_purpose)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except CardPurpose.DoesNotExist:
            return Response({"error": "Card purpose not found"}, status=status.HTTP_404_NOT_FOUND)

    @swagger_auto_schema(
        request_body=serializers.CardPurposeSerializer,
        operation_description="Update an existing card purpose (append new features, do not overwrite).",
        responses={200: serializers.CardPurposeSerializer()}
    )
    def put(self, request, pk):
        """
        Update a card purpose, appending new features instead of overwriting existing ones.
        """
        try:
            card_purpose = CardPurpose.objects.get(pk=pk)
        except CardPurpose.DoesNotExist:
            return Response({"error": "Card purpose not found"}, status=status.HTTP_404_NOT_FOUND)

        existing_features = set(card_purpose.features)  # Convert existing features to a set
        new_features = request.data.get("features", [])  # Get new features from request

        if not isinstance(new_features, list):
            return Response({"error": "Features must be a list of strings."}, status=status.HTTP_400_BAD_REQUEST)

        updated_features = list(existing_features.union(new_features))  # Append only unique features
        request.data["features"] = updated_features  # Update request data

        serializer = serializers.CardPurposeSerializer(card_purpose, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Card purpose updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a specific card purpose.",
        responses={204: "Deleted successfully"}
    )
    def delete(self, request, pk):
        """
        Delete a specific card purpose.
        """
        try:
            card_purpose = CardPurpose.objects.get(pk=pk)
            card_purpose.delete()
            return Response({"message": "Card purpose deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except CardPurpose.DoesNotExist:
            return Response({"error": "Card purpose not found"}, status=status.HTTP_404_NOT_FOUND)
        
        


class PhysicalCardsListByBusiness(APIView):

    @swagger_auto_schema(
        operation_description="Get all physical cards",
        responses={200: serializers.PhysicalCardSerializer(many=True)},tags=['physical card']
    )
    def get(self, request, business_id):
        cards = PhysicalCard.objects.filter(business_id=business_id)
        serializer = serializers.PhysicalCardSerializer(cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    


class GeneratePhysicalCardsView(APIView):

    @swagger_auto_schema(
        operation_description="Get all physical cards",
        responses={200: serializers.PhysicalCardSerializer(many=True)},tags=['physical card']
    )
    def get(self, request):
        cards = PhysicalCard.objects.all()
        serializer = serializers.PhysicalCardSerializer(cards, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        operation_description="Generate unique 16-digit physical cards for a selected business.",
        request_body=serializers.GenerateCardSerializer,
        responses={201: serializers.PhysicalCardSerializer(many=True)},tags=['physical card']
    )
    def post(self, request):
        # try:
        number_of_cards = int(request.data.get('count'))
        business_id = request.data.get('business_id')

        if not number_of_cards or not business_id:
            return Response({'error': 'count and business_id are required'}, status=status.HTTP_400_BAD_REQUEST)

        business = Business.objects.get(business_id=business_id)

        # ✅ Fetch used card numbers from both Member and PhysicalCard tables
        physical_card_numbers = PhysicalCard.objects.values_list('card_number', flat=True)
        member_card_numbers = Member.objects.values_list('mbrcardno', flat=True)
        used_card_numbers = set(physical_card_numbers).union(set(member_card_numbers))

        new_cards = []
        attempts = 0

        while len(new_cards) < number_of_cards and attempts < number_of_cards * 10:
            card_number = random.randint(10**15, 10**16 - 1)
            if card_number not in used_card_numbers:
                new_cards.append(PhysicalCard(card_number=card_number, business=business))
                used_card_numbers.add(card_number)
            attempts += 1

        if not new_cards:
            return Response({'error': 'Could not generate unique card numbers. Try again.'},
                            status=status.HTTP_400_BAD_REQUEST)

        PhysicalCard.objects.bulk_create(new_cards)
        serializer = serializers.PhysicalCardSerializer(new_cards, many=True)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

        # except Business.DoesNotExist:
        #     return Response({'error': 'Business not found'}, status=status.HTTP_404_NOT_FOUND)
        # except Exception as e:
        #     return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

