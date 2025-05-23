# Generated by Django 5.2 on 2025-05-16 13:28

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_common', '0012_businesskyc'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAuthToken',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key', models.CharField(max_length=255, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin_auth_token', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
