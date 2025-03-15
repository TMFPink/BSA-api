from django.urls import path
from .views import (
    FriendListView, 
    AddFriendView, 
    RemoveFriendView, 
    GetFriendSuggestionsView, 
    SendFriendRequestView, 
    RejectFriendRequestView, 
    GetFriendRequestsView
)

urlpatterns = [
    path('', FriendListView.as_view(), name='friend-list'),
    path('add/', AddFriendView.as_view(), name='add-friend'),
    path('remove/', RemoveFriendView.as_view(), name='remove-friend'),
    path('suggestions/', GetFriendSuggestionsView.as_view(), name='friend-suggestions'),
    path('send-request/', SendFriendRequestView.as_view(), name='send-friend-request'),
    path('reject-request/', RejectFriendRequestView.as_view(), name='reject-friend-request'),
    path('requests/', GetFriendRequestsView.as_view(), name='get-friend-requests'),
]
