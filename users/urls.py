from django.urls import path
from .views import GetMeView, GetAllUsersView

urlpatterns = [
    path('all/', GetAllUsersView.as_view(), name='get-all-users'),
    path('me/', GetMeView.as_view(), name='get-me'), 
]
