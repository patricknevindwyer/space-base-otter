# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-22 20:45
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0012_auto_20170422_2016'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ship',
            old_name='cargo_capactiy_max',
            new_name='upgrade_capactiy_max',
        ),
        migrations.AddField(
            model_name='ship',
            name='upgrade_capacity',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='shipupgrade',
            name='name',
            field=models.CharField(default='', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shipupgrade',
            name='quality',
            field=models.CharField(default='foo', max_length=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='shipupgrade',
            name='space',
            field=models.IntegerField(default=10),
        ),
    ]
