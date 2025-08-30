from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from ..models import Business, TempBusinessUser, BusinessKyc
from ..serializers import (
    BusinessSerializer, 
    TempBusinessUserSerializer,
    BusinessKycSerializer
)
from ..services import BusinessService
from ..authentication import BusinessAuthentication


class BusinessRegistrationView(APIView):
    """View for business registration - Step 1: Send OTP"""
    
    def post(self, request):
        try:
            serializer = TempBusinessUserSerializer(data=request.data)
            if serializer.is_valid():
                temp_business, otp = BusinessService.create_temp_business(
                    business_name=serializer.validated_data['business_name'],
                    email=serializer.validated_data.get('email'),
                    mobile_number=serializer.validated_data['mobile_number'],
                    pin=request.data.get('pin'),
                    is_institute=serializer.validated_data.get('is_institute', False)
                )
                
                # TODO: Send OTP via SMS/Email service
                
                return Response({
                    'message': 'OTP sent successfully',
                    'mobile_number': temp_business.mobile_number,
                    'otp': otp  # Remove this in production
                }, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BusinessOTPVerificationView(APIView):
    """View for business registration - Step 2: Verify OTP and create business"""
    
    def post(self, request):
        try:
            mobile_number = request.data.get('mobile_number')
            otp = request.data.get('otp')
            
            if not mobile_number or not otp:
                return Response({
                    'error': 'Mobile number and OTP are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            business = BusinessService.verify_otp_and_create_business(mobile_number, otp)
            serializer = BusinessSerializer(business)
            
            return Response({
                'message': 'Business created successfully',
                'business': serializer.data
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BusinessLoginView(APIView):
    """View for business login"""
    
    def post(self, request):
        try:
            mobile_number = request.data.get('mobile_number')
            pin = request.data.get('pin')
            
            if not mobile_number or not pin:
                return Response({
                    'error': 'Mobile number and PIN are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            business, token = BusinessService.authenticate_business(mobile_number, pin)
            business_serializer = BusinessSerializer(business)
            
            return Response({
                'message': 'Login successful',
                'token': token,
                'business': business_serializer.data
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BusinessProfileView(APIView):
    """View for business profile management"""
    authentication_classes = [BusinessAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get business profile"""
        serializer = BusinessSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        """Update business profile"""
        try:
            updated_business = BusinessService.update_business_profile(
                request.user, 
                **request.data
            )
            serializer = BusinessSerializer(updated_business)
            
            return Response({
                'message': 'Profile updated successfully',
                'business': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BusinessKycView(APIView):
    """View for business KYC management"""
    authentication_classes = [BusinessAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get business KYC status"""
        try:
            kyc = BusinessKyc.objects.get(business=request.user)
            serializer = BusinessKycSerializer(kyc)
            return Response(serializer.data)
        except BusinessKyc.DoesNotExist:
            return Response({
                'message': 'KYC not submitted yet',
                'kycStatus': False
            })
    
    def post(self, request):
        """Submit KYC documents"""
        try:
            kyc = BusinessService.submit_kyc_documents(
                request.user.business_id,
                request.data
            )
            serializer = BusinessKycSerializer(kyc)
            
            return Response({
                'message': 'KYC documents submitted successfully',
                'kyc': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BusinessKycApprovalView(APIView):
    """View for KYC approval (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, business_id):
        try:
            approved_by = request.user.email
            kyc = BusinessService.approve_kyc(business_id, approved_by)
            serializer = BusinessKycSerializer(kyc)
            
            return Response({
                'message': 'KYC approved successfully',
                'kyc': serializer.data
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BusinessListView(generics.ListAPIView):
    """View for listing businesses (Admin only)"""
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAdminUser]
    
    def get_queryset(self):
        queryset = Business.objects.all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status', None)
        if status_filter is not None:
            queryset = queryset.filter(business_is_active=status_filter.lower() == 'true')
        
        # Filter by type
        type_filter = self.request.query_params.get('type', None)
        if type_filter == 'institute':
            queryset = queryset.filter(is_institute=True)
        elif type_filter == 'business':
            queryset = queryset.filter(is_business=True, is_institute=False)
        
        # Search by name or mobile
        search = self.request.query_params.get('search', None)
        if search is not None:
            queryset = queryset.filter(
                models.Q(business_name__icontains=search) |
                models.Q(mobile_number__icontains=search) |
                models.Q(business_id__icontains=search)
            )
        
        return queryset.order_by('-business_created_at')


class BusinessDetailView(generics.RetrieveUpdateDestroyAPIView):
    """View for business detail management (Admin only)"""
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAdminUser]
    lookup_field = 'business_id'
    
    def delete(self, request, *args, **kwargs):
        """Deactivate business instead of deleting"""
        business = self.get_object()
        try:
            reason = request.data.get('reason', 'Deactivated by admin')
            BusinessService.deactivate_business(business, reason)
            return Response({
                'message': 'Business deactivated successfully'
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BusinessStatsView(APIView):
    """View for business statistics (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def get(self, request):
        try:
            stats = BusinessService.get_business_statistics()
            return Response(stats)
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class PhysicalCardGenerationView(APIView):
    """View for generating physical cards (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request, business_id):
        try:
            quantity = request.data.get('quantity', 1)
            
            if quantity > 100:  # Limit to prevent abuse
                return Response({
                    'error': 'Maximum 100 cards can be generated at once'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            cards = BusinessService.generate_physical_cards(business_id, quantity)
            
            return Response({
                'message': f'{quantity} physical cards generated successfully',
                'cards': [card.card_number for card in cards]
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class CardMappingView(APIView):
    """View for mapping cards (Admin only)"""
    permission_classes = [permissions.IsAdminUser]
    
    def post(self, request):
        try:
            primary_card = request.data.get('primary_card_number')
            secondary_card = request.data.get('secondary_card_number')
            card_type = request.data.get('card_type', 'physical')
            business_id = request.data.get('business_id')
            
            mapping = BusinessService.map_cards(
                primary_card, secondary_card, card_type, business_id
            )
            
            return Response({
                'message': 'Cards mapped successfully',
                'mapping_id': mapping.id
            })
            
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def business_logout(request):
    """Logout business by deleting auth token"""
    try:
        request.user.business_auth_token.delete()
        return Response({
            'message': 'Logout successful'
        })
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
