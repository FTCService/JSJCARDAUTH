# Generated by Django 5.2 on 2025-06-13 10:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_common', '0018_alter_member_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_jobmitra',
            field=models.BooleanField(default=False),
        ),
    ]
