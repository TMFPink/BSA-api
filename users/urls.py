from django.urls import path
from .views import GetMeView, FriendListView, AddFriendView, RemoveFriendView, GetAllUsersView

urlpatterns = [
    path('all/', GetAllUsersView.as_view(), name='get-all-users'),
    path('me/', GetMeView.as_view(), name='get-me'), 
    path('friends/', FriendListView.as_view(), name='friend-list'),
    path('friends/add/', AddFriendView.as_view(), name='add-friend'),
    path('friends/remove/', RemoveFriendView.as_view(), name='remove-friend'),
]
