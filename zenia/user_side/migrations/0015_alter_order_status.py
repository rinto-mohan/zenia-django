# Generated by Django 4.2.6 on 2023-11-10 15:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0014_product_starred'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(choices=[('Delivered', 'Delivered'), ('Placed', 'Placed'), ('Shipped', 'Shipped'), ('Cancelled', 'Cancelled'), ('Returned', 'Returned'), ('Return Pending', 'Return Pending')], default='Placed', max_length=50),
        ),
    ]
