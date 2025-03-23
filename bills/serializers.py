from rest_framework import serializers
from .models import Bill, BillParticipant, BillDetail
from users.models import User
from utils.hash import hash_id, decode_hashed_id
from users.serializers import UserSerializer
from hashlib import sha256
from django.shortcuts import get_object_or_404

class BillParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer()
    split_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)

    class Meta:
        model = BillParticipant
        fields = ['id', 'user', 'bill', 'split_amount', 'is_paid']

class BillDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillDetail
        fields = ['item_name', 'item_price']

class ParticipantSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    split_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid = serializers.BooleanField()

class PayerSerializer(serializers.Serializer):
    id = serializers.CharField()
    name = serializers.CharField()
    split_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    paid = serializers.BooleanField()

class BillSerializer(serializers.ModelSerializer):
    billDetails = BillDetailSerializer(many=True, write_only=True, required=True)
    billName = serializers.CharField( required=True)
    category = serializers.CharField(required=True)
    date = serializers.DateTimeField(source='created_at', required=True)
    participants = ParticipantSerializer(many=True, write_only=True, required=True)
    payer = PayerSerializer(write_only=True, required=True)
    shared = serializers.BooleanField(required=True)
    total_amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=True)

    class Meta:
        model = Bill
        fields = ['id', 'billDetails', 'billName', 'category', 'date', 'participants', 'payer', 'shared', 'total_amount']
        read_only_fields = ['id']

    def create(self, validated_data):
        # Extract nested data
        details_data = validated_data.pop('billDetails', [])
        participants_data = validated_data.pop('participants', [])
        payer_data = validated_data.pop('payer', None)

        # Create the bill
        bill = Bill.objects.create(**validated_data)

        # Add bill details
        for detail_data in details_data:
            BillDetail.objects.create(bill=bill, **detail_data)

        # Add participants
        for participant_data in participants_data:
            user_id = decode_hashed_id(participant_data['id'], User)
            user = get_object_or_404(User, id=user_id)
            BillParticipant.objects.create(
                bill=bill,
                user=user,
                split_amount=participant_data['split_amount'],
                is_paid=participant_data['paid']
            )

        # Add payer
        payer_id = decode_hashed_id(payer_data['id'], User)
        payer = get_object_or_404(User, id=payer_id)
        bill.payer = payer
        bill.save()

        return bill

    def to_representation(self, instance):
        representation = {
            "billName": instance.billName,
            "category": instance.category,
            "date": instance.created_at.isoformat(),
            "shared": instance.shared,
            "billDetails": [
                {
                    "description": detail.item_name,
                    "amount": detail.item_price
                }
                for detail in instance.details.all()
            ],
            "participants": [
                {
                    "id": hash_id(participant.user.id),
                    "name": participant.user.username,
                    "split_amount": participant.split_amount,
                    "paid": participant.is_paid
                }
                for participant in instance.bill_participants.all()
            ],
            "payer": {
                "id": hash_id(instance.payer.id),
                "name": instance.payer.username,
                "split_amount": instance.total_amount,
                "paid": instance.all_paid
            }
        }
        return representation
