# -*- coding: utf-8 -*-
# Generated by Django 1.10.7 on 2017-06-15 11:09
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('offline', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='offlinetransaction',
            name='notes',
            field=models.TextField(blank=True, null=True),
        ),
    ]