# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-12 13:44
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0004_ship'),
    ]

    operations = [
        migrations.AddField(
            model_name='ship',
            name='image_name',
            field=models.CharField(default='medfighter.png', max_length=255),
            preserve_default=False,
        ),
    ]
