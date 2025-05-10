from django.urls import path
from .views import BillListCreateView, BillDetailView, AddParticipantsToBillView, ProcessBillImageView,UserBalanceView, UserWeeklySpendingView,PayBillView

urlpatterns = [
    path('', BillListCreateView.as_view(), name='bill-list'),
    path('process-image/', ProcessBillImageView.as_view(), name='process-bill-image'),
    path('add-participants/', AddParticipantsToBillView.as_view(), name='add-multiple-friends-to-bill'),
    path('balance/', UserBalanceView.as_view(), name='user-balance'),
    path('spending/', UserWeeklySpendingView.as_view(), name='user-weekly-spending'),
    path('pay/', PayBillView.as_view(), name='pay-bill'),
    path('<str:hashed_id>/', BillDetailView.as_view(), name='bill-detail'),    
]
