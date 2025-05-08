from django.urls import path
from .views import BillListCreateView, BillDetailView, AddParticipantsToBillView, ProcessBillImageView

urlpatterns = [
    path('', BillListCreateView.as_view(), name='bill-list'),
    path('process-image/', ProcessBillImageView.as_view(), name='process-bill-image'),
    # path('pay/<int:pk>/', PayBillView.as_view(), name='pay-bill'),
    path('add-participants/', AddParticipantsToBillView.as_view(), name='add-multiple-friends-to-bill'),
    path('<str:hashed_id>/', BillDetailView.as_view(), name='bill-detail'),

]
