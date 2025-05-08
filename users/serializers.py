from rest_framework import serializers
from .models import User
from rest_framework_simplejwt.tokens import RefreshToken
from utils.hash import hash_id


class UserSerializer(serializers.ModelSerializer):
    id = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name','last_name' ,'email', 'phone', 'password','avatarUrl']
        extra_kwargs = {
            'password': {'write_only': True},
            'first_name': {'required': False},
            'last_name': {'required': False},
            'phone': {'required': False},
            'avatarUrl': {'required': False},

        }
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user
    def get_id(self, obj):
        return hash_id(obj.id)
    def to_representation(self, instance):
        """Ensure avatarUrl always has a value"""
        ret = super().to_representation(instance)
        # If avatarUrl is None or empty, set default
        if not ret.get('avatarUrl'):
            ret['avatarUrl'] = "avatar1.jpeg"
        return ret

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class JWTSerializer(serializers.Serializer):
    refresh = serializers.CharField()
    access = serializers.CharField()

