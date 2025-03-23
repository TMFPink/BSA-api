from django.db import models
from users.models import User
from django.core.exceptions import ValidationError

class Bill(models.Model):
        

    billName = models.CharField(max_length=255)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    all_paid = models.BooleanField(default=False)
    category = models.CharField(max_length=255, blank=True, null=True)
    shared = models.BooleanField(default=False, blank=True, null=True)
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bills_as_payer', blank=True, null=True)
    bill_detail = models.ManyToManyField('BillDetail', related_name='bills')
    participants = models.ManyToManyField(User, through='BillParticipant', related_name='bills_as_participant')

    def clean(self):
        if self.payer and not User.objects.filter(pk=self.payer.pk).exists():
            raise ValidationError({'payer': 'Invalid payer - object does not exist.'})

    def __str__(self):
        return self.billName

class BillDetail(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='details')
    item_name = models.CharField(max_length=255)
    item_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.item_name} for {self.bill.billName}"
    
class BillParticipant(models.Model):
    bill = models.ForeignKey(Bill, on_delete=models.CASCADE, related_name='bill_participants')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    split_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} will pay {self.split_amount} for {self.bill.billName}"
