from rest_framework import serializers
from .models import Friends, FriendRequest
from users.serializers import UserSerializer
from django.db.models import Q

class UserWithMutualFriendsSerializer(UserSerializer):
    mutual_friends_count = serializers.SerializerMethodField()
    
    class Meta(UserSerializer.Meta):
        fields = list(UserSerializer.Meta.fields) + ['mutual_friends_count']
    
    def get_mutual_friends_count(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated or obj.id == request.user.id:
            return 0
        
        # Get current user's friends
        current_user_friends = Friends.objects.filter(user=request.user).values_list('friend_id', flat=True)
        
        # Get target user's friends
        target_user_friends = Friends.objects.filter(user=obj).values_list('friend_id', flat=True)
        
        # Calculate intersection
        mutual_friends = set(current_user_friends).intersection(set(target_user_friends))
        
        return len(mutual_friends)

class FriendSerializer(serializers.ModelSerializer):
    friend_details = UserWithMutualFriendsSerializer(source='friend', read_only=True)
    
    class Meta:
        model = Friends
        fields = '__all__'

class FriendRequestSerializer(serializers.ModelSerializer):
    sender_details = UserWithMutualFriendsSerializer(source='sender', read_only=True)
    receiver_details = UserWithMutualFriendsSerializer(source='receiver', read_only=True)
    
    class Meta:
        model = FriendRequest
        fields = '__all__'
