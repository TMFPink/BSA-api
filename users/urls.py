from django.urls import path
from .views import GetMeView, GetAllUsersView, UserUpdateView,ChangePasswordView

urlpatterns = [
    path('all/', GetAllUsersView.as_view(), name='get-all-users'),
    path('me/', GetMeView.as_view(), name='get-me'), 
    path('profile/', UserUpdateView.as_view(), name='user-update'),
    path('password', ChangePasswordView.as_view(), name='user-update-password'),
]
