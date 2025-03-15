from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from utils.hash import hash_id


class UserSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name','last_name' ,'email', 'phone', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone': {'required': False},
        }
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    def get_id(self, obj):
        return hash_id(obj.id)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class JWTSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

