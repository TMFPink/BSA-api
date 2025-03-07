from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from .models import Bill, BillParticipant
from .serializers import BillParticipantSerializer, BillSerializer
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from users.models import Friends, User
from rest_framework import status
from utils.hash import decode_hashed_id, hash_id

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
        participant = BillParticipant.objects.create(bill=bill, user=self.request.user, is_paid=True, amount_owed=bill.total_amount)
        return participant
        

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

class PayBillView(generics.UpdateAPIView):
    serializer_class = BillParticipantSerializer
    permission_classes = [IsAuthenticated]

    def perform_update(self, serializer):
        serializer.save(is_paid=True)


class AddParticipantsToBillView(APIView):
    permission_classes = [IsAuthenticated]

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