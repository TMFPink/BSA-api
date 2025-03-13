from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError
from .models import Bill, BillParticipant, BillDetail
from .serializers import BillParticipantSerializer, BillSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from users.models import Friends, User
from rest_framework import status
from utils.hash import decode_hashed_id, hash_id
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class BillListCreateView(generics.ListCreateAPIView):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        
        queryset =  Bill.objects.filter(id__in=BillParticipant.objects.filter(user=self.request.user).values_list('bill_id', flat=True))    

        title = self.request.query_params.get("title", None)
        all_paid = self.request.query_params.get("all_paid",None)
        
        if title:
            queryset = queryset.filter(title__icontains=title)
        if all_paid:
            queryset = queryset.filter(all_paid=all_paid)
        

        return queryset
        

    def perform_create(self, serializer):
        bill = serializer.save()
        participants_data = self.request.data.get("participants", [])
        details_data = self.request.data.get("details", [])

        if not isinstance(participants_data, list) or not participants_data:
            raise ValidationError({"participants": "Participants must be a list of hashed user IDs."})

        valid_friends = [decode_hashed_id(fid, User) for fid in participants_data]
        valid_friends = [friend for friend in valid_friends if friend]

        if not valid_friends:
            raise ValidationError({"participants": "Invalid participant IDs."})

        total_participants = len(valid_friends) + 1  # Including the creator
        split_amount = bill.total_amount / total_participants

        BillParticipant.objects.create(bill=bill, user=self.request.user, is_paid=True, amount_owed=split_amount)

        for friend_id in valid_friends:
            friend = get_object_or_404(User, id=friend_id)
            if not Friends.objects.filter(user=self.request.user, friend=friend).exists():
                raise ValidationError({"participants": f"{friend.username} is not your friend!"})
            BillParticipant.objects.create(bill=bill, user=friend, amount_owed=split_amount)

        for detail in details_data:
            if not BillDetail.objects.filter(bill=bill, **detail).exists():
                BillDetail.objects.create(bill=bill, **detail)

        return bill

    @swagger_auto_schema(
        request_body=BillSerializer,
        responses={201: BillSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

class BillDetailView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = BillSerializer

    def get_object(self):
        # Get the hashed bill ID from the URL
        hashed_id = self.kwargs.get("hashed_id")

        # Decode it to get the original bill ID
        bill_id = decode_hashed_id(hashed_id, Bill)

        if not bill_id:
            return get_object_or_404(Bill, id=-1)  # Return 404 if invalid ID

        # Ensure the user has access to the bill
        return get_object_or_404(
            Bill, 
            id=bill_id, 
            id__in=BillParticipant.objects.filter(user=self.request.user).values_list("bill_id", flat=True)
        )

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('hashed_id', openapi.IN_PATH, description="Hashed bill ID", type=openapi.TYPE_STRING)
        ],
        responses={200: BillSerializer}
    )
    def get(self, request, *args, **kwargs):
        bill = self.get_object()
        serializer = self.get_serializer(bill)
        return Response(serializer.data)

class BillUpdateView(generics.UpdateAPIView):
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Get the hashed bill ID from the URL
        hashed_id = self.kwargs.get("hashed_id")

        # Decode it to get the original bill ID
        bill_id = decode_hashed_id(hashed_id, Bill)

        if not bill_id:
            return get_object_or_404(Bill, id=-1)  # Return 404 if invalid ID

        # Ensure the user has access to the bill
        return get_object_or_404(
            Bill, 
            id=bill_id, 
            id__in=BillParticipant.objects.filter(user=self.request.user).values_list("bill_id", flat=True)
        )

    def perform_update(self, serializer):
        bill = serializer.save()
        participants_data = self.request.data.get("participants", [])

        if participants_data:
            if not isinstance(participants_data, list):
                raise ValidationError({"participants": "Participants must be a list of hashed user IDs."})

            valid_friends = [decode_hashed_id(fid, User) for fid in participants_data]
            valid_friends = [friend for friend in valid_friends if friend]

            if not valid_friends:
                raise ValidationError({"participants": "Invalid participant IDs."})

            total_participants = len(valid_friends) + 1  # Including the creator
            split_amount = bill.total_amount / total_participants

            BillParticipant.objects.filter(bill=bill).delete()
            BillParticipant.objects.create(bill=bill, user=self.request.user, is_paid=True, amount_owed=split_amount)

            for friend_id in valid_friends:
                friend = get_object_or_404(User, id=friend_id)
                if not Friends.objects.filter(user=self.request.user, friend=friend).exists():
                    raise ValidationError({"participants": f"{friend.username} is not your friend!"})
                BillParticipant.objects.create(bill=bill, user=friend, amount_owed=split_amount)

        return bill

class PayBillView(generics.UpdateAPIView):
    serializer_class = BillParticipantSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(is_paid=True)

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('pk', openapi.IN_PATH, description="Primary key of the bill participant", type=openapi.TYPE_INTEGER)
        ],
        request_body=BillParticipantSerializer,
        responses={200: BillParticipantSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

class AddParticipantsToBillView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'bill_id': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed bill ID'),
                'participants': openapi.Schema(type=openapi.TYPE_ARRAY, items=openapi.Items(type=openapi.TYPE_STRING), description='List of hashed participant IDs')
            },
            required=['bill_id', 'participants']
        ),
        responses={201: "Participants added successfully!"}
    )
    def post(self, request):

        encoded_bill_id = request.data.get("bill_id")
        bill_id = decode_hashed_id(encoded_bill_id, Bill)
        if not bill_id:
            return Response({"error": "Invalid bill ID."}, status=status.HTTP_400_BAD_REQUEST)
        bill = get_object_or_404(Bill, id=bill_id)


        hashed_friend_ids = request.data.get("participants", [])
        if not isinstance(hashed_friend_ids, list) or not hashed_friend_ids:
            return Response({"error": "Participants must be a list of hashed user IDs."}, status=status.HTTP_400_BAD_REQUEST)

        # Decode the hashed user IDs
        valid_friends = [decode_hashed_id(fid, User) for fid in hashed_friend_ids]
        valid_friends = [friend for friend in valid_friends if friend]  # Remove None values

        if not valid_friends:
            return Response({"error": "Invalid participant IDs."}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure all provided users are friends of the requester
        for friend in valid_friends:
            friend = get_object_or_404(User, id=friend)
            if not Friends.objects.filter(user=request.user, friend=friend).exists():
                return Response(
                    {"error": f"{friend.username} is not your friend!"},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Calculate how much each participant should owe (including new participants)
        total_participants = bill.participants.count() + len(valid_friends)
        split_amount = bill.total_amount / total_participants

        # Update existing participants' owed amount
        for participant in bill.participants.all():
            participant.amount_owed = split_amount
            participant.save()

        # Add new participants
        new_participants = []
        for friend in valid_friends:
            friend = get_object_or_404(User, id=friend)
            participant, created = BillParticipant.objects.get_or_create(
                bill=bill, user=friend, defaults={"amount_owed": split_amount}
            )
            if not created:
                participant.amount_owed = split_amount
                participant.save()
            new_participants.append(participant)

        # Hash the participant IDs before returning the response
        hashed_participants = [
            {
                "id": hash_id(participant.id),
                "user": {
                    "id": hash_id(participant.user.id),
                    "username": participant.user.username
                },
                "amount_owed": participant.amount_owed,
                "is_paid": participant.is_paid,
            }
            for participant in new_participants
        ]

        return Response(hashed_participants, status=status.HTTP_201_CREATED)