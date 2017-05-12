# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-05-07 19:02
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0017_remove_ship_upgrade_capactiy_max'),
    ]

    operations = [
        migrations.AddField(
            model_name='ship',
            name='shipyard',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='ships', to='ui.ShipYard'),
        ),
    ]