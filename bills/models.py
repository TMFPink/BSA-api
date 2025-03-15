from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Bill(models.Model):
    title = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    all_paid = models.BooleanField(default=False)
    category = models.CharField(max_length=255, blank=True, null=True)
    bill_detail = models.ManyToManyField('BillDetail', related_name='bills')
    participants = models.ManyToManyField(User, through='BillParticipant', related_name='bills')

    def __str__(self):
        return self.title

class BillDetail(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='details')
    item_name = models.CharField(max_length=255)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item_name} for {self.bill.title}"
    
class BillParticipant(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='bill_participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount_owed = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} owes {self.amount_owed} for {self.bill.title}"
