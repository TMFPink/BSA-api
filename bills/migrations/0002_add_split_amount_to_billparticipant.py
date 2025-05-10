from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('bills', '0001_initial'),  # Update this to the last migration in the `bills` app
    ]

    operations = [
        # migrations.AddField(
        #     model_name='billparticipant',
        #     name='split_amount',
        #     field=models.DecimalField(max_digits=10, decimal_places=2, default=0),
        #     preserve_default=False,
        # ),
    ]
