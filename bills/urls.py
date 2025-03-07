from django.urls import path
from .views import BillListCreateView, BillDetailView, PayBillView, AddParticipantsToBillView

urlpatterns = [
    path('', BillListCreateView.as_view(), name='bill-list'),
    path('<str:hashed_id>/', BillDetailView.as_view(), name='bill-detail'),
    path('pay/<int:pk>/', PayBillView.as_view(), name='pay-bill'),
    path('add-participants/', AddParticipantsToBillView.as_view(), name='add-multiple-friends-to-bill'),
]
