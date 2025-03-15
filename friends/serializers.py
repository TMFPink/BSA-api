from rest_framework import serializers
from .models import Friends, FriendRequest
from users.serializers import UserSerializer

class FriendSerializer(serializers.ModelSerializer):
    class Meta:
        model = Friends
        fields = '__all__'

class FriendRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = FriendRequest
        fields = '__all__'
