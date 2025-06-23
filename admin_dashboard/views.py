from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from app_common.models import Member,Business,User, BusinessKyc
from . import serializers
from admin_dashboard.models import CardPurpose, JobProfileField, FieldCategory
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


class CategoryListCreateApi(APIView):
    """List and Create Categories"""
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all categories.",
        responses={200: serializers.CategorySerializer(many=True)},
    )
    def get(self, request):
        categories = FieldCategory.objects.all()
        serializer = serializers.CategorySerializer(categories, many=True)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.CategorySerializer,
        operation_description="Create a new category.",
        responses={201: serializers.CategorySerializer()},
    )
    def post(self, request):
        # Check for duplicate category name
        if FieldCategory.objects.filter(name=request.data.get('name')).exists():
            return Response(
                {"error": "Category with this name already exists"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = serializers.CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Category created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailApi(APIView):
    """Retrieve, Update, and Delete a Category"""
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, category_id):
        try:
            return FieldCategory.objects.get(id=category_id)
        except FieldCategory.DoesNotExist:
            raise NotFound("Category not found")

    @swagger_auto_schema(
        operation_description="Retrieve a specific category by ID.",
        responses={200: serializers.CategorySerializer()},
    )
    def get(self, request, category_id):
        category = self.get_object(category_id)
        serializer = serializers.CategorySerializer(category)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.CategorySerializer,
        operation_description="Update a category by ID.",
        responses={200: serializers.CategorySerializer()},
    )
    def put(self, request, category_id):
        category = self.get_object(category_id)
        serializer = serializers.CategorySerializer(
            category, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Category updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Delete a category by ID.",
        responses={200: "Category deleted successfully"},
    )
    def delete(self, request, category_id):
        category = self.get_object(category_id)
        category.delete()
        return Response(
            {"message": "Category deleted successfully"}, status=status.HTTP_200_OK
        )





class JobProfileFieldCreateApi(APIView):
    """API to create a new dynamic field."""
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=serializers.JobProfileFieldSerializer,
        operation_description="Create a new dynamic field.",
        responses={201: serializers.JobProfileFieldSerializer()},
    )
    def post(self, request):
        serializer = serializers.JobProfileFieldSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Field created successfully", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class JobProfileFieldListApi(APIView):
    """API to list all dynamic fields grouped by category."""
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_description="List all dynamic fields grouped by category.",
        responses={200: "Grouped dynamic fields by category"}
    )
    def get(self, request):
        fields = JobProfileField.objects.all()
        serializer = serializers.JobProfileFieldSerializer(fields, many=True)

        # Grouping logic
        grouped_fields = defaultdict(list)
        for field in serializer.data:
            key = (field["category_name"], field["category"])
            grouped_fields[key].append({
                "label": field["label"],
                "field_id": field["field_id"],
                "field_type": field["field_type"],
                "is_required": field["is_required"],
                "placeholder": field["placeholder"],
                "value": field.get("value", ""),
                "option": field.get("option", []) if field["field_type"] == "select" else []
            })

        # Prepare final structured response
        response_data = []
        for (category_name, category_id), fields_list in grouped_fields.items():
            response_data.append({
                "category_name": category_name,
                "category": category_id,
                "fields": fields_list
            })

        return Response(response_data, status=status.HTTP_200_OK)


