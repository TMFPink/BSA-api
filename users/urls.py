from django.urls import path
from .views import GetMeView, FriendListView, AddFriendView, RemoveFriendView, GetAllUsersView, GetFriendSuggestionsView, SendFriendRequestView, RejectFriendRequestView, GetFriendRequestsView

urlpatterns = [
    path('all/', GetAllUsersView.as_view(), name='get-all-users'),
    path('me/', GetMeView.as_view(), name='get-me'), 
    path('friends/', FriendListView.as_view(), name='friend-list'),
    path('friends/add/', AddFriendView.as_view(), name='add-friend'),
    path('friends/remove/', RemoveFriendView.as_view(), name='remove-friend'),
    path('friends/suggestions/', GetFriendSuggestionsView.as_view(), name='friend-suggestions'),
    path('friends/send-friend-request/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('friends/reject-friend-request/', RejectFriendRequestView.as_view(), name='reject-friend-request'),
    path('friends/requests/', GetFriendRequestsView.as_view(), name='get-friend-requests'),
]
