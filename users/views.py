from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, BasePermission
from .models import User, Friends
from .serializers import UserSerializer, FriendSerializer
from utils.hash import decode_hashed_id

class GetMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user  
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
class IsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return request.user and (request.user.username == 'admin')

class GetAllUsersView(APIView):
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        users = User.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
    

class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friends = Friends.objects.filter(user=request.user)
        friend_details = [friend.friend for friend in friends]
        serializer = UserSerializer(friend_details, many=True)
        return Response(serializer.data)

class AddFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        encode_friend_id = request.data.get('friend_id')
        friend_id = decode_hashed_id(encode_friend_id, User)
        friend = User.objects.get(id=friend_id)
        Friends.objects.create(user=request.user, friend=friend)
        return Response({"message": "Friend added successfully!"})

class RemoveFriendView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, friend_id):
        Friends.objects.filter(user=request.user, friend__id=friend_id).delete()
        return Response({"message": "Friend removed successfully!"})