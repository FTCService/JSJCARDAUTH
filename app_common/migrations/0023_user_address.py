# Generated by Django 5.2 on 2025-06-25 07:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_common', '0022_remove_member_mbrpincode_remove_member_mbraddress_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='address',
            field=models.JSONField(default=dict),
        ),
    ]
