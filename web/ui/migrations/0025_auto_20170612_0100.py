# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-12 01:00
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0024_auto_20170612_0100'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ship',
            name='home_planet',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='registrants', to='ui.Location'),
        ),
        migrations.AlterField(
            model_name='ship',
            name='location',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='orbiters', to='ui.Location'),
        ),
    ]
