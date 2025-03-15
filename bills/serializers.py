from rest_framework import serializers
from .models import Bill, BillParticipant, BillDetail
from users.models import User
from utils.hash import hash_id
from users.serializers import UserSerializer

class BillParticipantSerializer(serializers.ModelSerializer):
    user = UserSerializer()

    class Meta:
        model = BillParticipant
        fields = ['user', 'amount_owed', 'is_paid']

class BillDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillDetail
        fields = ['item_name', 'item_price']

class BillSerializer(serializers.ModelSerializer):
    participants = serializers.ListField(
        child=serializers.CharField(), write_only=True, required=False
    )
    details = BillDetailSerializer(many=True, write_only=True, required=False)

    class Meta:
        model = Bill
        fields = ['id', 'title', 'total_amount','category', 'all_paid', 'participants', 'details']
        read_only_fields = ['id']

    def create(self, validated_data):
        participants_data = validated_data.pop('participants', [])
        details_data = validated_data.pop('details', [])
        bill = Bill.objects.create(**validated_data)

        for detail_data in details_data:
            BillDetail.objects.create(bill=bill, **detail_data)

        return bill

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['participants'] = [
            {
                "id": hash_id(participant.id),
                "user": {
                    "id": hash_id(participant.user.id),
                    "username": participant.user.username
                },
                "amount_owed": participant.amount_owed,
                "is_paid": participant.is_paid,
            }
            for participant in instance.bill_participants.all()  # Corrected reference
        ]
        representation['details'] = BillDetailSerializer(instance.details.all(), many=True).data
        return representation
