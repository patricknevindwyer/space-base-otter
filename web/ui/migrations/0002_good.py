# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-12 01:43
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ui', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Good',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('is_import', models.BooleanField()),
                ('is_export', models.BooleanField()),
                ('price', models.FloatField()),
                ('planet', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='goods', to='ui.Planet')),
            ],
        ),
    ]
