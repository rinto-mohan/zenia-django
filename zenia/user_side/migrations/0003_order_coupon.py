# Generated by Django 4.2.6 on 2023-10-23 12:58

from django.db import migrations, models
import django.db.models.deletion
import user_side.models


class Migration(migrations.Migration):

    dependencies = [
        ('user_side', '0002_coupon'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='coupon',
            field=models.ForeignKey(default=user_side.models.get_default_coupon, on_delete=django.db.models.deletion.CASCADE, to='user_side.coupon'),
        ),
    ]