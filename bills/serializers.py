from rest_framework import serializers
from .models import Bill, BillParticipant
from utils.hash import hash_id
from users.serializers import UserSerializer

class BillParticipantSerializer(serializers.ModelSerializer):
    # id = serializers.SerializerMethodField()
    user = UserSerializer()

    class Meta:
        model = BillParticipant
        fields = ['user','amount_owed','is_paid']

    # def get_id(self, obj):
    #     return hash_id(obj.id)

class BillSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()
    participants = BillParticipantSerializer(many=True, read_only=True)

    class Meta:
        model = Bill
        fields = '__all__'

    def get_id(self, obj):
        return hash_id(obj.id)
