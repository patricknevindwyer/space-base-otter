# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-06-10 19:57
from __future__ import unicode_literals

import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import ui.models


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0021_auto_20170521_1952'),
    ]

    operations = [
        migrations.AddField(
            model_name='planet',
            name='location_meta',
            field=django.contrib.postgres.fields.jsonb.JSONField(default=ui.models.default_location_meta),
        ),
        migrations.AddField(
            model_name='planet',
            name='location_type',
            field=models.CharField(choices=[('planet', 'Planet'), ('star', 'Star'), ('moon', 'Moon'), ('asteroid', 'Asterpid'), ('nebula', 'Nebula')], default='planet', max_length=255),
        ),
    ]