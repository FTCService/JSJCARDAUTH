from app_common.models import CardMapper, PhysicalCard
from rest_framework.response import Response
from rest_framework.views import APIView
from app_common.authentication import BusinessTokenAuthentication
from rest_framework.permissions import IsAuthenticated
import requests
from django.conf import settings

def is_primary_card_in_business(card_number, business_id):
    try:
        response = requests.get(
            settings.REWARD_SERVER_URL + "/cardno/member-details/",
            params={"card_number": card_number}
        )
        if response.status_code == 200:
            member = response.json()
            return member.get("BizMbrBizId") == int(business_id)
    except requests.RequestException:
        pass
    return False


class GetPrimaryCardAPI(APIView):
    def get(self, request):
        card_number = request.GET.get("card_number")
        business_id = request.GET.get("business_id")

        if not card_number:
            return Response({"success": False, "message": "Card number required"}, status=400)

        # Step 1: Check PhysicalCard
        physical_card = PhysicalCard.objects.filter(card_number=card_number, business__business_id=business_id).first()
        if physical_card:
            try:
                mapping = CardMapper.objects.get(
                    business__business_id=business_id,
                    secondary_card__card_number=card_number
                )
                return Response({
                    "success": True,
                    "primary_card_number": mapping.primary_card.mbrcardno,
                    "is_associated": True,
                    "message": "Mapped secondary card resolved to primary."
                }, status=200)
            except CardMapper.DoesNotExist:
                return Response({
                    "success": False,
                    "primary_card_number": card_number,
                    "is_associated": False,
                    "message": "Card exists but not mapped to any primary card."
                }, status=200)

        # Step 2: Check if it's a primary card directly via Server B
        if is_primary_card_in_business(card_number, business_id):
            return Response({
                "success": True,
                "primary_card_number": card_number,
                "is_associated": True,
                "message": "Primary card is directly associated with business."
            }, status=200)

        # Step 3: Not associated
        return Response({
            "success": False,
            "message": "This card is not associated with this business.",
            "primary_card_number": None,
            "is_associated": False
        }, status=200)




# class GetPrimaryCardAPI(APIView):
#     def get(self, request):
#         card_number = request.GET.get("card_number")
#         business_id = request.GET.get("business_id")

#         if not card_number:
#             return Response({"success": False, "message": "Card number required"}, status=400)

#         # ✅ Step 1: Check in PhysicalCard table
#         physical_card = PhysicalCard.objects.filter(card_number=card_number, business__business_id=business_id).first()
#         if not physical_card:
#             return Response({
#                 "success": False,
#                 "message": "This card is not associated with this business.",
#                 "primary_card_number": None,
#                 "is_associated": False
#             }, status=200)

#         # ✅ Step 2: Check CardMapper for mapping
#         try:
#             mapping = CardMapper.objects.get(
#                 business__business_id=business_id,
#                 secondary_card__card_number=card_number
#             )
#             return Response({
#                 "success": True,
#                 "primary_card_number": mapping.primary_card.mbrcardno,
#                 "is_associated": True,
#                 "message": "Mapped secondary card resolved to primary."
#             }, status=200)
#         except CardMapper.DoesNotExist:
#             # ✅ Card exists but is not mapped (may be primary)
#             return Response({
#                 "success": False,
#                 "primary_card_number": card_number,
#                 "is_associated": False,
#                 "message": "Card exists but not mapped to any primary card."
#             }, status=200)




# class GetPrimaryCardAPI(APIView):
#     def get(self, request):
#         card_number = request.GET.get("card_number")
#         business_id = request.GET.get("business_id")

#         if not card_number:
#             return Response({"success": False, "message": "Card number required"}, status=400)
        
#         physical_card = PhysicalCard.objects.filter(card_number=card_number, business__business_id=business_id).first()
#         if not physical_card:
            
#             return Response({"success":False,"message":"this card not associate with business"})
#         try:
#             query = CardMapper.objects.select_related('primary_card', 'secondary_card')
#             if business_id:
#                 query = query.filter(business__business_id=business_id)

#             mapping = query.get(secondary_card__card_number=card_number)
#             return Response({
#                 "success": True,
#                 "primary_card_number": mapping.primary_card.mbrcardno
#             }, status=200)
#         except CardMapper.DoesNotExist:
            
#             return Response({
#                 "success": False,
#                 "primary_card_number": card_number,  # fallback to cleaned original
#                 "message": "No mapping found"
#             }, status=400)


