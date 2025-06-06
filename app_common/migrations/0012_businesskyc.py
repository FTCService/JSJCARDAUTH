# Generated by Django 5.2 on 2025-05-09 12:30

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app_common', '0011_businessauthtoken'),
    ]

    operations = [
        migrations.CreateModel(
            name='BusinessKyc',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('kycStatus', models.BooleanField(blank=True, default=False, null=True, verbose_name='KYC Status')),
                ('kycAdharCard', models.CharField(blank=True, max_length=255, null=True, verbose_name='Aadhar Card URL')),
                ('kycGst', models.CharField(blank=True, max_length=15, null=True, verbose_name='GST Number')),
                ('kycPanCard', models.CharField(blank=True, max_length=255, null=True, verbose_name='PAN Card URL')),
                ('kycOthers', models.CharField(blank=True, max_length=255, null=True, verbose_name='Other Documents URL')),
                ('business', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='kyc', to='app_common.business', verbose_name='Business')),
            ],
        ),
    ]
