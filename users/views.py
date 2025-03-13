from rest_framework import status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, BasePermission
from .models import User, Friends, FriendRequest
from django.db.models import Q
from .serializers import UserSerializer, FriendSerializer
from utils.hash import decode_hashed_id
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

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

class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friends = Friends.objects.filter(Q(user=request.user) | Q(friend=request.user))
        friend_details = []
        for friend in friends:
            if friend.user == request.user:
                friend_details.append(friend.friend)
            elif friend.friend == request.user:
                friend_details.append(friend.user)
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
        return Response({"message": "Friend added successfully!"})

class RemoveFriendView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('friend_id', openapi.IN_PATH, description="ID of the friend to remove", type=openapi.TYPE_INTEGER)
        ],
        responses={200: "Friend removed successfully!"}
    )
    def delete(self, request, friend_id):
        Friends.objects.filter(user=request.user, friend__id=friend_id).delete()
        return Response({"message": "Friend removed successfully!"})

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
        FriendRequest.objects.filter(from_user=friend, to_user=request.user).delete()
        return Response({"message": "Friend request rejected successfully!"})

class GetFriendRequestsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        friend_requests = FriendRequest.objects.filter(to_user=request.user)
        users = [fr.from_user for fr in friend_requests]
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)