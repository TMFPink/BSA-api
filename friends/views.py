from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from .models import Friends, FriendRequest
from users.models import User
from users.serializers import UserSerializer
from friends.serializers import UserWithMutualFriendsSerializer, FriendSerializer, FriendRequestSerializer
from utils.hash import decode_hashed_id
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class FriendListView(APIView):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('username', openapi.IN_QUERY, description="Username to filter friends by", type=openapi.TYPE_STRING)
        ],
        responses={200: UserWithMutualFriendsSerializer(many=True)}
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
        
        # Get current user's friends
        user_friends = Friends.objects.filter(Q(user=request.user) | Q(friend=request.user))
        user_friend_ids = set()
        for friend in user_friends:
            if friend.user == request.user:
                user_friend_ids.add(friend.friend.id)
            elif friend.friend == request.user:
                user_friend_ids.add(friend.user.id)
        
        # Calculate mutual friends for each friend
        result = []
        for friend_user in friend_details:
            # Get friends of this friend
            friend_friends = Friends.objects.filter(Q(user=friend_user) | Q(friend=friend_user))
            friend_friend_ids = set()
            for ff in friend_friends:
                if ff.user == friend_user:
                    friend_friend_ids.add(ff.friend.id)
                elif ff.friend == friend_user:
                    friend_friend_ids.add(ff.user.id)
            
            # Calculate mutual friends
            mutual_friends_count = len(user_friend_ids.intersection(friend_friend_ids))
            
            # Serialize user data
            user_data = UserWithMutualFriendsSerializer(friend_user, context={'request': request}).data
            user_data['mutual_friends_count'] = mutual_friends_count
            result.append(user_data)
        
        return Response(result)

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
        responses={200: openapi.Schema(
            type=openapi.TYPE_ARRAY,
            items=openapi.Schema(
                type=openapi.TYPE_OBJECT,
                properties={
                    'user': openapi.Schema(
                        type=openapi.TYPE_OBJECT,
                        properties={
                            'id': openapi.Schema(type=openapi.TYPE_INTEGER),
                            'username': openapi.Schema(type=openapi.TYPE_STRING),
                            'email': openapi.Schema(type=openapi.TYPE_STRING),
                            'first_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'last_name': openapi.Schema(type=openapi.TYPE_STRING),
                            'phone': openapi.Schema(type=openapi.TYPE_STRING),
                            'avatarUrl': openapi.Schema(type=openapi.TYPE_STRING),
                            'mutual_friends_count': openapi.Schema(type=openapi.TYPE_INTEGER, description='Number of mutual friends')
                        }
                    ),
                    'has_sent_request': openapi.Schema(type=openapi.TYPE_BOOLEAN)
                }
            )
        )}
    )
    def get(self, request):
        # Get current user's friends
        user_friends = Friends.objects.filter(Q(user=request.user) | Q(friend=request.user))
        friend_ids = set()

        for friend in user_friends:
            if friend.user == request.user:
                friend_ids.add(friend.friend.id)
            elif friend.friend == request.user:
                friend_ids.add(friend.user.id)

        # Get user suggestions (non-friends)
        suggestions = User.objects.exclude(
            Q(id__in=friend_ids) | Q(username='admin') | Q(id=request.user.id)
        ).filter(username__icontains=request.query_params.get('username', ''))

        suggestion_data = []
        for suggestion in suggestions:
            # Get friends of the suggested user
            suggestion_friends = Friends.objects.filter(Q(user=suggestion) | Q(friend=suggestion))
            suggestion_friend_ids = set()

            for sf in suggestion_friends:
                if sf.user == suggestion:
                    suggestion_friend_ids.add(sf.friend.id)
                elif sf.friend == suggestion:
                    suggestion_friend_ids.add(sf.user.id)

            # Calculate mutual friends correctly
            mutual_friends_count = len(friend_ids.intersection(suggestion_friend_ids))

            # Check if a friend request has been sent
            has_sent_request = FriendRequest.objects.filter(from_user=request.user, to_user=suggestion).exists()

            # Serialize user data
            user_data = UserWithMutualFriendsSerializer(suggestion, context={'request': request}).data
            user_data['mutual_friends_count'] = mutual_friends_count

            suggestion_data.append({
                'user': user_data,
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

    @swagger_auto_schema(
        responses={200: UserWithMutualFriendsSerializer(many=True)}
    )
    def get(self, request):
        friend_requests = FriendRequest.objects.filter(to_user=request.user)
        users = [fr.from_user for fr in friend_requests]
        serializer = UserWithMutualFriendsSerializer(users, many=True, context={'request': request})
        return Response(serializer.data)
