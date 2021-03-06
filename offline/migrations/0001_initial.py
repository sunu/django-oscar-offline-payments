# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-15 07:04
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import offline.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='OfflineTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('payment_type', models.CharField(choices=[('CHEQUE', 'Cheque'), ('DD', 'Demand Draft'), ('MO', 'Money Order'), ('ET', 'Electronic Transfer')], max_length=32)),
                ('email', models.EmailField(blank=True, max_length=254, null=True)),
                ('txnid', models.CharField(db_index=True, default=offline.models.generate_id, max_length=32)),
                ('basket_id', models.CharField(blank=True, db_index=True, max_length=12, null=True)),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=12, null=True)),
                ('currency', models.CharField(blank=True, max_length=8, null=True)),
                ('status', models.CharField(choices=[('initiated', 'initiated'), ('received', 'received'), ('settled', 'settled'), ('failed', 'failed')], max_length=32)),
                ('user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('-date_created',),
            },
        ),
    ]
