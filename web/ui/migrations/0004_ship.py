# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-12 13:28
from __future__ import unicode_literals

from django.db import migrations, models
import ui.models


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0003_planet_image_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ship',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('model', models.CharField(max_length=255)),
                ('max_range', models.IntegerField(default=1000)),
                ('fuel_level', models.FloatField(default=100.0)),
                ('cargo_capacity', models.IntegerField(default=50)),
                ('planet', models.ForeignKey(on_delete=models.SET(ui.models.get_default_ship_location), to='ui.Planet')),
            ],
        ),
    ]
