from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Friends, FriendRequest
from users.models import User
from users.serializers import UserSerializer
from utils.hash import decode_hashed_id
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_QUERY, description="Username to filter friends by", type=openapi.TYPE_STRING)
        ],
        responses={200: "List of friends"}
    )
    def get(self, request):
        friends = Friends.objects.filter(Q(user=request.user) | Q(friend=request.user))
        friend_details = []
        for friend in friends:
            if friend.user == request.user:
                friend_details.append(friend.friend)
            elif friend.friend == request.user:
                friend_details.append(friend.user)
        
        username_filter = request.query_params.get('username', '')
        if username_filter:
            friend_details = [friend for friend in friend_details if username_filter.lower() in friend.username.lower()]
        
        serializer = UserSerializer(friend_details, many=True)
        return Response(serializer.data)

class AddFriendView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'friend_id': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed friend ID')
            },
            required=['friend_id']
        ),
        responses={200: "Friend added successfully!"}
    )
    def post(self, request):
        encode_friend_id = request.data.get('friend_id')
        friend_id = decode_hashed_id(encode_friend_id, User)
        friend = User.objects.get(id=friend_id)
        Friends.objects.create(user=request.user, friend=friend)
        FriendRequest.objects.filter(from_user=friend, to_user=request.user).delete()  # Delete friend request
        return Response({"message": "Friend added successfully!"})

class RemoveFriendView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'friend_id': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed friend ID')
            },
            required=['friend_id']
        ),
        responses={200: "Friend removed successfully!"}
    )
    def post(self, request):
        encode_friend_id = request.data.get('friend_id')
        friend_id = decode_hashed_id(encode_friend_id, User)
        Friends.objects.filter(Q(user=request.user, friend_id=friend_id) | 
                              Q(friend=request.user, user_id=friend_id)).delete()
        return Response({"message": "Friend removed successfully!"})

class GetFriendSuggestionsView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_QUERY, description="Username to search for", type=openapi.TYPE_STRING)
        ],
        responses={200: "List of friend suggestions"}
    )
    def get(self, request):
        friends = Friends.objects.filter(Q(user=request.user) | Q(friend=request.user))
        friend_details = []
        for friend in friends:
            if friend.user == request.user:
                friend_details.append(friend.friend)
            elif friend.friend == request.user:
                friend_details.append(friend.user)
        suggestions = User.objects.exclude(
            Q(id__in=[friend.id for friend in friend_details]) | Q(username='admin') | Q(id=request.user.id)
        ).filter(username__icontains=request.query_params.get('username', ''))
        
        suggestion_data = []
        for suggestion in suggestions:
            has_sent_request = FriendRequest.objects.filter(from_user=request.user, to_user=suggestion).exists()
            suggestion_data.append({
                'user': UserSerializer(suggestion).data,
                'has_sent_request': has_sent_request
            })
        
        return Response(suggestion_data)

class SendFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'friend_id': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed friend ID')
            },
            required=['friend_id']
        ),
        responses={200: "Friend request sent successfully!"}
    )
    def post(self, request):
        encode_friend_id = request.data.get('friend_id')
        friend_id = decode_hashed_id(encode_friend_id, User)
        friend = User.objects.get(id=friend_id)
        if FriendRequest.objects.filter(from_user=request.user, to_user=friend).exists():
            return Response({"message": "Friend request already sent!"}, status=status.HTTP_400_BAD_REQUEST)
        FriendRequest.objects.create(from_user=request.user, to_user=friend)
        return Response({"message": "Friend request sent successfully!"})

class RejectFriendRequestView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'friend_id': openapi.Schema(type=openapi.TYPE_STRING, description='Hashed friend ID')
            },
            required=['friend_id']
        ),
        responses={200: "Friend request rejected successfully!"}
    )
    def post(self, request):
        encode_friend_id = request.data.get('friend_id')
        friend_id = decode_hashed_id(encode_friend_id, User)
        friend = User.objects.get(id=friend_id)
        FriendRequest.objects.filter(from_user=friend, to_user=request.user).delete()  # Delete friend request
        return Response({"message": "Friend request rejected successfully!"})

class GetFriendRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friend_requests = FriendRequest.objects.filter(to_user=request.user)
        users = [fr.from_user for fr in friend_requests]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)