class JobProfileFieldDetailApi(APIView):
    """API to retrieve, update or delete a specific field."""
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, id):
        try:
            return JobProfileField.objects.get(id=id)
        except JobProfileField.DoesNotExist:
            raise NotFound("Field not found")

    @swagger_auto_schema(
        operation_description="Retrieve a specific field by ID.",
        responses={200: serializers.JobProfileFieldSerializer()},
    )
    def get(self, request, id):
        field = self.get_object(id)
        serializer = serializers.JobProfileFieldSerializer(field)
        return Response({"data": serializer.data}, status=status.HTTP_200_OK)

    @swagger_auto_schema(
        request_body=serializers.JobProfileFieldSerializer,
        operation_description="Update a field by ID.",
        responses={200: serializers.JobProfileFieldSerializer()},
    )
    def put(self, request, id):
        field = self.get_object(id)
        serializer = serializers.JobProfileFieldSerializer(
            field, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Field updated successfully", "data": serializer.data},
                status=status.HTTP_200_OK,
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    @swagger_auto_schema(
        operation_description="Delete a field by ID.",
        responses={200: "Field deleted successfully"},
    )
    def delete(self, request, id):
        field = self.get_object(id)
        field.delete()
        return Response(
            {"message": "Field deleted successfully"}, status=status.HTTP_200_OK
        )
            
            
            
            
class JobProfileFieldListByCategory(APIView):
    authentication_classes = [UserTokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Get list of job profile fields for a specific category (grouped by category name)",
        manual_parameters=[
            openapi.Parameter(
                'category_id',
                openapi.IN_QUERY,
                description="ID of the category",
                type=openapi.TYPE_INTEGER,
                required=True
            )
        ],
        responses={
            200: openapi.Response(
                description="Fields grouped by category name",
                examples={
                    "application/json": {
                        "status": True,
                        "basicInformation": [
                            {
                                "id": 6,
                                "option": [],
                                "label": "full name",
                                "field_id": "full_name",
                                "field_type": "text",
                                "is_required": True,
                                "placeholder": "Enter your Full Name",
                                "value": ""
                            },
                            {
                                "id": 7,
                                "option": [],
                                "label": "gender",
                                "field_id": "gender",
                                "field_type": "text",
                                "is_required": True,
                                "placeholder": "Enter your gender",
                                "value": ""
                            }
                        ]
                    }
                }
            )
        }
    )
    def get(self, request):
        category_id = request.query_params.get("category_id")
        if not category_id:
            return Response({
                "status": False,
                "message": "category_id is required"
            }, status=200)

        fields = JobProfileField.objects.filter(category_id=category_id)
        if not fields.exists():
            return Response({
                "status": False,
                "message": "No fields found for this category"
            }, status=200)

        serialized_fields = serializers.JobProfileFieldSerializer(fields, many=True).data
        for item in serialized_fields:
            item.pop("category", None)
            item.pop("category_name", None)

        return Response({
            "status": True,
            "data": serialized_fields
        })

    @swagger_auto_schema(
        operation_description="Create or update a job profile field. Pass 'id' to update, omit 'id' to create.",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                
                'category': openapi.Schema(type=openapi.TYPE_INTEGER, description='Category ID'),
                'label': openapi.Schema(type=openapi.TYPE_STRING, description='Label'),
                'field_id': openapi.Schema(type=openapi.TYPE_STRING, description='Field ID'),
                'field_type': openapi.Schema(type=openapi.TYPE_STRING, description='Field Type'),
                'placeholder': openapi.Schema(type=openapi.TYPE_STRING, description='Placeholder text'),
                'is_required': openapi.Schema(type=openapi.TYPE_BOOLEAN, description='Is required'),
                'value': openapi.Schema(type=openapi.TYPE_STRING, description='Default value'),
                'option': openapi.Schema(
                    type=openapi.TYPE_ARRAY,
                    items=openapi.Items(type=openapi.TYPE_STRING),
                    description='Options (for select fields)'
                )
            }
        ),
        responses={
            200: openapi.Response(description="Field created or updated successfully")
        }
    )
    def post(self, request):
        data = request.data

        # Check if the input is a list (bulk) or dict (single)
        fields_data = data if isinstance(data, list) else [data]

        response_fields = []

        for field_data in fields_data:
            field_id_value = field_data.get("field_id")
            print("field_id_value",field_id_value,"----------")
            if field_id_value:
                try:
                    field = JobProfileField.objects.get(field_id=field_id_value)
                    serializer = serializers.JobProfileFieldSerializer(field, data=field_data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        response_fields.append({
                            "status": True,
                            "message": f"Field '{field_id_value}' updated successfully",
                            "field": serializer.data
                        })
                        continue
                    else:
                        response_fields.append({
                            "status": False,
                            "message": f"Validation failed for '{field_id_value}'",
                            "errors": serializer.errors
                        })
                        continue
                except JobProfileField.DoesNotExist:
                    pass  # Not found, will create below

            # Create new field if not found
            serializer = serializers.JobProfileFieldSerializer(data=field_data)
            if serializer.is_valid():
                serializer.save()
                response_fields.append({
                    "status": True,
                    "message": f"Field '{field_data.get('field_id')}' created successfully",
                    "field": serializer.data
                })
            else:
                response_fields.append({
                    "status": False,
                    "message": f"Validation failed for '{field_data.get('field_id')}'",
                    "errors": serializer.errors
                })

        return Response({
            "status": True,
            "results": response_fields
        }, status=status.HTTP_200_OK)