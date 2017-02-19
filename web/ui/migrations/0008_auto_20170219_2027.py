# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-19 20:27
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0007_profile'),
    ]

    operations = [
        migrations.AddField(
            model_name='ship',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='ui.Profile'),
        ),
        migrations.AddField(
            model_name='ship',
            name='value',
            field=models.IntegerField(default=10000),
        ),
    ]